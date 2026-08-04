"""NorthPeak policy-docs MCP server.

Exposes three tools over stdio:
  - list_docs(): names of all policy documents.
  - read_doc(name): full text of one policy doc by name.
  - search_docs(query): docs whose text contains the query, with a snippet.

Data source: data/docs/*.md (resolved relative to the project root, i.e.
the parent of this file's directory). A doc's "name" is its filename without
the .md extension, e.g. "returns-policy".
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("northpeak-docs")

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"


def _doc_paths() -> list:
    return sorted(DOCS_DIR.glob("*.md"))


@mcp.tool()
def list_docs() -> list:
    """Return the names of all policy documents (without the .md extension)."""
    return [p.stem for p in _doc_paths()]


@mcp.tool()
def read_doc(name: str) -> str:
    """Return the full text of one policy doc by name, e.g. "returns-policy".

    The name may be given with or without the .md extension.
    """
    stem = name[:-3] if name.endswith(".md") else name
    path = DOCS_DIR / f"{stem}.md"
    if not path.exists():
        available = ", ".join(p.stem for p in _doc_paths())
        return f"No doc named {stem!r}. Available docs: {available}."
    return path.read_text(encoding="utf-8")


@mcp.tool()
def search_docs(query: str) -> list:
    """Return docs whose text contains the query (case-insensitive).

    Each match is {"name", "snippet"}, where snippet is a short excerpt
    around the first occurrence of the query.
    """
    q = query.strip().lower()
    results = []
    for path in _doc_paths():
        text = path.read_text(encoding="utf-8")
        idx = text.lower().find(q)
        if idx != -1:
            start = max(0, idx - 40)
            end = min(len(text), idx + len(q) + 40)
            snippet = text[start:end].replace("\n", " ").strip()
            results.append({"name": path.stem, "snippet": f"...{snippet}..."})
    return results


if __name__ == "__main__":
    mcp.run()
