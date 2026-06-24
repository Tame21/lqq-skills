# TODO Audit Rules

Use this reference when the user asks for TODO, FIXME, comment, review-note, remediation, or issue cleanup analysis.

## Scope

Count TODO/comment-review findings only in primary supported file types:

- `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`
- `.xml`, `.html`, `.md`
- `.java`, `.py`, `.js`

Other extensions may provide context, but do not include them in TODO/comment-review statistics unless the user explicitly expands scope.

## Tokens

Detect these tokens case-insensitively:

- `TODO`
- `FIXME`
- `HACK`
- `XXX`
- `BUG`
- `REVIEW`
- `OPTIMIZE`

Keep the original line snippet short enough for a CSV cell and a readable report.

## Comment Forms

Relevant findings may appear in:

- Line comments such as `//`, `#`, and similar source-code conventions.
- Block comments such as `/* ... */`.
- HTML/XML comments such as `<!-- ... -->`.
- Markdown comments and visible Markdown text.
- Extracted Office text containing review-note tokens.

For Office formats, line numbers are extracted-text line numbers, not original document layout coordinates.

## Reporting

Report:

- Source path.
- Line number when available.
- Token.
- Short snippet.

When summarizing, group by token, file type, and likely owner area. Collapse duplicates or near-duplicates before recommending remediation work.
