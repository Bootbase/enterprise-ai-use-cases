#!/usr/bin/env python3
"""
Generate Jekyll-compatible pages from use-case markdown files.

Reads all use-case.md files, extracts metadata from the markdown tables,
adds Jekyll front matter, and writes them to docs/_use_cases/.
Also copies solution-design.md, implementation-guide.md, evaluation.md,
and references.md if they exist.
"""

import os
import re
import sys
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_CASES_DIR = os.path.join(REPO_ROOT, "use-cases")
DOCS_DIR = os.path.join(REPO_ROOT, "docs")
COLLECTION_DIR = os.path.join(DOCS_DIR, "_use_cases")

# Map category directory names to display names
CATEGORY_MAP = {
    "document-processing": "Document Processing",
    "customer-service": "Customer Service",
    "workflow-automation": "Workflow Automation",
    "code-and-devops": "Code & DevOps",
    "knowledge-management": "Knowledge Management",
    "industry-specific": "Industry-Specific",
}

# Category icons (emoji for simplicity, works in Jekyll)
CATEGORY_ICONS = {
    "Document Processing": "file-text",
    "Customer Service": "headphones",
    "Workflow Automation": "settings",
    "Code & DevOps": "terminal",
    "Knowledge Management": "book-open",
    "Industry-Specific": "briefcase",
}

# Files that make up a detailed use case
DETAIL_FILES = [
    "solution-design.md",
    "implementation-guide.md",
    "evaluation.md",
    "references.md",
]


