# Contributing

Thanks for helping. This repo is a skill collection: the "code" is mostly instructions an agent follows, so changes are judged by whether an agent following them gets the right result.

## Most useful contributions

1. **A run report**: what you archived (builder, theme, host, OS), what worked, and which gotcha/phase was wrong or missing. Open an issue with the template below.
2. **A builder adapter** for a page builder other than Elementor — copy [`skills/wp-archiver/builders/_template.md`](skills/wp-archiver/builders/_template.md) and fill in only what you observed.
3. **macOS / Linux fixes** to the toolkit (it was written on Windows + Git Bash).
4. **New gotchas**, with symptom → cause → fix, in the right area of [`reference/gotchas.md`](skills/wp-archiver/reference/gotchas.md).

## Run report template

```
Site: <anonymised: page count, builder + version, WordPress version, host type>
Environment: <OS, Docker version, agent used>
Phases completed: <00–10>
Worked as written: <…>
Wrong or missing: <phase file / gotcha ID / script, with the symptom>
Fix proposed: <…>
```

## Ground rules

- **No real site data, ever**: no real domains, hostnames, table prefixes, dumps, logs, screenshots or credentials in commits, issues or PRs. Use `example.site` style placeholders. If a run report would identify a site, anonymise it.
- **Stable gotcha IDs**: never renumber; new entries go at the end of their area and are cited from the phase that uses them.
- **One source of truth**: a fact lives in one file and is pointed to from elsewhere. Phase files stay short and end on a checkable exit criterion.
- **Scripts read `.env`**, not hard-coded site values. Keep them idempotent and dry-run-first for anything destructive.
- **Say what is unverified.** Mark untested paths as untested rather than writing them as fact.
- Run `python tools/check-docs.py` before opening a PR; it checks links, gotcha IDs, script names and syntax.
- Disclose AI assistance in the PR description (it is welcome; undisclosed is not). Keep the `Co-Authored-By` trailer on agent-assisted commits.

## Security

Do not open a public issue for something that exposes secrets or could cause data loss (for example a script path that could delete the wrong folder). Use GitHub's private vulnerability reporting for the repository instead.
