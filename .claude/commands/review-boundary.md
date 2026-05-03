Run a boundary review on the current git diff.

Steps:
1. Run `git diff HEAD` to get all modified Python files
2. For each modified file in `app/` or `tests/`, check for:
   - Forbidden imports per layer (`.claude/rules/boundary.md`)
   - `Inconsistencia` or `Update` contract violations (CLAUDE.md CONTRACTS)
   - Hardcoded DB path instead of `app.paths.db_path()`
3. Report as a bulleted list: `[FILE:LINE] rule — fix`

If no violations: output "No boundary violations found."
Maximum output: 300 words.
