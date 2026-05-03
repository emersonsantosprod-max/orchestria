Load `.claude/skills/strategic-compact/SKILL.md` and compact the current session context.

The skill will guide you to produce a concise session snapshot preserving:
- Active invariants touched this session
- Files modified (relative path + what changed in 5 words)
- Current TODO step and any blocker
- Next step

Output the snapshot to `.claude/sessions/<YYYY-MM-DD>-<topic>.tmp` and update `SESSION_STATE.md`
to point to that file.
