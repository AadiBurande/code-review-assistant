# context_builder.py
import ast
from typing import Dict, List, Set


STDLIB_MODULES = {
    "os", "sys", "json", "re", "time", "datetime", "pathlib", "collections",
    "itertools", "functools", "operator", "string", "io", "urllib", "http",
    "email", "csv", "sqlite3", "logging", "argparse", "tempfile", "shutil",
    "subprocess", "threading", "multiprocessing", "asyncio", "concurrent",
    "pickle", "hashlib", "hmac", "secrets", "base64", "struct", "codecs",
    "copy", "abc", "types", "inspect", "traceback", "warnings", "contextlib",
    "dataclasses", "typing", "enum", "decimal", "fractions", "statistics",
    "math", "random", "unittest", "doctest", "pdb", "cProfile", "pstats",
    "socket", "ssl", "select", "signal", "platform", "uuid", "weakref",
}


def _is_stdlib(module_name: str) -> bool:
    return module_name.split(".")[0] in STDLIB_MODULES


def extract_imports(code: str) -> Dict[str, List[str]]:
    imports = {"stdlib": [], "third_party": []}
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bucket = "stdlib" if _is_stdlib(alias.name) else "third_party"
                    imports[bucket].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                bucket = "stdlib" if _is_stdlib(mod) else "third_party"
                imports[bucket].append(mod)
    except Exception:
        pass
    return imports


def extract_function_signatures(code: str) -> List[str]:
    sigs = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = ", ".join(arg.arg for arg in node.args.args)
                prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                sigs.append(f"{prefix} {node.name}({args})")
            elif isinstance(node, ast.ClassDef):
                sigs.append(f"class {node.name}")
    except Exception:
        pass
    return sigs


def extract_external_calls(code: str) -> Set[str]:
    calls = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    calls.add(ast.unparse(node.func))
                elif isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
    except Exception:
        pass
    return calls


def build_context(code: str, filename: str) -> str:
    """Generate rich structural context about the code to feed agents."""
    imports = extract_imports(code)
    sigs    = extract_function_signatures(code)
    calls   = extract_external_calls(code)

    lines = [
        f"[CODE CONTEXT for {filename}]",
        f"stdlib imports   : {', '.join(imports['stdlib'])      or 'none'}",
        f"third-party deps : {', '.join(imports['third_party']) or 'none'}",
        f"functions/classes: {', '.join(sigs)                   or 'none'}",
        f"external calls   : {', '.join(sorted(calls))          or 'none'}",
    ]
    return "\n".join(lines)
