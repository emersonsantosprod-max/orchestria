---
name: strategic-compact
description: Compact the session context preserving invariants, modified files, current TODO, and next step.
---

# Strategic Compact

Use when the context is growing too large or before ending a session.

## Steps

1. **Identify active invariants:** Which CLAUDE.md invariants were exercised this session? Mark ✓ or ✗ + one-line note.
2. **Collect modified files:** `git diff --name-only HEAD` or list from memory. For each: `path (what changed in 5 words)`.
3. **Current TODO:** Which step is in-progress? Any blocker?
4. **Next step:** What is the immediate next action?

## Output format

Write to `.claude/sessions/YYYY-MM-DD-<topic>.tmp`:

```
## Last Completed Step
<step name> — <files, comma-separated>
Test count: N passed, 0 failed | Lint: clean

## Next Step
<step name> — <files in scope>
Blocker: <one line or "none">

## Invariants Exercised
- <name>: ✓/✗ <note>

## Files Modified
- <relative path> (<5-word summary>)
```

Then update `SESSION_STATE.md` (project root `.claude/SESSION_STATE.md`) with:
```
Plan: <path/to/plan.md or "none">
State: .claude/sessions/YYYY-MM-DD-<topic>.tmp
```

## Constraints

- Max 3 lines per field.
- Do not copy ruleset text into the snapshot — reference file paths.
- Do not include full test output — pass/fail count only.
