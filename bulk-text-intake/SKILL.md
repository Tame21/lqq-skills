---
name: bulk-text-intake
description: Use this skill to process large batches of mixed text-bearing files, especially 200+ files containing doc, docx, ppt, pptx, xls, xlsx, xml, java, py, html, md, js, and miscellaneous extensions. It extracts text where practical, classifies files by type and role, organizes outputs, finds TODO/comment-review issues in supported file types, and uses unsupported files only as auxiliary context unless the user asks otherwise.
---

# Bulk Text Intake

## Overview

Use this skill when a user needs a large mixed folder of documents, source files, markup, spreadsheets, or miscellaneous text inputs turned into an organized corpus for review, migration, audit, summarization, or downstream analysis.

Default to a reproducible batch workflow: inventory first, extract next, classify and summarize last. For 200+ files, avoid opening files one by one in chat; use the bundled script and inspect the generated reports.

## Supported Scope

Primary file types for extraction, classification, and TODO/comment-review issue finding:

- Office documents: `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`
- Markup and text-like files: `.xml`, `.html`, `.md`
- Source files: `.java`, `.py`, `.js`

Other extensions may be inventoried and used as auxiliary input, but do not include them in file-type coverage statistics or TODO/comment-review issue counts unless the user explicitly expands scope.

## Batch Workflow

1. Confirm the input root and desired output root. If the user did not specify an output path, create one near the input such as `bulk_text_output/`.
2. Run the bundled script:

```bash
python bulk-text-intake/scripts/bulk_text_intake.py /path/to/input --output /path/to/output
```

3. Review `summary.md`, `manifest.json`, and `todo_findings.csv`.
4. If extraction failures matter, inspect `manifest.json` entries where `status` is not `ok`. For legacy `.doc`, `.ppt`, and `.xls`, install or use available converters such as LibreOffice, `antiword`, or `catdoc` when the environment permits.
5. Use extracted text files under `extracted_text/` for downstream summarization, clustering, deduplication, translation, issue triage, or prompt input.

For reusable user prompts, load `references/prompt_templates.md` and replace the `{{PLACEHOLDERS}}` for the current corpus and desired output.

Load `references/extraction_rules.md` when extraction quality, converter choice, legacy Office files, or rerun strategy matters.

Load `references/todo_audit_rules.md` when the user asks for TODO, FIXME, comment, review-note, remediation, or issue cleanup analysis.

## Output Contract

The script writes:

- `manifest.json`: one record per discovered file, including extension, classification, size, status, extraction method, output text path, and notes.
- `extracted_text/`: normalized UTF-8 `.txt` files for successfully extracted content.
- `todo_findings.csv`: TODO/FIXME/HACK/XXX plus comment-style issue markers from primary supported types only.
- `summary.md`: concise counts by class, type, extraction status, and TODO/comment-review findings.

## Classification Rules

Classify by extension first, then optionally refine by path or content:

- `office_document`: `.doc`, `.docx`
- `office_presentation`: `.ppt`, `.pptx`
- `office_spreadsheet`: `.xls`, `.xlsx`
- `source_code`: `.java`, `.py`, `.js`
- `markup`: `.xml`, `.html`, `.md`
- `auxiliary`: all other extensions

For review reporting, keep auxiliary files separate. They can inform context but should not inflate supported-type counts or TODO/comment-review statistics.

## Working Style

For large corpora, keep user-facing updates high level:

- Report total files discovered and supported vs auxiliary counts.
- Name any extraction gaps by file type and required tool.
- Summarize top issue clusters rather than pasting long file contents.
- Preserve source files; write all derived artifacts to the output directory.
