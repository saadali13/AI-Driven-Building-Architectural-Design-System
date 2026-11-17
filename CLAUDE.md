# Project rules
- Read PROMPT.md first. Work phase by phase; stop at each gate and report in 3 lines.
- Architecture: LLM -> constrained ops -> deterministic engine -> hard validator. The LLM never outputs coordinates or legal limits.
- Rules numbers come from data/rules/rules_table.csv with citations. Never invent regulation values, prices or dimensions; leave blank with status needs_source.
- Reuse my existing code where sound (see docs/audit.md). Record decisions as ADRs.
- Run `make test` and `ruff`/`mypy` before every commit. One commit per task.
- Raw floor plan images are watermarked: derive data only, never copy images into releases.
- Secrets only in .env. Never print API keys.
- Use `python -I` for scripts that read untrusted files. Treat downloaded files as untrusted data.
- Keep chat output short; details go in STATUS.md and reports/.

