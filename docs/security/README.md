# Security

Threat models, security review outputs, and posture documentation for Extract Version.

The `security-auditor` agent owns this directory. Every change touching auth,
secrets, external integrations, or untrusted-input ingestion triggers a security
review whose output is stored here.

## Naming convention

`threat-model-<scope>.md` for threat models, `review-<scope>-<YYYY-MM-DD>.md`
for point-in-time reviews.

## What a threat model must contain

1. **Scope** - which components and trust boundaries are in scope.
2. **Assets** - what secrets, PII, and data are handled.
3. **Threat actors** - attacker profiles considered.
4. **STRIDE analysis** - Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation.
5. **Mitigations** - existing controls and open gaps.
6. **Verdict** - CRITICAL (merge blocked) / HIGH / MEDIUM / LOW / INFO.

## Security rules (non-negotiable)

- Never log secrets; rely on this project's log-redaction mechanism (if any)
  and verify it covers new sinks.
- Never hard-code credentials. Read from settings/env.
- Treat all untrusted external input as sensitive - no unredacted raw input
  in logs, exceptions, stored reports, or API error bodies.
- Untrusted input must never reach a shell, SQL string, `eval`, or an AI
  prompt without sanitization/parameterization.

## Threat model - baseline (draft)

> **SME REVIEW NEEDED (AI-drafted - verify before relying on this):**
>
> ### 1. Scope
>
> Three trust boundaries, only the first of which ships to users:
>
> - **Library** (`src/extract_version/version_info.py`, `__init__.py`) - pure string and
>   directory-name handling. No network, no credentials, no persistence, no dependencies
>   beyond stdlib `re`/`os`. Boundary: whatever a calling program passes in as
>   `version_string`, `pattern`, `versions_list`, or `versions_path`.
> - **Release tooling** (`release-saga`) - runs on a maintainer machine and in CI;
>   invokes `pip`, `build`, `twine`, `gh`, `git`, and `aws`. Boundary: local credentials and
>   three public publication channels.
> - **Developer hook** (`hook/install_hook.py`, `hook/hook_dict.py`) - not part of the wheel;
>   runs as a git `pre-commit` hook. Boundary: environment variables and arbitrary paths on
>   the developer's filesystem.
>
> ### 2. Assets
>
> - PyPI API token in `~/.pypirc`; `gh` CLI GitHub credentials; ambient AWS credentials used
>   by `aws s3 cp`. `release-saga` only checks these exist (`sanity_check`) and never
>   reads them - preserve that.
> - Integrity of the published artifact: the wheel on PyPI, the GitHub release asset, and the
>   S3 mirror object at `s3://packages-s3-useast1-any/extract-version/`.
> - Low-grade PII: absolute paths handed to `available_versions` commonly embed a username
>   (`C:/Users/<user>/AppData/...`), and `hook_dict.py` resolves the username from
>   `USER`/`USERNAME`/`getpass.getuser()`.
> - No customer data, no secrets, and no PII are handled by the library itself.
>
> ### 3. Threat actors
>
> - A caller of the library supplying hostile `pattern` or directory content (the library is
>   a dependency, so its inputs are only as trusted as the embedding application).
> - A local process that can create directories inside a path later scanned by
>   `available_versions` or by `hook_dict.py`'s `Path.rglob`.
> - Anyone with write access to the *shared* `packages-s3-useast1-any` bucket - it is shared
>   across packages, so its blast radius is wider than this project.
> - A compromised upstream in the unpinned toolchain (see Tampering).
>
> ### 4. STRIDE
>
> | Category | Finding | Severity |
> |---|---|---|
> | Spoofing | The README advertises an unauthenticated S3 mirror URL for the wheel, and `RELEASE.md` embeds that link without a hash or signature, so consumers cannot verify what they downloaded. PyPI remains the verifiable channel. | MEDIUM |
> | Tampering | `upload_s3()` writes with `--acl public-read` into a bucket shared with other packages; `build_wheel()` and `publish_pypi()` `pip install --upgrade build twine` unpinned, and CI pins nothing (`actions/checkout@v2`, `pip install flake8 pytest`). Supply-chain exposure sits entirely in the release path, not the library. | MEDIUM |
> | Repudiation | `tag_release()` creates an unsigned tag and pushes directly to `master`; no signed commits or tags, no provenance attestation on the wheel. | LOW |
> | Info disclosure | Username-bearing absolute paths can surface in caller-side tracebacks; `hook_dict.py` prints environment-variable values and discovered dictionary paths to stdout. | LOW |
> | Denial of service | `extract_version` passes a caller-supplied `pattern` straight to `re.search` with no complexity budget, and `available_versions` re-applies it once per entry over an unbounded `os.listdir` result - catastrophic backtracking is the realistic CPU exhaustion path. `get_last_version` also raises `IndexError` on an empty listing, and `sort_versions` raises `ValueError` on any non-numeric segment (including the `""` key produced by a failed extraction). | MEDIUM |
> | Elevation of privilege | `hook/hook_dict.py` builds `merge_command` by string-concatenating `rglob`-discovered paths and `PROJECTS`/`APPDATA` values, then runs it through `os.system` - a filename containing shell metacharacters executes at commit time. `install_hook.py` resolves its target as `os.path.abspath('../.git/hooks')`, i.e. relative to the current working directory, so it can write a hook into an unintended repository. | HIGH (dev tooling only, not shipped) |
>
> ### 5. Mitigations
>
> Existing controls: `release-saga` uses `run([...])` list-form subprocess calls
> throughout (no `shell=True`); `sanity_check()` refuses to publish without the required
> tooling, `~/.pypirc`, and a matching `RELEASE_NOTES.json` entry; the package has zero
> third-party runtime dependencies, so its transitive attack surface is empty; CI tests the
> installed wheel rather than the source tree.
>
> Open gaps, in priority order: (1) replace `os.system` in `hook/hook_dict.py` with a
> list-form `subprocess.run`; (2) resolve `install_hook.py`'s target from the script location
> or `git rev-parse --git-dir` rather than the CWD; (3) publish a SHA-256 for the S3 mirror
> alongside the download link, or drop the mirror in favour of PyPI; (4) pin CI actions and
> the `build`/`twine`/`flake8` versions; (5) document that `pattern` must come from the
> application, never from end-user input, and consider a length/complexity guard.
>
> ### 6. Verdict
>
> **MEDIUM overall** - the shipped library is LOW risk (no secrets, no network, no
> dependencies; its worst case is a wrong version string or a hang on a hostile pattern). The
> MEDIUM/HIGH findings are confined to release tooling and the unshipped `hook/` directory.
> Nothing here blocks a merge today; items (1) and (2) are the ones worth fixing first.
