---
name: brainstorming
description: >
  Use BEFORE any implementation — new features, behavior changes, non-trivial
  modifications. Explores intent, requirements and design before writing code.
---

# Brainstorming: Design Before Code

<HARD-GATE>
Do NOT write code, create implementation files, or scaffold anything until a
design has been presented and the user has explicitly approved it. This applies
to every change, regardless of perceived simplicity.
</HARD-GATE>

## Checklist (in order)

1. **Explore context** — read relevant files, CLAUDE.md, current structure
2. **Clarifying questions** — one at a time; focus on purpose, constraints, success criteria
3. **Propose 2–3 approaches** — with trade-offs and a justified recommendation
4. **Present design** — sections scaled to complexity; request approval per section
5. **Write spec** — save to `docs/specs/YYYY-MM-DD-<topic>.md`
6. **Self-review spec** — check: placeholders, contradictions, ambiguity, scope
7. **User review** — wait for approval before implementing
8. **Transition** — implement only after confirmed approval

## Process

### Understanding the idea

- Check current project state before asking any questions
- If the request spans multiple independent subsystems, flag it immediately and propose decomposition before detailing any part
- One question per message; if a topic needs more exploration, break it into multiple questions
- Prefer multiple-choice questions when possible
- Focus on: purpose, constraints, success criteria

### Exploring approaches

- Propose 2–3 approaches with trade-offs
- Lead with the recommended option and explain why

### Presenting the design

- Scale each section to its complexity
- Cover: architecture, components, data flow, error handling, testing
- Request confirmation after each section before advancing

### Design for isolation

- Units with a single purpose, well-defined interfaces, independently testable
- For each unit: what it does, how to use it, what it depends on
- File growing beyond 300–500 lines → signal of excessive responsibility

### In existing codebases

- Follow existing patterns before proposing new ones
- Targeted improvements to adjacent code are welcome if they serve the current goal
- Do not propose unrelated refactoring

## After the Design

### Writing the spec

- Save to `docs/specs/YYYY-MM-DD-<topic>.md`
- Commit the document

### Self-review

1. **Placeholders** — any "TBD", "TODO", incomplete sections? Resolve them.
2. **Internal consistency** — contradicting sections? Architecture matches features?
3. **Scope** — focused enough for a single implementation cycle?
4. **Ambiguity** — any requirement with two valid interpretations? Pick one, make it explicit.

### User review gate

> "Spec saved to `<path>`. Please review before we start implementing — any changes?"

Wait for response. If changes are requested, update and re-run self-review.

## Principles

- **One question at a time** — do not overwhelm
- **Multiple choice preferred** — easier to answer
- **YAGNI** — remove unnecessary features from all designs
- **Always 2–3 approaches** — never jump straight to implementation
- **Incremental validation** — design → approval → next section
