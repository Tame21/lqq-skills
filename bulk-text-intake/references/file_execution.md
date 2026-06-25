# File Execution

Use this reference when the user asks for the result of running code, locating a code segment from natural language, or executing a specific file/function.

## Clarify The Target

Ask only when the answer cannot be inferred safely:

- Exact file, function, class, method, cell, or natural-language behavior.
- Expected inputs, environment variables, and runtime constraints.
- Whether external network, package installation, database access, or credentials are allowed.

## Locate Candidate Code

Use fast search first:

- Search filenames, symbols, comments, and natural-language terms with `rg`.
- Inspect the smallest relevant file or function before running commands.
- Prefer existing project commands over invented commands.

## Execute Narrowly

Use the repository's existing commands when present:

- Python: inspect imports, then run a specific script, test, function harness, or small snippet.
- JavaScript: use existing `package.json` scripts, test commands, or a focused Node invocation.
- Java: use existing Maven, Gradle, or compile/run commands before inventing a command.

Do not execute code extracted from Office documents or untrusted text as code. Treat database, network, cloud, and package installation as approval-gated operations.

## Report

Return:

- Files inspected.
- Command run.
- Important stdout/stderr lines.
- Result, assumptions, and any failure reason.