def extract_metadata(content: str) -> dict:
    """Extract metadata from the markdown metadata table."""
    metadata = {}

    # Extract title from first H1
    title_match = re.search(r"^#\s+UC-\d+:\s*(.+)$", content, re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()

    # Extract fields from the metadata table
    field_pattern = re.compile(
        r"\|\s*\*\*(\w[\w\s]*)\*\*\s*\|\s*(.+?)\s*\|", re.MULTILINE
    )
    for match in field_pattern.finditer(content):
        key = match.group(1).strip().lower()
        value = match.group(2).strip().strip("`")
        metadata[key] = value

    return metadata


def extract_section(content: str, section_name: str) -> str:
    """Extract a specific section's content from markdown."""
    pattern = re.compile(
        rf"^##\s+{re.escape(section_name)}\s*\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""


def strip_metadata_and_title(content: str) -> str:
    """Remove the title and metadata table, return remaining content."""
    # Remove title line
    content = re.sub(r"^#\s+UC-\d+:.*\n+", "", content, count=1)
    # Remove metadata section (## Metadata ... ---)
    content = re.sub(
        r"^##\s+Metadata\s*\n.*?(?=^---\s*$)",
        "",
        content,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    # Remove leading ---
    content = re.sub(r"^---\s*\n", "", content, count=1, flags=re.MULTILINE)
    return content.strip()


def process_use_case(category_dir: str, uc_dir: str) -> dict | None:
    """Process a single use case directory and return page data."""
    uc_path = os.path.join(USE_CASES_DIR, category_dir, uc_dir)
    use_case_file = os.path.join(uc_path, "use-case.md")

    if not os.path.isfile(use_case_file):
        return None

    with open(use_case_file, "r", encoding="utf-8") as f:
        content = f.read()

    metadata = extract_metadata(content)
    if not metadata.get("id"):
        return None

    uc_id = metadata["id"]
    category_name = CATEGORY_MAP.get(category_dir, category_dir)
    status = metadata.get("status", "research")

    # Extract problem statement for the card description
    problem = extract_section(content, "Problem Statement")
    # Take first 2 sentences for summary
    sentences = re.split(r"(?<=[.!?])\s+", problem)
    summary = " ".join(sentences[:2]) if sentences else ""
    if len(summary) > 300:
        summary = summary[:297] + "..."

    # Check which detail files exist
    has_details = {}
    for detail_file in DETAIL_FILES:
        detail_path = os.path.join(uc_path, detail_file)
        has_details[detail_file.replace(".md", "").replace("-", "_")] = os.path.isfile(
            detail_path
        )

    # Build the slug
    slug = uc_dir

    return {
        "id": uc_id,
        "title": metadata.get("title", uc_dir),
        "category": category_name,
        "category_dir": category_dir,
        "category_icon": CATEGORY_ICONS.get(category_name, "folder"),
        "industry": metadata.get("industry", "Cross-Industry"),
        "complexity": metadata.get("complexity", "Medium"),
        "status": status,
        "summary": summary,
        "slug": slug,
        "content": content,
        "uc_path": uc_path,
        "has_details": has_details,
    }


def write_use_case_page(uc_data: dict):
    """Write a Jekyll page for a use case."""
    slug = uc_data["slug"]
    output_dir = os.path.join(COLLECTION_DIR, slug)
    os.makedirs(output_dir, exist_ok=True)

    # Write main use-case page with front matter
    front_matter = f"""---
layout: use-case
title: "{uc_data['title']}"
uc_id: "{uc_data['id']}"
category: "{uc_data['category']}"
category_dir: "{uc_data['category_dir']}"
category_icon: "{uc_data['category_icon']}"
industry: "{uc_data['industry']}"
complexity: "{uc_data['complexity']}"
status: "{uc_data['status']}"
summary: "{uc_data['summary'].replace('"', '\\"')}"
slug: "{slug}"
has_solution_design: {str(uc_data['has_details']['solution_design']).lower()}
has_implementation_guide: {str(uc_data['has_details']['implementation_guide']).lower()}
has_evaluation: {str(uc_data['has_details']['evaluation']).lower()}
has_references: {str(uc_data['has_details']['references']).lower()}
permalink: /use-cases/{slug}/
---

"""
    # Strip the title and metadata table from content since we show them via layout
    body = strip_metadata_and_title(uc_data["content"])

    with open(os.path.join(output_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write(front_matter + body)

    # Copy detail files if they exist
    for detail_file in DETAIL_FILES:
        src = os.path.join(uc_data["uc_path"], detail_file)
        if os.path.isfile(src):
            with open(src, "r", encoding="utf-8") as f:
                detail_content = f.read()

            detail_name = detail_file.replace(".md", "")
            detail_title = detail_name.replace("-", " ").title()

            detail_front = f"""---
layout: use-case-detail
title: "{detail_title} — {uc_data['title']}"
uc_id: "{uc_data['id']}"
uc_title: "{uc_data['title']}"
detail_type: "{detail_name}"
detail_title: "{detail_title}"
category: "{uc_data['category']}"
status: "{uc_data['status']}"
slug: "{slug}"
permalink: /use-cases/{slug}/{detail_name}/
---

"""
            # Strip the first H1 title from detail content
            detail_body = re.sub(r"^#\s+.*\n+", "", detail_content, count=1)

            with open(
                os.path.join(output_dir, f"{detail_name}.md"), "w", encoding="utf-8"
            ) as f:
                f.write(detail_front + detail_body)


def main():
    """Main entry point."""
    # Clean and recreate collection dir
    if os.path.exists(COLLECTION_DIR):
        shutil.rmtree(COLLECTION_DIR)
    os.makedirs(COLLECTION_DIR, exist_ok=True)

    all_use_cases = []

    for category_dir in sorted(os.listdir(USE_CASES_DIR)):
        category_path = os.path.join(USE_CASES_DIR, category_dir)
        if not os.path.isdir(category_path) or category_dir.startswith("_"):
            continue
        if category_dir == "PROMPT.md":
            continue

        for uc_dir in sorted(os.listdir(category_path)):
            uc_path = os.path.join(category_path, uc_dir)
            if not os.path.isdir(uc_path):
                continue

            uc_data = process_use_case(category_dir, uc_dir)
            if uc_data:
                all_use_cases.append(uc_data)
                write_use_case_page(uc_data)
                print(f"  ✓ {uc_data['id']}: {uc_data['title']} [{uc_data['status']}]")

    print(f"\nGenerated {len(all_use_cases)} use case pages in {COLLECTION_DIR}")

    # Summary
    statuses = {}
    for uc in all_use_cases:
        s = uc["status"]
        statuses[s] = statuses.get(s, 0) + 1
    for s, count in sorted(statuses.items()):
        print(f"  {s}: {count}")


if __name__ == "__main__":
    main()
