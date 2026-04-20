---
name: brainstorm
description: >
  Socratic brainstorming protocol. Invoke when user message starts with
  "BRAINSTORM:". Reads CLAUDE.md and PROJECT_STRUCTURE.md, identifies gaps,
  asks critical questions, then outputs a self-contained XML prompt for a
  new Claude Code session. Never executes the task itself.
disable-model-invocation: false
---

## Trigger

Activate when user message starts with `BRAINSTORM:`.
If a prior BRAINSTORM already exists in this conversation, resume from the last state — never restart.

Confirmation keyword: "EXECUTAR"

## STATE 1 — INTAKE

Read silently before responding:
- `CLAUDE.md`
- `PROJECT_STRUCTURE.md`
- Any module source files explicitly mentioned in the trigger description

Extract from the trigger: objective, involved modules (inferred from PROJECT_STRUCTURE.md), missing or ambiguous information.

If the request is fully clear (objective + scope + constraints all inferable from files and trigger), skip STATE 2 and go directly to STATE 3.

## STATE 2 — QUESTIONS

Ask max 5 critical questions. No suggestions. No code. No plan.
Only ask what cannot be inferred from CLAUDE.md, PROJECT_STRUCTURE.md, or the trigger.
Wait for the confirmation keyword before proceeding.

## STATE 3 — EXECUTION

Triggered only by the confirmation keyword. Output one XML prompt block:

    <task>
      <explore>
        [list only files relevant to this task, derived from trigger + PROJECT_STRUCTURE.md]
        Identify conflicts between context below and the codebase.
        List assumptions needed to proceed.
        Ask clarifying questions before producing any plan.
        Do not plan. Do not write code.
      </explore>
      <context>
        <objective>[derived from trigger + user answers]</objective>
        <constraints>[CLAUDE.md invariants + task-specific constraints]</constraints>
        <inputs>[files, data, parameters]</inputs>
        <outputs>[expected deliverables]</outputs>
        <success_criteria>[how to verify the task is complete]</success_criteria>
      </context>
      <plan_gate>
        Produce the plan only after I have answered your questions from the EXPLORE phase.
      </plan_gate>
    </task>

The prompt must be self-contained: a new Claude Code session using only that prompt must complete the task without additional context.

**Language:** The XML prompt block must always be written in English, regardless of the language used in the conversation.

## STATE 4 — PERSISTENCE AND HANDOFF

After producing the XML block, always persist it so the user can retrieve it later:

1. **Save location:**
   - If running under plan mode: the XML block already lives inside the active plan file — use that path.
   - Otherwise: save the XML block to `.claude/brainstorms/<slug>.md` (create the directory if missing). The `<slug>` is derived from the trigger objective (kebab-case, ≤60 chars).

2. **Final message to the user:** the last line of the turn must be a single reference line in this exact format:

   `XML salvo em: <absolute-or-relative-path>`

   This line must appear in every STATE 3 turn and in any later turn where the user asks where the XML is. Never omit it.

## Rules
- Never produce output before the confirmation keyword
- Never restart if context already exists in the conversation
- explore section is always task-specific — never generic boilerplate
- Minimize token usage at every state
- XML output is always in English
- Every STATE 3 turn ends with the `XML salvo em: <path>` reference line
