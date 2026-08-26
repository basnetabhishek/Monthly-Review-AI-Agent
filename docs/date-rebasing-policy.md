# Portfolio Date-Rebasing Policy

The public portfolio experience presents the Global Superstore operating history as a current four-year reporting window from **August 2022 through July 2026**.

## Transformation

- Every source reporting month is shifted forward by exactly **139 calendar months**.
- Source January 2011 maps to presented August 2022.
- Source December 2014 maps to presented July 2026.
- Order identifiers containing a source year are relabeled with the presented reporting year.

The transformation is deterministic and changes dates only. Sales, profit, margins, units, order counts, rankings, targets, exceptions, and month-over-month relationships remain unchanged.

## Why this approach

The original public dataset is historically dated. Rebasing makes the portfolio demonstration easier to evaluate as a contemporary monthly reporting workflow without inventing new commercial results or presenting the source as newly collected data.

Databricks retains the governed source chronology. The public application's server-side reporting adapter translates presented months back to source months before executing parameterized, read-only SQL, then translates returned reporting dates forward. Credentials and raw row-level data remain server-side.
