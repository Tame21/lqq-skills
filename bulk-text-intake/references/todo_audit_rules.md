# Review Audit Rules

Use this reference when the user asks for Office comments, TODO, FIXME, comment, review-note, remediation, filtering, statistics, or issue cleanup analysis.

## Scope

Count review findings only in primary supported file types:

- `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`
- `.xml`, `.html`, `.md`
- `.java`, `.py`, `.js`

Other extensions may provide context, but do not include them in review statistics unless the user explicitly expands scope.

## Finding Types

The intake script writes:

- `office_comment`: comments extracted from supported OOXML Office files where practical.
- `todo`: TODO-style text markers from supported text and extracted Office content.

For legacy `.doc`, `.ppt`, and `.xls`, comments may require LibreOffice or another converter and should be reported as an extraction limitation when unavailable.

## TODO Tokens

Detect these tokens case-insensitively:

- `TODO`
- `FIXME`
- `HACK`
- `XXX`
- `BUG`
- `REVIEW`
- `OPTIMIZE`

Keep the original line snippet short enough for a CSV cell and a readable report.

## Comment Forms And Fields

Relevant findings may appear in:

- Line comments such as `//`, `#`, and similar source-code conventions.
- Block comments such as `/* ... */`.
- HTML/XML comments such as `<!-- ... -->`.
- Markdown comments and visible Markdown text.
- Extracted Office text containing review-note tokens.

For Office formats, line numbers are extracted-text line numbers, not original document layout coordinates.
For structured Office comments, prefer `author`, `date`, `location`, and `text` from `comments_findings.csv` or `review_findings.csv`.

## Reporting

Report:

- Source path.
- Location or line number when available.
- Token.
- Author or responsible person when available.
- Date or date bucket when available.
- Short snippet or comment text.

When summarizing, group by token, author, date bucket, file type, and likely owner area. Collapse duplicates or near-duplicates before recommending remediation work.
