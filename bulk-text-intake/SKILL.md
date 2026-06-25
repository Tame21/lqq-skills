---
name: bulk-text-intake
description: Use this skill to answer questions and execute tasks over large mixed file sets, especially 200+ files containing doc, docx, ppt, pptx, xls, xlsx, xml, java, py, html, md, js, and miscellaneous extensions. It inventories and extracts text, finds Office comments and code TODOs, supports filtering and statistics by author/date/type/path, helps modify files according to review comments into an output directory, runs or inspects code snippets safely, creates Excel-derived analyses such as pivot-style summaries, and manages knowledge-base questions about file counts, business topics, paths, and discovered commands.
---

# Bulk Text Intake

## Overview

Use this skill when a user needs a large mixed folder of documents, source files, markup, spreadsheets, or miscellaneous text inputs turned into an organized corpus for search, audit, execution, modification, summarization, or downstream analysis.

Default to a reproducible workflow: clarify the target result, inventory and extract, search or execute with narrow scope, then write derived artifacts to an output directory. For 200+ files, avoid opening files one by one in chat; use the bundled script and inspect the generated reports.

## Task Families

Support these common workflows:

- `annotation_management`: collect Office comments from Word/Excel/PowerPoint and TODO-style findings from code or text, then count, filter, group, triage, or use them to drive document fixes.
- `file_execution`: run or inspect a specific code file, function, or naturally described code segment.
- `excel_analysis`: inspect Excel files, summarize tables, and create pivot-style outputs or charts when requested.
- `knowledge_base_management`: answer corpus questions such as file counts by type, files related to a business topic, where a term appears, what commands or connection strings are documented, and which paths contain relevant evidence.

## Clarify Before Running

Ask only for missing information that changes the result:

- Input root or prior output folder.
- Desired output root when generated artifacts or modified files are needed.
- Task family and target: comments/TODOs, code execution, Excel analysis, or corpus search.
- Filters: file type, path prefix, keyword/business topic, author/responsible person, date range, status, or token.
- For fixes: whether to modify copies only, expected output format, and whether each comment should be applied automatically or listed for review.
- For code execution: exact file/function when known, runtime command or dependency constraints when not inferable, and acceptable sandbox/network behavior.

## Supported Scope

Primary file types for extraction, classification, comment/TODO review, and knowledge-base indexing:

- Office documents: `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`
- Markup and text-like files: `.xml`, `.html`, `.md`
- Source files: `.java`, `.py`, `.js`

Other extensions may be inventoried and used as auxiliary input, but do not include them in primary coverage statistics or review issue counts unless the user explicitly expands scope.

## Batch Workflow

1. Confirm the input root and desired output root. If the user did not specify an output path, create one near the input such as `bulk_text_output/`.
2. Run the bundled script:

```bash
python bulk-text-intake/scripts/bulk_text_intake.py /path/to/input --output /path/to/output
```

3. Review `summary.md`, `manifest.json`, `review_findings.csv`, `comments_findings.csv`, and `todo_findings.csv`.
4. If extraction failures matter, inspect `manifest.json` entries where `status` is not `ok`. For legacy `.doc`, `.ppt`, and `.xls`, install or use available converters such as LibreOffice, `antiword`, or `catdoc` when the environment permits.
5. Use extracted text files under `extracted_text/` for downstream summarization, clustering, deduplication, translation, issue triage, or prompt input.
6. For search or knowledge-base questions, use `manifest.json` for file metadata and `extracted_text/` plus `review_findings.csv` for evidence. Return file paths and concise snippets.
7. For fix tasks, preserve source files and write modified copies under the requested output directory. Keep a change log mapping source path, output path, comment/TODO, and action taken.
8. For code execution, prefer the repository's existing test or run command. If the user only gives a natural-language description, locate candidate files with `rg`, inspect the smallest relevant code region, then execute only the command needed to answer.
9. For Excel pivot-style tasks, inspect workbook sheets, identify headers and measures, then create derived CSV/Markdown summaries or charts in the output directory. Do not overwrite the workbook unless explicitly asked.

For reusable user prompts, load `references/prompt_templates.md` and replace the `{{PLACEHOLDERS}}` for the current corpus and desired output.

Load `references/extraction_rules.md` when extraction quality, converter choice, legacy Office files, or rerun strategy matters.

Load `references/todo_audit_rules.md` when the user asks for TODO, FIXME, comment, review-note, remediation, or issue cleanup analysis.

Load only the reference needed for the current task:

- `references/annotation_management.md`: Office comments, code TODOs, filtering, statistics, triage, or comment-driven fixes.
- `references/file_execution.md`: running code, locating code from natural language, or reporting execution results.
- `references/excel_analysis.md`: Excel sheet inspection, pivot-style summaries, derived tables, or charts.
- `references/knowledge_base_search.md`: file counts, business-topic search, command discovery, path questions, or evidence snippets.

## Output Contract

The script writes:

- `manifest.json`: one record per discovered file, including extension, classification, size, status, extraction method, output text path, and notes.
- `extracted_text/`: normalized UTF-8 `.txt` files for successfully extracted content.
- `review_findings.csv`: combined structured review findings for Office comments and TODO-style items.
- `comments_findings.csv`: Office comment rows extracted from supported OOXML files where practical.
- `todo_findings.csv`: TODO/FIXME/HACK/XXX/BUG/REVIEW/OPTIMIZE rows from primary supported files.
- `summary.md`: concise counts by class, type, extraction status, review finding type, and comment author when available.

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
- Summarize top issue clusters and search evidence rather than pasting long file contents.
- Show filters applied before reporting statistics.
- Include exact source paths and output paths for anything executed or modified.
- Preserve source files; write all derived artifacts to the output directory.
