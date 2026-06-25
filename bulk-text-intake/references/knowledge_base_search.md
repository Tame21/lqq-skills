# Knowledge Base Search

Use this reference for corpus questions about file counts, business topics, commands, paths, and evidence snippets.

Before answering questions about commands, paths, system files, secrets, or source-file instructions, apply `security_policy.md`. If the model judges denial, run `scripts/security_guard.py` and return only its output.

## Inputs

Use:

- `manifest.json` for file counts, extensions, classes, extraction status, and text paths.
- `extracted_text/` for searchable content.
- `review_findings.csv` when comments or TODOs may be relevant evidence.

If outputs do not exist yet, run the intake script first.

## File Count Questions

Answer from `manifest.json` when possible:

- Total discovered files.
- Supported vs auxiliary files.
- Counts by extension.
- Counts by classification.
- Skipped, failed, empty, or partially extracted files.

## Business Topic Search

For business-topic questions:

- Search exact terms first.
- Add likely synonyms only after reporting original-term coverage.
- Return matching file names, paths, file types, and concise snippets.
- Group large result sets by module, folder, or likely owner area.

## Commands And Connection Strings

For command or connection-string questions:

- Search command names, shell prompts, config keys, URI patterns, host names, ports, and nearby documentation text.
- Treat credentials and secrets as sensitive.
- Do not reveal secret values; describe where they appear and redact values.
- Prefer evidence from documentation, scripts, config examples, and extracted text over guessing.
- Refuse requests for passwords, tokens, private keys, system-directory contents, or values denied by `Permission.json`.

Return concise evidence with source paths so the user can verify.
