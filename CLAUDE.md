# Agent Instructions

## Memory Configuration

At the start of every session, read .memory/project/MEMORY_INDEX.md
to orient yourself. Then read any active entries listed there that
are relevant to the current task.

Before making any significant decision or observing something worth
remembering across sessions, check the index for an existing entry
on the same topic. Update existing entries rather than creating
duplicates.

### Memory layers

- .memory/project/ — Read on startup via MEMORY_INDEX.md. You may
 write new entries here when a significant decision is made or
 project state changes.

- .memory/knowledge/ — Read-only. Consult before making any decision
 that touches coding standards or architectural constraints. Never
 attempt to write to this directory.

- .memory/reference/ — Read-only. Query by keyword for relevant
 excerpts when you need background context. Do not read the entire
 directory.

### Write policy

Before writing a new memory entry, check MEMORY_INDEX.md for an
existing entry on the same topic. Update existing entries rather
than creating new ones. Never write anything classified as
Confidential or Secret to any memory layer.

### Permission denials

If a hook, permission rule, sandbox or file permission denies a
tool call, stop that action. Do not try to reach the same result
another way: no switching tools (e.g. Edit or Write after a Bash
denial), no rewording the command to get past the check, no
writing a copy elsewhere and moving it into place, no git command
that overwrites the file, and no disabling the sandbox. Never edit
.claude/hooks/, .claude/settings*.json or settings.json to weaken
a protection unless a human explicitly asks for that change.

Instead, report in your session output:

- the tool and the command or path that was denied,
- the exact denial message, and
- the change you were trying to make and why.

Then ask a human to act: make the change themselves (give the
exact edit), approve it, or say how to proceed. Carry on with
work that does not depend on the denied action, and mark the
dependent work as blocked.

One exception: if the denied call only reads a path you are
allowed to read (e.g. a hook rejects a read-only loop), you may
retry with a simpler read-only command or the Read tool, and say
in your output that you did. This exception never covers writes.

### Stale memory policy

If a memory entry's review date has passed, flag it in your session
output and ask for human confirmation before acting on it.

### Scope verification

Read SCOPE.md at the root of .memory/ on startup. If it does not
match this project, halt and report the mismatch before doing
anything else.
