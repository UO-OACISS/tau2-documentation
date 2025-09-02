#!/usr/bin/env python3

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional

# --- Configuration ---
CWD = Path.cwd()
SRC_DIR = CWD / "src"
MODULE_ROOT = SRC_DIR / "modules/ROOT"
PAGES_DIR = MODULE_ROOT / "pages"
PARTIALS_DIR = MODULE_ROOT / "partials"
DEST_NAV_FILE = MODULE_ROOT / "nav.adoc"

MASTER_FILES = [
    "usersguide/usersguide.adoc",
    "installguide/installguide.adoc",
    "referenceguide/referenceguide.adoc",
]

# Navigation settings
MAX_NAV_DEPTH = 4
# Only include chapter-level headings (===) in the nav for page internals.
ALLOWED_SECTION_LEVELS = {3}

IGNORE_TITLES = {"description", "options", "example", "examples", "notes", "see also"}

# Aliasing for shared content. Support both "basename" master keys and "relative path" keys.
ALIAS_MAP = {
    # Original mapping (by basename)
    "referenceguide.adoc": {
        "perfdmf/book.adoc": "referenceguide/taudb-alias.adoc",
        "newguide/introduction.adoc": "referenceguide/installation-alias.adoc",
    },
    # Full relative master path for robustness
    "referenceguide/referenceguide.adoc": {
        "perfdmf/book.adoc": "referenceguide/taudb-alias.adoc",
        "newguide/introduction.adoc": "referenceguide/installation-alias.adoc",
    },
}

# -------------- Utilities --------------

def read_text_lines(p: Path) -> List[str]:
    try:
        return p.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Warning: Could not read {p}: {e}")
        return []

def debug_head(p: Path, max_lines: int = 12):
    lines = read_text_lines(p)
    print(f"DEBUG: First {max_lines} lines of {p}:")
    for i, line in enumerate(lines[:max_lines]):
        print(f"  {i+1:2d}: {repr(line)}")
    if len(lines) > max_lines:
        print(f"  ... ({len(lines) - max_lines} more lines)")

