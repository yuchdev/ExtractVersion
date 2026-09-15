# Junie porting status

## Claude kit import

- The manifest-listed Claude source files were not present in this checkout when this porting task ran.
- No `.junie/agents`, `.junie/skills`, or `.junie/commands` files were generated, because the porting rules require reading each Claude-authored source before re-authoring an equivalent.
- Hook behavior was not ported or re-expressed, because the corresponding `.claude/hooks/*.py` sources were also unavailable.

## Required follow-up

- Restore the manifest-listed `.claude/agents`, `.claude/hooks`, `.claude/loops`, and `.claude/skills` sources, then rerun this porting step.
- Until those sources are available, any filename-based recreation would be speculative and intentionally avoided.