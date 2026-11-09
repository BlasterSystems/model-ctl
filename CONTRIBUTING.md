# Contributing to modelctl

Thanks for considering a contribution. `modelctl` is a small, focused CLI with
strong atomicity guarantees — read the short rules below before opening a PR.

## Development setup

Python 3.11+ and [`uv`](https://docs.astral.sh/uv/) are required.

```bash
git clone https://github.com/BlasterSystems/model-ctl
cd model-ctl
uv sync --all-extras
uv run --extra test pytest   # full suite; the repo has no CI, this is the gate
```

There is **no CI**: the local suite is the only gate. Run it before every
push — CI will never catch a red suite for you.

## Ground rules

- Standard-library-first style: type annotations, `pathlib.Path`, frozen
  dataclasses, explicit exceptions from `errors.py`. No new dependencies
  unless the standard library and current dependencies are insufficient.
- Keep argument parsing and user-facing output in `cli.py`; filesystem and
  domain behavior belong in the focused modules documented in `AGENTS.md`.
- **Every behavior change needs a test.** Assert observable contracts:
  filesystem layout, symlink targets, journal state, emitted argv/output,
  exception types. Use `tmp_path`, `monkeypatch`, and small fakes — tests
  must not touch the network, a NAS, or real subprocesses.
- **Atomicity and safety invariants are product guarantees**, not
  implementation details. If your change touches download, publish,
  activation, sync, or deletion workflows, include a failure-path test
  proving that partially completed work cannot become active. See
  `AGENTS.md` for the full invariant list.

## Submitting

- Keep changes narrowly scoped; do not rewrite unrelated code.
- Concise, imperative commit subjects following the existing history:
  `feat(scope): ...`, `fix(scope): ...`, `docs: ...`, `chore: ...`.
- PRs are rebased onto `main` (linear history); a `chore(release):` commit
  touching only `src/modelctl/__init__.py` carries version bumps.
- Update `README.md`, `CHANGELOG.md`, and CLI help text together whenever a
  user-visible command or option changes.

## Reporting issues

- Bug reports and feature requests: use the issue templates.
- Security vulnerabilities: do **not** open an issue — see
  [SECURITY.md](SECURITY.md) and use GitHub's private vulnerability reporting.
