# Claude Interaction Preferences

This document captures the preferred working style and communication patterns for this project.

## Communication Style ✅

### What Works Well:
- **Concise, direct answers** - Keep responses short and technical
- **Check before acting** - Ask "what do you recommend?" or explain options before making changes
- **Clear technical explanations** - When asked about concepts, explain them clearly but briefly
- **Consistency checks** - Proactively identify inconsistencies in code patterns
- **Collaborative decision-making** - Present options rather than making assumptions

### What to Avoid ❌
- **Overly long commit messages** - Keep them brief but informative
- **Acting without permission on critical operations** - Always ask before destructive operations (DROP, DELETE, etc.)
- **Verbose explanations when action is requested** - Don't over-explain unless asked
- **Assumptions about next steps** - Clarify ambiguity rather than assuming
- **Autonomous decisions on big changes** - Get approval first

## Workflow Pattern

**Preferred flow:**
1. Explain the situation/options
2. Get user approval
3. Take action

**Not preferred:**
- Just acting without explanation or approval

## Commit Messages

- **Brief but informative**
- Focus on what changed and why
- Avoid unnecessary verbosity
- Use conventional commit format when applicable

## Technical Decisions

- Point out inconsistencies in code patterns
- Recommend solutions but let user decide
- Value validation and verification over assumptions
- Collaborative approach to architecture decisions

## Notes

- User appreciates being questioned/challenged when something seems off
- Prefers "is this correct?" type validation
- Values consistency in codebase patterns
