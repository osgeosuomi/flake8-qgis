import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path

"""
A script to update qgis_return_methods.json
with methods that possibly return a value that should be checked.

You have to have a compiled QGIS or access to sip files for running the script.
"""

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger(__name__)

DOCSTRING_START = "%Docstring"
DOCSTRING_END = "%End"

RETURN_LINE_RE = re.compile(r"\breturn(?:s)?\b")
PYNAME_RE = re.compile(r"/PyName=([^/]+)/")
CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_]\w*)")

TOO_COMMON_METHOD_NAMES = {"run", "get"}

CATEGORY_KEYWORDS: dict[str, tuple[str | re.Pattern, ...]] = {
    "methods_to_check": (
        "success",
        "returns true if",
        re.compile(r"[a-z]result"),
        "``none`` if unable to",
    ),
}


def _docstring_has_keyword(docstring: str, keyword: str | re.Pattern) -> bool:
    doc_lower = docstring.lower()
    search = RETURN_LINE_RE.search(doc_lower)
    if not search:
        return False
    if isinstance(keyword, str):
        keyword_found = keyword.lower() in doc_lower
    else:
        keyword_found = keyword.search(doc_lower) is not None
    if keyword_found:
        if keyword == "success" and "which returns with success" in doc_lower:
            return False
        index = doc_lower.index("return")
        LOGGER.info("\n\n######################################")
        LOGGER.info("Found keyword '%s' in docstring:", keyword)
        LOGGER.info(docstring[index : index + 200].rstrip())
    return keyword_found


def _is_common_name(name: str) -> bool:
    if name in TOO_COMMON_METHOD_NAMES:
        # Too common name
        LOGGER.info("Skipping '%s' for being too common", name)
        return True
    return False


def _extract_py_name(signature: str) -> str | None:
    match = PYNAME_RE.search(signature)
    if match:
        value = match.group(1).strip()
        if "," in value:
            value = value.split(",", 1)[0].strip()

        if _is_common_name(value):
            return None

        return value
    return None


def _extract_method_name(signature: str) -> str | None:
    match = re.search(r"([A-Za-z_]\w*)\s*\(", signature)
    if not match:
        return None

    name = match.group(1)
    if name == "operator":
        return None

    signature = signature.lstrip()
    if signature.startswith((f"{name}(", f"explicit {name}(")):
        return None

    if _is_common_name(name):
        return None

    return name


def _looks_like_signature_start(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("%"):
        return False
    if stripped.startswith("#"):
        return False
    if stripped.startswith(("class ", "enum ")):
        return False
    return "(" in stripped


def _iter_sip_methods(path: Path) -> list[tuple[str, str]]:  # noqa: C901, PLR0912, PLR0915
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    methods: list[tuple[str, str]] = []
    pending_signature: list[str] = []
    pending_name: str | None = None
    awaiting_docstring = False

    brace_depth = 0
    class_stack: list[tuple[str, int]] = []
    pending_class: str | None = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        opens = line.count("{")
        closes = line.count("}")
        class_match = CLASS_RE.match(line)
        if class_match:
            if "{" in line:
                class_stack.append((class_match.group(1), brace_depth + opens - closes))
                pending_class = None
            else:
                pending_class = class_match.group(1)
        elif pending_class and "{" in line:
            class_stack.append((pending_class, brace_depth + opens - closes))
            pending_class = None

        current_class = class_stack[-1][0] if class_stack else None

        if stripped.startswith(DOCSTRING_START) and not awaiting_docstring:
            brace_depth += opens - closes
            while class_stack and brace_depth < class_stack[-1][1]:
                class_stack.pop()
            i += 1
            while i < len(lines) and lines[i].strip() != DOCSTRING_END:
                i += 1
            i += 1
            continue

        if awaiting_docstring:
            if not stripped:
                brace_depth += opens - closes
                while class_stack and brace_depth < class_stack[-1][1]:
                    class_stack.pop()
                i += 1
                continue
            if stripped.startswith(DOCSTRING_START):
                doc_lines: list[str] = []
                i += 1
                while i < len(lines) and lines[i].strip() != DOCSTRING_END:
                    doc_lines.append(lines[i])
                    i += 1
                docstring = "\n".join(doc_lines)
                if pending_name:
                    methods.append((pending_name, docstring))
                pending_name = None
                awaiting_docstring = False
                if i < len(lines) and lines[i].strip() == DOCSTRING_END:
                    i += 1
                continue

            pending_name = None
            awaiting_docstring = False
            brace_depth += opens - closes
            while class_stack and brace_depth < class_stack[-1][1]:
                class_stack.pop()
            i += 1
            continue

        if pending_signature or _looks_like_signature_start(line):
            pending_signature.append(line.strip())
            if ";" in line:
                signature = " ".join(pending_signature)
                pending_signature = []
                name = _extract_method_name(signature)
                if name:
                    pending_name = _extract_py_name(signature) or name
                    if current_class:
                        pending_name = f"{current_class}.{pending_name}"
                    awaiting_docstring = True
            brace_depth += opens - closes
            while class_stack and brace_depth < class_stack[-1][1]:
                class_stack.pop()
            i += 1
            continue

        brace_depth += opens - closes
        while class_stack and brace_depth < class_stack[-1][1]:
            class_stack.pop()
        i += 1

    return methods


def parse_qgis_sip_methods(root: Path) -> dict[str, list[str]]:
    methods: dict[str, set[str]] = defaultdict(set[str])

    if not root.exists():
        return {"optional_methods": [], "bool_message_methods": []}

    for path in root.rglob("*.sip"):
        for method_name, docstring in _iter_sip_methods(path):
            for category, keywords in CATEGORY_KEYWORDS.items():
                if method_name not in methods[category] and any(
                    _docstring_has_keyword(docstring, keyword) for keyword in keywords
                ):
                    LOGGER.info(f"{category}: {method_name}")
                    LOGGER.info("######################################")
                    methods[category].add(method_name)

    return {category: sorted(methods[category]) for category in methods}


def write_return_methods_json(data: dict[str, list[str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate PyQGIS return-method lists from sip files."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("/home/foo/dev/QGIS/build-debug/python"),
        help="Path to QGIS compiled python/sip root.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "flake8_qgis"
        / "qgis_return_methods.json",
        help="Path to output JSON file.",
    )
    args = parser.parse_args()

    data = parse_qgis_sip_methods(args.root)
    write_return_methods_json(data, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
