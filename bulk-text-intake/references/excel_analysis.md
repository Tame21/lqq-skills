# Excel Analysis

Use this reference for Excel inspection, pivot-style summaries, derived tables, and charts.

## Inspect First

For `.xlsx` files, inspect:

- Sheet names.
- Header rows and table ranges.
- Row counts.
- Likely dimensions and measures.
- Empty, merged, hidden, or formula-heavy areas that may affect confidence.

For legacy `.xls`, use available converters or libraries. If unsupported, record the gap instead of pretending the workbook was fully analyzed.

## Pivot-Style Requests

For pivot-style requests:

1. Identify the source workbook, sheet, and table range.
2. Determine rows, columns, values, and aggregation from the user's words.
3. If the aggregation is unclear, choose count for categories and sum for numeric measures, then state the assumption.
4. Write derived CSV/Markdown summaries to the output directory.
5. Create charts when requested or when they materially help answer the question.
6. Keep the workbook unchanged unless the user asks for an edited workbook copy.

## Output Expectations

Write generated artifacts under the output directory:

- `excel_summary.md` for a human-readable explanation.
- Derived `.csv` files for pivot-style tables.
- Chart images or edited workbook copies only when requested or clearly useful.

When reporting, include the source sheet, fields used, aggregation, filters, and any rows excluded.
