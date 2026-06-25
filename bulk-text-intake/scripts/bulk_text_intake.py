#!/usr/bin/env python3
"""Batch extract, classify, and summarize mixed text-bearing files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


SUPPORTED_EXTS = {
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".xml",
    ".java",
    ".py",
    ".html",
    ".md",
    ".js",
}

CLASS_BY_EXT = {
    ".doc": "office_document",
    ".docx": "office_document",
    ".ppt": "office_presentation",
    ".pptx": "office_presentation",
    ".xls": "office_spreadsheet",
    ".xlsx": "office_spreadsheet",
    ".java": "source_code",
    ".py": "source_code",
    ".js": "source_code",
    ".xml": "markup",
    ".html": "markup",
    ".md": "markup",
}

TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG|REVIEW|OPTIMIZE)\b[:\-\s]*(.*)", re.IGNORECASE)
TEXT_EXTS = {".xml", ".java", ".py", ".html", ".md", ".js"}
REVIEW_FIELDNAMES = [
    "kind",
    "path",
    "extension",
    "location",
    "line",
    "token",
    "author",
    "date",
    "text",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input file or directory")
    parser.add_argument("--output", "-o", type=Path, default=Path("bulk_text_output"))
    parser.add_argument("--max-bytes", type=int, default=50_000_000, help="Skip extraction above this size")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files and folders")
    return parser.parse_args()


def iter_files(root: Path, include_hidden: bool) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if not include_hidden and any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        yield path


def safe_rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return path.name


def output_name(rel: str) -> str:
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:10]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", rel).strip("_") or "file"
    return f"{stem}.{digest}.txt"


def decode_bytes(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def extract_text_file(path: Path) -> tuple[str, str]:
    return decode_bytes(path.read_bytes()), "text"


def read_zip_xml(path: Path, members: Iterable[str]) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as zf:
        for name in members:
            try:
                raw = zf.read(name)
            except KeyError:
                continue
            try:
                root = ElementTree.fromstring(raw)
            except ElementTree.ParseError:
                continue
            text = " ".join(t.strip() for t in root.itertext() if t and t.strip())
            if text:
                chunks.append(html.unescape(text))
    return "\n".join(chunks)


def local_name(name: str) -> str:
    if "}" in name:
        return name.rsplit("}", 1)[1]
    return name


def attr_value(element: ElementTree.Element, attr_name: str) -> str:
    for key, value in element.attrib.items():
        if local_name(key) == attr_name:
            return value
    return ""


def normalized_text(element: ElementTree.Element) -> str:
    return " ".join(text.strip() for text in element.itertext() if text and text.strip())


def office_members(path: Path, ext: str) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
    if ext == ".docx":
        return [name for name in names if name.startswith("word/") and name.endswith(".xml")]
    if ext == ".pptx":
        return sorted(name for name in names if name.startswith("ppt/slides/") and name.endswith(".xml"))
    if ext == ".xlsx":
        preferred = [name for name in names if name == "xl/sharedStrings.xml"]
        preferred.extend(name for name in names if name.startswith("xl/worksheets/") and name.endswith(".xml"))
        return preferred
    return []


def extract_ooxml(path: Path, ext: str) -> tuple[str, str]:
    members = office_members(path, ext)
    if not members:
        return "", "ooxml-empty"
    return read_zip_xml(path, members), "ooxml"


def read_xml_member(zf: zipfile.ZipFile, name: str) -> ElementTree.Element | None:
    try:
        return ElementTree.fromstring(zf.read(name))
    except (KeyError, ElementTree.ParseError):
        return None


def extract_docx_comments(zf: zipfile.ZipFile, rel: str, ext: str) -> list[dict[str, str]]:
    root = read_xml_member(zf, "word/comments.xml")
    if root is None:
        return []
    findings = []
    for element in root.iter():
        if local_name(element.tag) != "comment":
            continue
        text = normalized_text(element)
        if not text:
            continue
        comment_id = attr_value(element, "id")
        findings.append(
            {
                "kind": "office_comment",
                "path": rel,
                "extension": ext,
                "location": f"comment:{comment_id}" if comment_id else "comment",
                "line": "",
                "token": "COMMENT",
                "author": attr_value(element, "author"),
                "date": attr_value(element, "date"),
                "text": text[:500],
            }
        )
    return findings


def extract_pptx_comments(zf: zipfile.ZipFile, rel: str, ext: str) -> list[dict[str, str]]:
    authors: dict[str, str] = {}
    author_root = read_xml_member(zf, "ppt/commentAuthors.xml")
    if author_root is not None:
        for element in author_root.iter():
            if local_name(element.tag) == "cmAuthor":
                author_id = attr_value(element, "id")
                name = attr_value(element, "name") or attr_value(element, "initials")
                if author_id:
                    authors[author_id] = name

    findings = []
    for name in sorted(member for member in zf.namelist() if member.startswith("ppt/comments/") and member.endswith(".xml")):
        root = read_xml_member(zf, name)
        if root is None:
            continue
        for element in root.iter():
            if local_name(element.tag) not in {"cm", "comment"}:
                continue
            text = normalized_text(element)
            if not text:
                continue
            author_id = attr_value(element, "authorId")
            idx = attr_value(element, "idx")
            findings.append(
                {
                    "kind": "office_comment",
                    "path": rel,
                    "extension": ext,
                    "location": f"{name}:{idx}" if idx else name,
                    "line": "",
                    "token": "COMMENT",
                    "author": authors.get(author_id, author_id),
                    "date": attr_value(element, "dt") or attr_value(element, "date"),
                    "text": text[:500],
                }
            )
    return findings


def extract_xlsx_comments(zf: zipfile.ZipFile, rel: str, ext: str) -> list[dict[str, str]]:
    findings = []
    for name in sorted(member for member in zf.namelist() if member.startswith("xl/") and "comments" in member and member.endswith(".xml")):
        root = read_xml_member(zf, name)
        if root is None:
            continue
        authors = [normalized_text(element) for element in root.iter() if local_name(element.tag) == "author"]
        for element in root.iter():
            tag = local_name(element.tag)
            if tag not in {"comment", "threadedComment"}:
                continue
            text = normalized_text(element)
            if not text:
                continue
            author_id = attr_value(element, "authorId")
            author = ""
            if author_id.isdigit() and int(author_id) < len(authors):
                author = authors[int(author_id)]
            else:
                author = attr_value(element, "personId") or author_id
            location = attr_value(element, "ref") or attr_value(element, "id") or name
            findings.append(
                {
                    "kind": "office_comment",
                    "path": rel,
                    "extension": ext,
                    "location": location,
                    "line": "",
                    "token": "COMMENT",
                    "author": author,
                    "date": attr_value(element, "dT") or attr_value(element, "date"),
                    "text": text[:500],
                }
            )
    return findings


def office_comment_findings(path: Path, rel: str, ext: str) -> list[dict[str, str]]:
    if ext not in {".docx", ".pptx", ".xlsx"}:
        return []
    try:
        with zipfile.ZipFile(path) as zf:
            if ext == ".docx":
                return extract_docx_comments(zf, rel, ext)
            if ext == ".pptx":
                return extract_pptx_comments(zf, rel, ext)
            if ext == ".xlsx":
                return extract_xlsx_comments(zf, rel, ext)
    except (OSError, zipfile.BadZipFile):
        return []
    return []


def run_converter(command: list[str], timeout: int = 60) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0 and result.stdout:
        return decode_bytes(result.stdout)
    return None


def extract_legacy_office(path: Path, ext: str) -> tuple[str, str]:
    if ext == ".doc":
        for tool in ("antiword", "catdoc"):
            if shutil.which(tool):
                text = run_converter([tool, str(path)])
                if text:
                    return text, tool
    if shutil.which("libreoffice"):
        with tempfile.TemporaryDirectory() as tmp:
            cmd = [
                "libreoffice",
                "--headless",
                "--convert-to",
                "txt:Text",
                "--outdir",
                tmp,
                str(path),
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=False, timeout=120)
            except (OSError, subprocess.TimeoutExpired):
                pass
            txt_files = list(Path(tmp).glob("*.txt"))
            if txt_files:
                return decode_bytes(txt_files[0].read_bytes()), "libreoffice"
    if shutil.which("strings"):
        text = run_converter(["strings", str(path)])
        if text and text.strip():
            return text, "strings-partial"
    return "", "unsupported-legacy-office"


def extract(path: Path, ext: str, max_bytes: int) -> tuple[str, str, str]:
    if path.stat().st_size > max_bytes:
        return "", "skipped", f"larger than --max-bytes ({max_bytes})"
    try:
        if ext in TEXT_EXTS:
            text, method = extract_text_file(path)
        elif ext in {".docx", ".pptx", ".xlsx"}:
            text, method = extract_ooxml(path, ext)
        elif ext in {".doc", ".ppt", ".xls"}:
            text, method = extract_legacy_office(path, ext)
        else:
            text, method = "", "auxiliary-not-extracted"
    except (OSError, zipfile.BadZipFile, RuntimeError, ElementTree.ParseError) as exc:
        return "", "failed", f"{type(exc).__name__}: {exc}"
    if text.strip():
        return text, "ok", method
    if method == "unsupported-legacy-office":
        return "", "failed", "legacy Office extraction requires a converter"
    if method == "auxiliary-not-extracted":
        return "", "auxiliary", "extension outside primary scope"
    return "", "empty", method


def todo_findings(rel: str, ext: str, text: str) -> list[dict[str, str]]:
    if ext not in SUPPORTED_EXTS:
        return []
    findings = []
    for i, line in enumerate(text.splitlines(), start=1):
        match = TODO_RE.search(line)
        if not match:
            continue
        snippet = " ".join(line.strip().split())
        findings.append(
            {
                "kind": "todo",
                "path": rel,
                "extension": ext,
                "location": "",
                "line": str(i),
                "token": match.group(1).upper(),
                "author": "",
                "date": "",
                "text": snippet[:500],
            }
        )
    return findings


def write_summary(
    output: Path,
    manifest: list[dict[str, object]],
    findings: list[dict[str, str]],
    input_path: Path,
) -> None:
    total = len(manifest)
    supported = sum(1 for item in manifest if item["supported"])
    by_class = Counter(str(item["classification"]) for item in manifest)
    by_ext = Counter(str(item["extension"]) or "[none]" for item in manifest if item["supported"])
    by_status = Counter(str(item["status"]) for item in manifest)
    lines = [
        "# Bulk Text Intake Summary",
        "",
        f"Input: `{input_path}`",
        f"Total files discovered: {total}",
        f"Primary supported files: {supported}",
        f"Auxiliary files: {total - supported}",
        f"Review findings: {len(findings)}",
        "",
        "## By Classification",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in sorted(by_class.items()))
    lines.extend(["", "## Supported Extensions", ""])
    lines.extend(f"- {name}: {count}" for name, count in sorted(by_ext.items()))
    lines.extend(["", "## Extraction Status", ""])
    lines.extend(f"- {name}: {count}" for name, count in sorted(by_status.items()))
    if findings:
        by_token = Counter(item["token"] for item in findings if item["kind"] == "todo")
        if by_token:
            lines.extend(["", "## TODO Tokens", ""])
            lines.extend(f"- {name}: {count}" for name, count in sorted(by_token.items()))
        lines.extend(["", "## Finding Kinds", ""])
        by_kind = Counter(item["kind"] for item in findings)
        lines.extend(f"- {name}: {count}" for name, count in sorted(by_kind.items()))
        by_author = Counter(item["author"] for item in findings if item.get("author"))
        if by_author:
            lines.extend(["", "## Office Comment Authors", ""])
            lines.extend(f"- {name}: {count}" for name, count in sorted(by_author.items()))
    output.joinpath("summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output = args.output.resolve()
    extracted_dir = output / "extracted_text"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    findings: list[dict[str, str]] = []
    todo_rows: list[dict[str, str]] = []
    comment_rows: list[dict[str, str]] = []
    base = input_path if input_path.is_dir() else input_path.parent

    for path in iter_files(input_path, args.include_hidden):
        ext = path.suffix.lower()
        rel = safe_rel(path, base)
        supported = ext in SUPPORTED_EXTS
        classification = CLASS_BY_EXT.get(ext, "auxiliary")
        text, status, note = extract(path, ext, args.max_bytes)
        text_rel = ""
        if text:
            out_file = extracted_dir / output_name(rel)
            out_file.write_text(text, encoding="utf-8", errors="replace")
            text_rel = str(out_file.relative_to(output))
            rows = todo_findings(rel, ext, text)
            todo_rows.extend(rows)
            findings.extend(rows)
        comments = office_comment_findings(path, rel, ext)
        comment_rows.extend(comments)
        findings.extend(comments)
        manifest.append(
            {
                "path": rel,
                "extension": ext,
                "classification": classification,
                "supported": supported,
                "size_bytes": path.stat().st_size,
                "status": status,
                "method_or_note": note,
                "text_path": text_rel,
            }
        )

    output.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with output.joinpath("todo_findings.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(todo_rows)
    with output.joinpath("comments_findings.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(comment_rows)
    with output.joinpath("review_findings.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(findings)
    write_summary(output, manifest, findings, input_path)
    print(f"Wrote {len(manifest)} file records to {output}")
    print(f"Found {len(findings)} review findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
