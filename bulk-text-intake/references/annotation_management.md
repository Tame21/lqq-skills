# Annotation Management

Use this reference for Office comments, code TODOs, review statistics, filtering, triage, and comment-driven fixes.

## Source Artifacts

Start from `review_findings.csv` when available. If it does not exist, run the intake script first.

Use:

- `review_findings.csv` for combined Office comments and TODO-style findings.
- `comments_findings.csv` for Office comments only.
- `todo_findings.csv` for TODO/FIXME/HACK/XXX/BUG/REVIEW/OPTIMIZE rows only.
- `manifest.json` to map findings back to file class, extension, extraction status, and text path.

## Filters

Apply requested filters before reporting counts or fixes:

- `kind`: `office_comment` or `todo`
- `extension`: `.docx`, `.pptx`, `.xlsx`, `.java`, `.py`, `.js`, `.xml`, `.html`, `.md`
- `author`: Office comment author or responsible person named in text
- `date`: Office comment timestamp when present
- `token`: `COMMENT`, `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `REVIEW`, `OPTIMIZE`
- `path`: file path, module, folder, or business area

For statistics, report the filters first, then counts by author, date bucket, extension, token, and path prefix.

## Comment-Driven Fixes

When asked to fix files according to comments or TODOs:

1. Preserve all source files.
2. Write modified copies to the requested output directory.
3. Apply only changes directly supported by the comment/TODO and surrounding content.
4. If a comment is ambiguous, add it to a review list instead of guessing.
5. Produce a change log with source path, output path, finding location, action, and confidence.

For Office files, prefer editing copies. If the requested edit requires preserving complex formatting, comments, tracked changes, formulas, or slide layout and the available libraries cannot do that safely, report the limitation and produce an actionable review list instead of corrupting the file.
