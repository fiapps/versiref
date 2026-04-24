# Security

## Reporting a vulnerability

If you find a security issue in VersiRef, please email the maintainer (address in `pyproject.toml`) rather than filing a public issue. For a project this small, that's the whole disclosure process.

## Supply-chain defenses

VersiRef is a small library with a single runtime dependency (`pyparsing`) and a handful of dev-only tools. Even so, a compromised transitive dependency could land malicious code in a released wheel, so the project runs three overlapping checks against that risk.

### 1. Cooldown on upgrades

When a package maintainer's account is hijacked, the malicious release is typically detected and yanked within hours to a few days. A short quarantine period on new versions turns that class of attack into a near-miss, at the cost of not having the absolute latest release for a week.

Upgrades to dependencies are pinned to versions at least 7 days old, using uv's `--exclude-newer`:

```sh
uv lock --upgrade --exclude-newer "$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ)"
```

**Exception:** if a CVE is announced for a dependency already in the lockfile, upgrade immediately without the cooldown. A known-bad current version is worse than an un-quarantined fixed version.

### 2. pip-audit on the locked dependencies

`pip-audit` (PyPA-maintained) queries the PyPI Advisory Database and OSV for known vulnerabilities in the resolved dependency tree. It's run after any lockfile change and before each release:

```sh
uv export --format requirements-txt --no-emit-project | uvx pip-audit -r /dev/stdin --disable-pip --require-hashes
```

`--disable-pip` skips pip-audit's own venv-creation step (which fails on uv-managed Python); `--require-hashes` makes it trust the pinned-and-hashed list from `uv export`.

This catches *published* CVEs; it does nothing for a fresh compromise that hasn't been reported yet — which is why the cooldown exists.

### 3. GitHub Dependabot alerts

Dependabot provides passive monitoring between manual audits: if a new advisory lands for something in `uv.lock`, GitHub notifies the maintainer. Enable it under **Settings → Code security** in the GitHub repo if it isn't already on. Dependabot's automatic PRs are not used — upgrades go through the cooldown-bound procedure above.

## What these defenses don't cover

- **Malicious code present in a package from the beginning** (typosquats, impostor packages). Mitigation is to keep the dependency list small and only add well-established packages.
- **Vulnerabilities in the uv toolchain or Python itself.** Out of scope for this project; keep `uv` and Python updated through their normal channels.
- **Compromise of the maintainer's PyPI account.** Relevant to downstream users of `versiref`, not to this defense layer. 2FA on the PyPI account is the mitigation.

## Upgrade procedure

1. Run the cooldown-bound `uv lock --upgrade` shown above.
2. Review the diff in `uv.lock`. If anything looks unfamiliar (new transitive dependency, unusual version jump), investigate before committing.
3. Run `pip-audit` and confirm no advisories apply.
4. Run the test suite, type checker, and linter.
5. Commit the lockfile change on its own, with a message noting which packages were upgraded.
