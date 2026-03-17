# loader.py
import ast
import os
import re
import tiktoken
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# ── Data Model ───────────────────────────────────────────────────────────────

@dataclass
class CodeChunk:
    chunk_id: str
    file_path: str
    language: str
    content: str
    start_line: int
    end_line: int
    ast_node_type: str        # "function", "class", "module", "block"
    ast_node_name: str        # function/class name if available
    token_count: int
    is_approximate: bool      # True if fallback token chunker was used

# ── Language Detection ────────────────────────────────────────────────────────

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

# ── Token Counter ─────────────────────────────────────────────────────────────

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# ── Python AST Chunker ────────────────────────────────────────────────────────

def chunk_python_by_ast(source: str, file_path: str) -> List[CodeChunk]:
    """Split Python source into function/class-level chunks using AST."""
    chunks = []
    lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # fallback to token chunker if AST parsing fails
        return []

    nodes_to_extract = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes_to_extract.append(node)

    # Sort by line number
    nodes_to_extract.sort(key=lambda n: n.lineno)

    # Track covered lines to find module-level code
    covered_lines = set()
    for node in nodes_to_extract:
        end = getattr(node, "end_lineno", node.lineno)
        for l in range(node.lineno, end + 1):
            covered_lines.add(l)

    # Extract each function/class as a chunk
    for node in nodes_to_extract:
        end_line = getattr(node, "end_lineno", node.lineno)
        # Include up to 3 context lines before the node
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

    # Handle module-level code (imports, globals) not covered by any node
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

    return sorted(chunks, key=lambda c: c.start_line)


# ── Regex-Based Chunker for Java / JavaScript ─────────────────────────────────

def chunk_by_regex(source: str, file_path: str, language: str) -> List[CodeChunk]:
    """
    Rough method/function chunker for Java and JavaScript using regex.
    Falls back to token chunker if no matches found.
    """
    chunks = []
    lines = source.splitlines()

    if language == "java":
        # Match Java method signatures
        pattern = re.compile(
            r'^[ \t]*(public|private|protected|static|final|synchronized|abstract|native)?'
            r'[\s\w<>\[\],?]*\s+(\w+)\s*\([^)]*\)\s*(throws\s+[\w,\s]+)?\s*\{',
            re.MULTILINE
        )
    else:  # javascript
        # Match JS function declarations, arrow functions, and method shorthand
        pattern = re.compile(
            r'^[ \t]*(async\s+)?function\s+(\w+)\s*\(|'
            r'^[ \t]*(?:const|let|var)\s+(\w+)\s*=\s*(async\s*)?\(?.*?\)?\s*=>|'
            r'^[ \t]*(\w+)\s*\([^)]*\)\s*\{',
            re.MULTILINE
        )

    matches = list(pattern.finditer(source))
    if not matches:
        return []  # trigger fallback

    for i, match in enumerate(matches):
        start_char = match.start()
        end_char = matches[i + 1].start() if i + 1 < len(matches) else len(source)

        block = source[start_char:end_char]
        start_line = source[:start_char].count("\n") + 1
        end_line = start_line + block.count("\n")

        # Extract function/method name
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

    return sorted(chunks, key=lambda c: c.start_line)


# ── Token-Based Fallback Chunker ──────────────────────────────────────────────

def chunk_by_tokens(
    source: str,
    file_path: str,
    language: str,
    target_tokens: int = 1000,
    overlap_tokens: int = 200,
) -> List[CodeChunk]:
    """Fallback: split source into overlapping token windows."""
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

            # Overlap: retain last N tokens worth of lines
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

    # Remaining lines
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


# ── Main CodeDocumentLoader ───────────────────────────────────────────────────

class CodeDocumentLoader:
    """
    Loads source code files from a directory or single file path.
    Tags each chunk with language, line numbers, and AST metadata.
    """

    def __init__(self, source_path: str, language_override: Optional[str] = None):
        self.source_path = Path(source_path)
        self.language_override = language_override

    def load(self) -> List[CodeChunk]:
        """Returns a flat list of CodeChunk objects from all discovered files."""
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

        # Try AST chunking first
        if language == "python":
            chunks = chunk_python_by_ast(source, file_path)
        else:
            chunks = chunk_by_regex(source, file_path, language)

        # Fallback to token chunker
        if not chunks:
            print(f"[Loader] AST chunking failed for {file_path}, using token fallback.")
            chunks = chunk_by_tokens(source, file_path, language)

        return chunks


# ── Quick test (run this file directly to verify) ─────────────────────────────

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/sample_inputs/buggy_python.py"
    loader = CodeDocumentLoader(path)
    chunks = loader.load()
    for c in chunks:
        print(f"\n{'='*60}")
        print(f"Chunk ID    : {c.chunk_id}")
        print(f"File        : {c.file_path}")
        print(f"Language    : {c.language}")
        print(f"Node Type   : {c.ast_node_type} → {c.ast_node_name}")
        print(f"Lines       : {c.start_line} – {c.end_line}")
        print(f"Tokens      : {c.token_count}  |  Approximate: {c.is_approximate}")
        print(f"Content Preview:\n{c.content[:300]}")
