# loader.py
import ast
import os
import re
import tiktoken
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# ── Data Model ──────────────────────────────────────────────────────────────────

@dataclass
class CodeChunk:
    chunk_id: str
    file_path: str
    language: str
    content: str
    start_line: int
    end_line: int
    ast_node_type: str
    ast_node_name: str
    token_count: int
    is_approximate: bool

# ── Language Detection ──────────────────────────────────────────────────────────

EXTENSION_MAP = {
    ".py":   "python",
    ".java": "java",
    ".js":   "javascript",
    ".jsx":  "javascript",
    ".ts":   "javascript",
    ".tsx":  "javascript",
}

def detect_language(file_path: str) -> Optional[str]:
    ext = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(ext, None)

# ── Token Counter ───────────────────────────────────────────────────────────────

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


# ── Chunk Merger ────────────────────────────────────────────────────────────────

def merge_small_chunks(
    chunks: List[CodeChunk],
    max_tokens: int = 1200,
    min_tokens: int = 300,
) -> List[CodeChunk]:
    """
    Merges consecutive small chunks that are below min_tokens into
    a single chunk, as long as the combined size stays under max_tokens.
    Chunks already above min_tokens are kept as-is.
    This reduces LLM calls while preserving all code and line metadata.
    """
    if not chunks:
        return chunks

    merged = []
    buffer: List[CodeChunk] = []
    buffer_tokens = 0

    for chunk in chunks:
        if buffer_tokens + chunk.token_count <= max_tokens:
            buffer.append(chunk)
            buffer_tokens += chunk.token_count
        else:
            # Flush buffer
            if buffer:
                merged.append(_combine_buffer(buffer))
            buffer = [chunk]
            buffer_tokens = chunk.token_count

    if buffer:
        merged.append(_combine_buffer(buffer))

    return merged


def _combine_buffer(buffer: List[CodeChunk]) -> CodeChunk:
    if len(buffer) == 1:
        return buffer[0]

    combined_content = "\n\n".join(c.content for c in buffer)
    names = [c.ast_node_name for c in buffer if c.ast_node_name != "<module>"]
    combined_name = "+".join(names[:3]) + ("..." if len(names) > 3 else "")

    return CodeChunk(
        chunk_id=buffer[0].chunk_id,           # keep first chunk's ID as anchor
        file_path=buffer[0].file_path,
        language=buffer[0].language,
        content=combined_content,
        start_line=buffer[0].start_line,
        end_line=buffer[-1].end_line,           # span full range
        ast_node_type="merged_block",
        ast_node_name=combined_name,
        token_count=count_tokens(combined_content),
        is_approximate=False,
    )


# ── Python AST Chunker ──────────────────────────────────────────────────────────

def chunk_python_by_ast(source: str, file_path: str) -> List[CodeChunk]:
    chunks = []
    lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    nodes_to_extract = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes_to_extract.append(node)

    nodes_to_extract.sort(key=lambda n: n.lineno)

    covered_lines = set()
    for node in nodes_to_extract:
        end = getattr(node, "end_lineno", node.lineno)
        for l in range(node.lineno, end + 1):
            covered_lines.add(l)

    for node in nodes_to_extract:
        end_line = getattr(node, "end_lineno", node.lineno)
        ctx_start = max(1, node.lineno - 3)
        snippet_lines = lines[ctx_start - 1: end_line]
        content = "\n".join(snippet_lines)

        node_type = "function"
        if isinstance(node, ast.ClassDef):
            node_type = "class"
        elif isinstance(node, ast.AsyncFunctionDef):
            node_type = "async_function"

        chunk_id = f"{Path(file_path).stem}_{node_type}_{node.name}_{node.lineno}"

        chunks.append(CodeChunk(
            chunk_id=chunk_id,
            file_path=file_path,
            language="python",
            content=content,
            start_line=node.lineno,
            end_line=end_line,
            ast_node_type=node_type,
            ast_node_name=node.name,
            token_count=count_tokens(content),
            is_approximate=False,
        ))

    module_lines = [
        (i + 1, line) for i, line in enumerate(lines)
        if (i + 1) not in covered_lines and line.strip()
    ]
    if module_lines:
        module_content = "\n".join(line for _, line in module_lines)
        first_line = module_lines[0][0]
        last_line = module_lines[-1][0]
        chunks.append(CodeChunk(
            chunk_id=f"{Path(file_path).stem}_module_level_{first_line}",
            file_path=file_path,
            language="python",
            content=module_content,
            start_line=first_line,
            end_line=last_line,
            ast_node_type="module",
            ast_node_name="<module>",
            token_count=count_tokens(module_content),
            is_approximate=False,
        ))

    chunks = sorted(chunks, key=lambda c: c.start_line)
    return merge_small_chunks(chunks, max_tokens=1200, min_tokens=300)


# ── Regex-Based Chunker for Java / JavaScript ───────────────────────────────────

