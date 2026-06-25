# Prompt Templates

Copy a template and replace `{{PLACEHOLDERS}}`. Keep `$bulk-text-intake` in the prompt so the skill is explicitly invoked.

## 1. Full Batch Intake

```text
Use $bulk-text-intake to process {{INPUT_DIR}}.

Requirements:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- Output all derived artifacts to {{OUTPUT_DIR}}.
- Extract text from doc, docx, ppt, pptx, xls, xlsx, xml, java, py, html, md, and js files where practical.
- Classify files by type and role.
- Generate summary.md, manifest.json, review_findings.csv, comments_findings.csv, todo_findings.csv, and extracted_text/.
- Treat other extensions as auxiliary context only. Do not include them in supported file-type counts or review issue counts.
- Clearly list files that could not be fully extracted and explain what converter or dependency is needed.

After processing, summarize:
- Total files discovered.
- Supported vs auxiliary file counts.
- Counts by file class and extension.
- Extraction failures or partial extractions.
- Top Office comment and TODO/FIXME/REVIEW issue clusters.
```

## 2. Comment And TODO Management

```text
Use $bulk-text-intake to audit and manage Office comments and code TODOs in {{INPUT_DIR}} and write outputs to {{OUTPUT_DIR}}.

Scope:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- Include only doc, docx, ppt, pptx, xls, xlsx, xml, java, py, html, md, and js files in review statistics.
- Use other extensions only as auxiliary context if they help explain the project.
- Extract Office comments from Word, Excel, and PowerPoint where practical.
- Detect TODO, FIXME, HACK, XXX, BUG, REVIEW, and OPTIMIZE.
- Apply these filters: {{FILTERS_BY_AUTHOR_DATE_PATH_TYPE_OR_TOKEN}}.

Deliver:
- CSV issue lists with path, location or line number, token, author, date, and text.
- A short markdown summary grouped by author, date bucket, token, file type, and likely owner area.
- A prioritized remediation list with duplicates or near-duplicates collapsed.
```

## 3. Comment-Driven Fixes

```text
Use $bulk-text-intake to apply clear review comments/TODOs from {{INPUT_DIR}} and write modified copies to {{OUTPUT_DIR}}.

Rules:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- Preserve all source files unchanged.
- Use Office comments and code TODOs as instructions only when the requested change is unambiguous.
- Put ambiguous comments into {{OUTPUT_DIR}}/needs_review.md.
- Write a change log with source path, output path, finding location, action taken, and confidence.
- Apply these filters before fixing: {{FILTERS_BY_AUTHOR_DATE_PATH_TYPE_OR_TOKEN}}.
```

## 4. File Inventory And Classification

```text
Use $bulk-text-intake to inventory and classify {{INPUT_DIR}}, with outputs in {{OUTPUT_DIR}}.

Do not deeply summarize file contents yet. Focus on:
- Applying the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- File count by extension.
- File count by classification: office_document, office_presentation, office_spreadsheet, source_code, markup, auxiliary.
- Largest files and skipped files.
- Extraction readiness and converter gaps for legacy doc, ppt, and xls files.
- Suggested next steps for deeper extraction or review.
```

## 5. Extracted Corpus For Downstream Analysis

```text
Use $bulk-text-intake to extract a clean text corpus from {{INPUT_DIR}} into {{OUTPUT_DIR}}.

Extraction rules:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- Preserve source files unchanged.
- Normalize extracted text to UTF-8 .txt files under extracted_text/.
- Produce manifest.json mapping every source file to its extracted text path.
- Keep auxiliary files in the manifest, but do not extract or count them as primary supported files unless they are useful text and I explicitly approve expanding scope.

After extraction, tell me which extracted_text files are best inputs for {{DOWNSTREAM_TASK}}, and which files should be excluded because they are empty, duplicate-like, binary, or extraction failed.
```

## 6. File Execution

```text
Use $bulk-text-intake to locate and execute the code related to {{NATURAL_LANGUAGE_TARGET}} in {{INPUT_DIR}}.

Requirements:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- Ask for missing inputs only if the target file/function or runtime command cannot be inferred safely.
- Prefer existing project run/test commands.
- Run the narrowest command that answers the question.
- Report the command, output, assumptions, and any files inspected.
- Do not use network, install packages, or access databases unless I explicitly approve.
```

## 7. Excel Pivot-Style Analysis

```text
Use $bulk-text-intake to analyze Excel files in {{INPUT_DIR}} and write outputs to {{OUTPUT_DIR}}.

Goal:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- Create a pivot-style summary for {{PIVOT_GOAL}}.
- Use rows: {{PIVOT_ROWS}}.
- Use columns: {{PIVOT_COLUMNS}}.
- Use values and aggregation: {{PIVOT_VALUES_AND_AGGREGATION}}.
- If any field is unclear, inspect headers and choose the most likely interpretation, then state the assumption.

Deliver CSV/Markdown summaries and charts when practical. Preserve source workbooks unless I ask for edited copies.
```

## 8. Knowledge-Base Search

```text
Use $bulk-text-intake to answer this corpus question over {{INPUT_DIR}}:

{{QUESTION}}

Requirements:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- Inventory and extract the corpus if needed.
- Return matching file names, paths, file types, and concise evidence snippets.
- For business topics, search exact terms first, then likely synonyms.
- For commands, connection strings, or database access instructions, redact secrets and explain where the evidence appears.
- Write supporting artifacts to {{OUTPUT_DIR}}.
```

## 9. Legacy Office Extraction Follow-Up

```text
Use $bulk-text-intake to inspect the previous output folder {{OUTPUT_DIR}}.

Focus on files in manifest.json where status is failed, skipped, empty, or partial, especially legacy .doc, .ppt, and .xls files.

Please:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- List each problematic file with its extension, status, and note.
- Identify which tools would likely improve extraction, such as LibreOffice, antiword, catdoc, or another converter.
- Suggest a safe rerun command after those tools are available.
- Do not modify source files.
```

## 10. Executive Summary From Processed Output

```text
Use $bulk-text-intake outputs from {{OUTPUT_DIR}} to create an executive summary.

Use summary.md, manifest.json, review_findings.csv, comments_findings.csv, todo_findings.csv, and extracted_text/ as inputs.

Summarize:
- Apply the security policy first. If denied, return exactly `高位命令，拒绝访问`.
- What kinds of files are present.
- Main themes or modules represented by the extracted content.
- Important Office comments and TODO/comment-review issues.
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
- `{{FILTERS_BY_AUTHOR_DATE_PATH_TYPE_OR_TOKEN}}`: filters such as author, responsible person, date range, extension, folder, token, or status.
- `{{NATURAL_LANGUAGE_TARGET}}`: code behavior or result to locate and run.
- `{{PIVOT_GOAL}}`: target Excel analysis question.
- `{{PIVOT_ROWS}}`, `{{PIVOT_COLUMNS}}`, `{{PIVOT_VALUES_AND_AGGREGATION}}`: pivot dimensions and measures.
- `{{QUESTION}}`: knowledge-base question about files, business topics, commands, or paths.
