# Prompt Templates

Copy a template and replace `{{PLACEHOLDERS}}`. Keep `$bulk-text-intake` in the prompt so the skill is explicitly invoked.

## 1. Full Batch Intake

```text
Use $bulk-text-intake to process {{INPUT_DIR}}.

Requirements:
- Output all derived artifacts to {{OUTPUT_DIR}}.
- Extract text from doc, docx, ppt, pptx, xls, xlsx, xml, java, py, html, md, and js files where practical.
- Classify files by type and role.
- Generate summary.md, manifest.json, todo_findings.csv, and extracted_text/.
- Treat other extensions as auxiliary context only. Do not include them in supported file-type counts or TODO/comment-review issue counts.
- Clearly list files that could not be fully extracted and explain what converter or dependency is needed.

After processing, summarize:
- Total files discovered.
- Supported vs auxiliary file counts.
- Counts by file class and extension.
- Extraction failures or partial extractions.
- Top TODO/FIXME/REVIEW issue clusters.
```

## 2. TODO And Comment Audit

```text
Use $bulk-text-intake to audit TODO/comment-review issues in {{INPUT_DIR}} and write outputs to {{OUTPUT_DIR}}.

Scope:
- Include only doc, docx, ppt, pptx, xls, xlsx, xml, java, py, html, md, and js files in TODO/comment-review statistics.
- Use other extensions only as auxiliary context if they help explain the project.
- Detect TODO, FIXME, HACK, XXX, BUG, REVIEW, and OPTIMIZE.

Deliver:
- A CSV issue list with path, line number when available, token, and snippet.
- A short markdown summary grouped by token, file type, and likely owner area.
- A prioritized remediation list with duplicates or near-duplicates collapsed.
```

## 3. File Inventory And Classification

```text
Use $bulk-text-intake to inventory and classify {{INPUT_DIR}}, with outputs in {{OUTPUT_DIR}}.

Do not deeply summarize file contents yet. Focus on:
- File count by extension.
- File count by classification: office_document, office_presentation, office_spreadsheet, source_code, markup, auxiliary.
- Largest files and skipped files.
- Extraction readiness and converter gaps for legacy doc, ppt, and xls files.
- Suggested next steps for deeper extraction or review.
```

## 4. Extracted Corpus For Downstream Analysis

```text
Use $bulk-text-intake to extract a clean text corpus from {{INPUT_DIR}} into {{OUTPUT_DIR}}.

Extraction rules:
- Preserve source files unchanged.
- Normalize extracted text to UTF-8 .txt files under extracted_text/.
- Produce manifest.json mapping every source file to its extracted text path.
- Keep auxiliary files in the manifest, but do not extract or count them as primary supported files unless they are useful text and I explicitly approve expanding scope.

After extraction, tell me which extracted_text files are best inputs for {{DOWNSTREAM_TASK}}, and which files should be excluded because they are empty, duplicate-like, binary, or extraction failed.
```

## 5. Legacy Office Extraction Follow-Up

```text
Use $bulk-text-intake to inspect the previous output folder {{OUTPUT_DIR}}.

Focus on files in manifest.json where status is failed, skipped, empty, or partial, especially legacy .doc, .ppt, and .xls files.

Please:
- List each problematic file with its extension, status, and note.
- Identify which tools would likely improve extraction, such as LibreOffice, antiword, catdoc, or another converter.
- Suggest a safe rerun command after those tools are available.
- Do not modify source files.
```

## 6. Executive Summary From Processed Output

```text
Use $bulk-text-intake outputs from {{OUTPUT_DIR}} to create an executive summary.

Use summary.md, manifest.json, todo_findings.csv, and extracted_text/ as inputs.

Summarize:
- What kinds of files are present.
- Main themes or modules represented by the extracted content.
- Important TODO/comment-review issues.
- Extraction limitations that may affect confidence.
- Recommended next actions.

Keep the summary suitable for {{AUDIENCE}}, with emphasis on {{FOCUS_AREA}}.
```

## Placeholder Reference

- `{{INPUT_DIR}}`: directory or file to process.
- `{{OUTPUT_DIR}}`: destination for generated artifacts.
- `{{DOWNSTREAM_TASK}}`: later use, such as summarization, migration, compliance review, translation, or code audit.
- `{{AUDIENCE}}`: target reader, such as engineering lead, project manager, auditor, or client.
- `{{FOCUS_AREA}}`: priority lens, such as risk, TODO cleanup, architecture, documentation coverage, or data migration.