def chunk_by_regex(source: str, file_path: str, language: str) -> List[CodeChunk]:
    chunks = []
    lines = source.splitlines()

    if language == "java":
        pattern = re.compile(
            r'^[ \t]*(public|private|protected|static|final|synchronized|abstract|native)?'
            r'[\s\w<>\[\],?]*\s+(\w+)\s*\([^)]*\)\s*(throws\s+[\w,\s]+)?\s*\{',
            re.MULTILINE
        )
    else:  # javascript
        pattern = re.compile(
            r'^[ \t]*(async\s+)?function\s+(\w+)\s*\(|'
            r'^[ \t]*(?:const|let|var)\s+(\w+)\s*=\s*(async\s*)?\(?.*?\)?\s*=>|'
            r'^[ \t]*(\w+)\s*\([^)]*\)\s*\{',
            re.MULTILINE
        )

    matches = list(pattern.finditer(source))
    if not matches:
        return []

    for i, match in enumerate(matches):
        start_char = match.start()
        end_char = matches[i + 1].start() if i + 1 < len(matches) else len(source)

        block = source[start_char:end_char]
        start_line = source[:start_char].count("\n") + 1
        end_line = start_line + block.count("\n")

        groups = [g for g in match.groups() if g and g.strip() not in
                  ("public","private","protected","static","final","async","const","let","var")]
        node_name = groups[0].strip() if groups else f"block_{start_line}"

        chunk_id = f"{Path(file_path).stem}_{language}_{node_name}_{start_line}"

        chunks.append(CodeChunk(
            chunk_id=chunk_id,
            file_path=file_path,
            language=language,
            content=block.strip(),
            start_line=start_line,
            end_line=end_line,
            ast_node_type="function",
            ast_node_name=node_name,
            token_count=count_tokens(block),
            is_approximate=False,
        ))

    chunks = sorted(chunks, key=lambda c: c.start_line)
    # ── Merge small functions into larger context windows ──────────────────────
    return merge_small_chunks(chunks, max_tokens=1200, min_tokens=300)


# ── Token-Based Fallback Chunker ────────────────────────────────────────────────

def chunk_by_tokens(
    source: str,
    file_path: str,
    language: str,
    target_tokens: int = 1200,
    overlap_tokens: int = 150,
) -> List[CodeChunk]:
    lines = source.splitlines()
    chunks = []
    current_lines = []
    current_tokens = 0
    chunk_index = 0
    start_line = 1

    for i, line in enumerate(lines, start=1):
        line_tokens = count_tokens(line)
        current_lines.append((i, line))
        current_tokens += line_tokens

        if current_tokens >= target_tokens:
            content = "\n".join(l for _, l in current_lines)
            end_line = current_lines[-1][0]

            chunks.append(CodeChunk(
                chunk_id=f"{Path(file_path).stem}_token_chunk_{chunk_index}",
                file_path=file_path,
                language=language,
                content=content,
                start_line=start_line,
                end_line=end_line,
                ast_node_type="block",
                ast_node_name=f"chunk_{chunk_index}",
                token_count=current_tokens,
                is_approximate=True,
            ))
            chunk_index += 1

            overlap_lines = []
            overlap_count = 0
            for line_num, line_text in reversed(current_lines):
                overlap_count += count_tokens(line_text)
                overlap_lines.insert(0, (line_num, line_text))
                if overlap_count >= overlap_tokens:
                    break

            current_lines = overlap_lines
            current_tokens = overlap_count
            start_line = current_lines[0][0] if current_lines else i + 1

    if current_lines:
        content = "\n".join(l for _, l in current_lines)
        chunks.append(CodeChunk(
            chunk_id=f"{Path(file_path).stem}_token_chunk_{chunk_index}",
            file_path=file_path,
            language=language,
            content=content,
            start_line=current_lines[0][0],
            end_line=current_lines[-1][0],
            ast_node_type="block",
            ast_node_name=f"chunk_{chunk_index}",
            token_count=count_tokens(content),
            is_approximate=True,
        ))

    return chunks


# ── Main CodeDocumentLoader ─────────────────────────────────────────────────────

class CodeDocumentLoader:
    def __init__(self, source_path: str, language_override: Optional[str] = None):
        self.source_path = Path(source_path)
        self.language_override = language_override

    def load(self) -> List[CodeChunk]:
        all_chunks: List[CodeChunk] = []

        if self.source_path.is_file():
            files = [self.source_path]
        elif self.source_path.is_dir():
            files = [
                p for p in self.source_path.rglob("*")
                if p.is_file() and detect_language(str(p)) is not None
            ]
        else:
            raise FileNotFoundError(f"Path not found: {self.source_path}")

        for file_path in files:
            chunks = self._load_file(str(file_path))
            all_chunks.extend(chunks)

        print(f"[Loader] Loaded {len(all_chunks)} chunks from {len(files)} file(s).")
        return all_chunks

    def _load_file(self, file_path: str) -> List[CodeChunk]:
        language = self.language_override or detect_language(file_path)
        if not language:
            return []

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        if not source.strip():
            return []

        if language == "python":
            chunks = chunk_python_by_ast(source, file_path)
        else:
            chunks = chunk_by_regex(source, file_path, language)

        if not chunks:
            print(f"[Loader] AST chunking failed for {file_path}, using token fallback.")
            chunks = chunk_by_tokens(source, file_path, language)

        return chunks


# ── Quick test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/sample_inputs/buggy_python.py"
    loader = CodeDocumentLoader(path)
    chunks = loader.load()
    for c in chunks:
        print(f"\n{'='*60}")
        print(f"Chunk ID    : {c.chunk_id}")
        print(f"Node Type   : {c.ast_node_type} → {c.ast_node_name}")
        print(f"Lines       : {c.start_line} – {c.end_line}")
        print(f"Tokens      : {c.token_count}  |  Approximate: {c.is_approximate}")
        print(f"Content Preview:\n{c.content[:300]}")