def make_anchor_from_title(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")

def extract_include_files(file_path: Path) -> List[Path]:
    """Return resolved include file paths present in a file."""
    includes: List[Path] = []
    lines = read_text_lines(file_path)
    pattern = re.compile(r'include::([^[\]]+)\[\]')
    for line in lines:
        m = pattern.search(line)
        if not m:
            continue
        include_rel_path = m.group(1).strip()
        inc = (file_path.parent / include_rel_path).resolve()
        if PARTIALS_DIR in inc.parents:
            continue
        if not inc.exists():
            print(f"Warning: Include file not found: {inc}")
            continue
        includes.append(inc)
    return includes

def get_title_and_anchor(file_path: Path, prefer_doc_title: bool = False) -> Tuple[str, str]:
    """
    Returns (title, anchor).
    - If prefer_doc_title=True, look for '= ' (doc title).
    - Otherwise, pick the first heading of level >= 2 ('== ' or deeper).
    """
    lines = read_text_lines(file_path)
    if not lines:
        return "Untitled", ""

    anchor: str = ""
    title: Optional[str] = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if (not line or line.startswith("//") or line.startswith(":") or line.startswith("include::")):
            i += 1
            continue

        if line.startswith("[[") and line.endswith("]]"):
            anchor = line[2:-2].strip()
            i += 1
            # find next heading
            while i < len(lines):
                peek = lines[i].strip()
                if (not peek or peek.startswith("//") or peek.startswith(":") or peek.startswith("include::")):
                    i += 1
                    continue
                if prefer_doc_title:
                    if peek.startswith("= ") and not peek.startswith("== "):
                        title = peek.lstrip("= ").strip()
                        return (title, anchor)
                m = re.match(r"^(=+)\s+(.+)$", peek)
                if m:
                    level = len(m.group(1))
                    if prefer_doc_title:
                        if level == 1:
                            title = m.group(2).strip()
                            return (title, anchor)
                        break
                    if level >= 2:
                        title = m.group(2).strip()
                        if not anchor:
                            anchor = make_anchor_from_title(title)
                        return (title, anchor)
                break
            continue

        if prefer_doc_title:
            if line.startswith("= ") and not line.startswith("== "):
                title = line.lstrip("= ").strip()
                if not anchor:
                    anchor = make_anchor_from_title(title)
                return (title, anchor)
        else:
            m = re.match(r"^(=+)\s+(.+)$", line)
            if m:
                level = len(m.group(1))
                if level >= 2:
                    title = m.group(2).strip()
                    if not anchor:
                        anchor = make_anchor_from_title(title)
                    return (title, anchor)

        i += 1

    return ("Untitled", anchor)

def extract_section_headings(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Returns list of (level, anchor, title) for headings within a file.
    Only collects headings where 'level' is in ALLOWED_SECTION_LEVELS.
    Prefer an explicit [[id]] immediately preceding the heading; otherwise, derive an anchor.
    """
    lines = read_text_lines(file_path)
    if not lines:
        return []

    results: List[Tuple[int, str, str]] = []
    i = 0
    last_anchor: Optional[str] = None

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("[[") and line.endswith("]]"):
            last_anchor = line[2:-2].strip()
            i += 1
            continue

        if (not line or line.startswith("//") or line.startswith(":") or line.startswith("include::")):
            i += 1
            continue

        m = re.match(r"^(=+)\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if title and title.lower() not in IGNORE_TITLES and level in ALLOWED_SECTION_LEVELS:
                anchor = last_anchor or make_anchor_from_title(title)
                results.append((level, anchor, title))
            last_anchor = None
        else:
            last_anchor = None

        i += 1

    return results

def is_aggregator_page(file_path: Path) -> bool:
    """
    Heuristic: a page that has a top heading and then mostly include:: lines.
    We detect at least one include and no in-page (===) headings.
    """
    includes = extract_include_files(file_path)
    if not includes:
        return False

    lines = read_text_lines(file_path)
    for line in lines:
        if re.match(r"^===\s+", line.strip()):
            return False
    return True

def resolve_alias(master_key: str, xref_path_str: str) -> Tuple[str, Optional[str]]:
    """
    Returns (final_xref_path, alias_path_if_created_or_None).
    Looks up alias rules for both the full master path and its basename.
    """
    basename_key = Path(master_key).name
    for key in (master_key, basename_key):
        if key in ALIAS_MAP and xref_path_str in ALIAS_MAP[key]:
            return (ALIAS_MAP[key][xref_path_str], ALIAS_MAP[key][xref_path_str])
    return (xref_path_str, None)

def create_alias_file(alias_page_path_str: str, target_page_path_str: str):
    """Creates an AsciiDoc alias file that includes the target page and sets page-alias."""
    alias_abs_path = PAGES_DIR / alias_page_path_str
    target_abs_path = PAGES_DIR / target_page_path_str

    alias_abs_path.parent.mkdir(parents=True, exist_ok=True)
    relative_include_path = os.path.relpath(target_abs_path, alias_abs_path.parent)

    content = (
        f":page-alias: {target_page_path_str}\n"
        f"include::{relative_include_path}[]\n"
    )
    alias_abs_path.write_text(content, encoding="utf-8")
    print(f"  -> Generated alias file: {alias_page_path_str}")

# -------------- Navigation generation --------------

def add_entry(nav_lines: List[str], level: int, xref_target: str, title: str, anchor: str = ""):
    indent = "*" * max(1, min(level, MAX_NAV_DEPTH))
    if anchor:
        nav_lines.append(f"{indent} xref:{xref_target}#{anchor}[{title}]")
    else:
        nav_lines.append(f"{indent} xref:{xref_target}[{title}]")

def process_aggregator_children_as_alias_sections(
    aggregator_file: Path,
    alias_xref_target: str,
    current_level: int,
    nav_lines: List[str]
):
    """
    For aggregator pages with an alias applied, list their included chapters
    as sections on the alias page instead of linking to the shared chapter files.
    """
    for inc in extract_include_files(aggregator_file):
        inc_title, inc_anchor = get_title_and_anchor(inc, prefer_doc_title=False)
        if not inc_title or inc_title.lower() == "untitled":
            continue
        # Use the alias page as the target, but the chapter's anchor
        add_entry(nav_lines, min(current_level + 1, MAX_NAV_DEPTH), alias_xref_target, inc_title, inc_anchor)

def process_page(
    file_path: Path,
    master_key: str,
    current_level: int,
    nav_lines: List[str],
    visited: set
):
    """
    Add a page and (limited) substructure to nav.
    - Adds the page itself (first heading >= '== '), using alias if configured.
    - Adds in-page headings (=== only by default), excluding the page's own first heading.
    - If the page is an aggregator and an alias is applied, show its children as sections on the alias page.
    """
    try:
        xref_path = file_path.relative_to(PAGES_DIR)
    except ValueError:
        print(f"Warning: File outside pages dir: {file_path}")
        return

    xref_path_str = str(xref_path)

    # Apply alias if this page is shared under this master
    final_xref_path, alias_created = resolve_alias(master_key, xref_path_str)
    alias_applied = alias_created is not None
    if alias_applied:
        create_alias_file(alias_created, xref_path_str)

    # Page title and anchor
    title, anchor = get_title_and_anchor(file_path, prefer_doc_title=False)
    if not title or title.lower() == "untitled":
        print(f"Warning: Skipping file with problematic title '{title}': {file_path}")
        debug_head(file_path, 15)
        return

    # Add the page entry
    add_entry(nav_lines, current_level, final_xref_path, title, anchor)

    # Aggregator handling: if alias is applied, render chapter links against the alias page
    if is_aggregator_page(file_path) and alias_applied:
        process_aggregator_children_as_alias_sections(file_path, final_xref_path, current_level, nav_lines)
        return  # Do not recurse into real chapter files under an alias context

    # In-page sections (only === headings by default), skip duplicate of the page's main heading
    sections = extract_section_headings(file_path)
    for level, sub_anchor, sub_title in sections:
        if (sub_anchor == anchor) or (sub_title.strip().lower() == title.strip().lower()):
            continue  # avoid "Introduction -> Introduction" duplicates
        sub_nav_level = current_level + (level - 2)  # '===' => +1
        if sub_nav_level <= MAX_NAV_DEPTH:
            add_entry(nav_lines, sub_nav_level, final_xref_path, sub_title, sub_anchor)

    # If it's an aggregator but no alias is applied, drill into its includes one level (chapters)
    if is_aggregator_page(file_path):
        for inc in extract_include_files(file_path):
            key = (str(inc), master_key)
            if key in visited:
                continue
            visited.add(key)
            process_page(inc, master_key, min(current_level + 1, MAX_NAV_DEPTH), nav_lines, visited)

def main():
    print("=== Generating navigation from AsciiDoc source ===")

    header = [
        "// WARNING: This file is generated. DO NOT EDIT DIRECTLY.",
        "",
    ]
    nav_lines: List[str] = []
    visited: set = set()

    for master_file_rel_path in MASTER_FILES:
        master_path = PAGES_DIR / master_file_rel_path

        if not master_path.exists():
            print(f"Warning: Master file not found: {master_path}")
            continue

        print(f"Processing master: {master_file_rel_path}")

        # Master entry: use document title (= ) if present
        book_title, book_anchor = get_title_and_anchor(master_path, prefer_doc_title=True)
        xref_path = master_path.relative_to(PAGES_DIR)
        if book_anchor:
            nav_lines.append(f"* xref:{xref_path}#{book_anchor}[{book_title}]")
        else:
            nav_lines.append(f"* xref:{xref_path}[{book_title}]")

        # Under each master, process includes directly
        includes = extract_include_files(master_path)
        master_key = str(master_path.relative_to(PAGES_DIR))
        for inc in includes:
            key = (str(inc), master_key)
            if key in visited:
                continue
            visited.add(key)
            process_page(inc, master_key, current_level=2, nav_lines=nav_lines, visited=visited)

        # separator
        if master_file_rel_path != MASTER_FILES[-1]:
            nav_lines.append("")

    final_content = "\n".join(header + nav_lines) + "\n"
    DEST_NAV_FILE.write_text(final_content, encoding="utf-8")

    # Summary
    print(f"Successfully generated navigation: {DEST_NAV_FILE}")
    print(f"Total navigation entries: {len([l for l in nav_lines if l.strip().startswith('*')])}")

if __name__ == "__main__":
    main()