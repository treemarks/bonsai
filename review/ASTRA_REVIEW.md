**FINDINGS**

Reviewed the requested working-tree files on Python 3.9.6. They changed concurrently during the review, so the final reproducible baseline is commit `b1e50c5a9abe184fc597b84b4bc67faed0887981`: `bonsai` (1,253 lines), `tests/test_bonsai.py` (222 lines), and `README.md` (229 lines). Its 19 existing tests pass. The added 51 test methods produce 45 failing/erroring methods and six passing holds methods; individual subtests produce additional reported failures. No actual credentials were read, no provider usage endpoints were called, and no model job was started. CLI help was checked with temporary homes. All line references below target this immutable baseline, not subsequent working-tree edits or the proposed patches. The baseline `bonsai` SHA-256 is `fd679f6c356b560c7892ae761a9a593090a304b5b40d31af4fdf5397851adc36`.

The executable regression code is [test_astra_regressions.py](test_astra_regressions.py). Its numbered test names map to the findings. These are acceptance tests for the proposed behavior; failures against the current program are intentional. The `test_holds_*` cases protect behavior that survived review. Patches below are review proposals, not changes applied to `bonsai`. Shared helpers are intended to be defined once.

Reproduce the pinned run without changing the working tree:

```sh
audit_snapshot=$(mktemp -d)
git archive b1e50c5a9abe184fc597b84b4bc67faed0887981 | tar -x -C "$audit_snapshot"
/usr/bin/python3 -m unittest discover -s "$audit_snapshot/tests"
BONSAI_REVIEW_SOURCE="$audit_snapshot/bonsai" /usr/bin/python3 -m unittest discover -s review -p test_astra_regressions.py -v
```

Concurrent-edit note: after the baseline was committed, observed edits added institution notices and changed Claude usage probing toward `claude auth status` with usage reads off by default. Those edits change the applicability of the baseline's Claude opt-out description, but do not by themselves repair inherited environment routing, provider-shared classification, sensitive named routing, redirect handling, file modes, or parser/ledger races. The in-progress working tree continued changing; this report is not a sign-off on that later version. The test harness also blocks newly introduced `claude_status` calls by default so running it against a changing tree cannot unexpectedly access real credentials.

**1. The chosen directory does not select the effective authentication or destination. Sure.**

`child_env`, `bonsai:554–556`:

```python
env = {k: v for k, v in os.environ.items()
       if k not in ("CLAUDECODE", "CLAUDE_CONFIG_DIR", "CODEX_HOME", "CLAUDE_CODE_ENTRYPOINT")}
```

Trigger: launch from an environment containing `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, or `CODEX_API_KEY`. Those variables survive unchanged. A selected Stanford directory can therefore run with the parent's credential or a different endpoint. `CLAUDE_CODE_OAUTH_TOKEN` explicitly outranks Keychain credentials. `CODEX_API_KEY` supports a per-invocation credential override for `codex exec`. This is a billing and data-destination defect, not merely a nested-session inconvenience. [Claude environment reference](https://code.claude.com/docs/en/env-vars), [Codex automation authentication](https://learn.chatgpt.com/docs/non-interactive-mode#authenticate-in-automation).

Other surviving controls include `OPENAI_API_KEY`, provider base URLs, `CLAUDE_CODE_USE_BEDROCK`/`USE_VERTEX`/`USE_FOUNDRY`, session-token/file-descriptor variants, `CODEX_THREAD_ID`, telemetry endpoints, and shell startup controls such as `BASH_ENV`. Their exact consequences vary by CLI version; their inheritance is certain. A growing blacklist cannot substantiate “never the parent's login.”

Replacement `child_env` for this login-only wrapper:

```python
def child_env(provider, pool):
    keep = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "TMP", "TEMP",
            "LANG", "LC_ALL", "LC_CTYPE", "TERM", "COLORTERM", "TZ",
            "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "USERPROFILE",
            "APPDATA", "LOCALAPPDATA"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    env["CLAUDE_CONFIG_DIR" if provider == "claude" else "CODEX_HOME"] = pool_dir(provider, pool)
    env["BONSAI_POOL"] = pool
    return env
```

This closes inherited-variable overrides, not settings-file overrides. The chosen CLI can still load authentication helpers, gateways, hooks, MCP servers and policies from its own configuration. Do not claim configuration-directory selection verifies identity. For supported Codex versions, pin the built-in provider and ChatGPT authentication with `-c 'model_provider="openai"' -c 'forced_login_method="chatgpt"'`; institution setups should also pin the expected `forced_chatgpt_workspace_id`. Record and check the actual workspace, not the pool's filename. A user-level provider configuration can change connection behavior. [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-reference), [login/workspace enforcement](https://learn.chatgpt.com/docs/auth#enforce-a-login-method-or-workspace).

Tests: `test_01_child_drops_auth_and_endpoint_overrides`; the test checks inheritance, not an actual billed request.

**2. `run` can select one provider and execute the other under its default login. Sure.**

`cmd_run`, `bonsai:944`:

```python
provider = a.provider or ("codex" if os.path.basename(cmdv[0]) == "codex" else "claude")
```

Trigger: `bonsai run --provider codex --pool stanford -- claude -p 'student records'`. Bonsai selects a Codex seat, sets `CODEX_HOME`, removes `CLAUDE_CONFIG_DIR`, and starts Claude. Claude uses its default directory or another surviving auth override. Likewise, `bonsai run --pool stanford -- python3 wrapper.py` silently assumes Claude even if the wrapper launches Codex. On Windows `codex.exe` is also misclassified. `bonsai run --` passes the first check and raises `IndexError` at `cmdv[0]`.

Replace the provider inference block:

```python
if not cmdv:
    raise SystemExit("bonsai run: give a command after --")
base = os.path.basename(cmdv[0]).lower()
direct = {"claude": "claude", "claude.exe": "claude", "claude.cmd": "claude",
          "codex": "codex", "codex.exe": "codex", "codex.cmd": "codex"}.get(base)
if direct and a.provider and direct != a.provider:
    raise SystemExit("bonsai run: --provider conflicts with the executable")
provider = a.provider or direct
if provider is None:
    raise SystemExit("bonsai run: wrappers require an explicit --provider")
```

A wrapper can still override its environment intentionally. Patch the README claim for `run` to: “Bonsai sets the selected provider's configuration directory. Arbitrary commands and wrappers must honor it; Bonsai does not sandbox them or verify their downstream login.”

Tests: `test_02_*`.

**3. Institution classification leaks across providers, and failed login changes classification. Sure.**

`is_institution`, `bonsai:306`, and `cmd_login`, `bonsai:910–923`:

```python
return bool(((cfg.get("logins") or {}).get(pool) or {}).get("institution"))
entry = logins.setdefault(pool, {})
...
save_config(cfg)
...
return subprocess.call(argv, env=child_env(provider, pool))
```

Trigger: a personal Claude pool and an institution Codex pool share an email. `login email --codex --institution` labels both institution seats. Sensitive Claude work now routes to the personal Claude account. Also, marking an existing personal pool institution happens before login; canceling the browser or receiving a nonzero CLI exit leaves the old credential newly marked institution. `--email` is only a hint to Claude's login flow, and Codex receives no email constraint at all.

Patch classification to be provider-specific, and commit config only after successful login. Exact replacement schema and call sites:

```python
# is_institution; pass provider at all three existing call sites (449, 471, 894).
def is_institution(cfg, pool, provider):
    entry = (cfg.get("logins") or {}).get(pool) or {}
    return entry.get("institutions", {}).get(provider) is True

# cmd_login: build argv first; run before modifying cfg or writing config.
code = subprocess.call(argv, env=child_env(provider, pool))
if code != 0:
    return code
entry = cfg.setdefault("logins", {}).setdefault(pool, {})
entry.setdefault("institutions", {})[provider] = bool(a.institution)
if a.name:
    entry["name"] = a.name
elif not entry.get("name"):
    entry["name"] = login_name(cfg, pool)
save_config(cfg)
return 0
```

During migration, reject legacy `institution: true` entries with a static error asking users to classify each provider; silently treating those entries as personal would create another routing error. Successful browser login alone still cannot prove institutional entitlement. Store/validate the actual account and workspace identity before advertising that stronger guarantee. A user-entered email or “edu” label is not proof of a contract.

Tests: `test_03_*`.

**4. Naming a personal target bypasses an explicit sensitive constraint. Sure; documented behavior contradicts the privacy promise.**

`pick`, `bonsai:531–542`: the named branch returns `r` without testing `kind`. `route`'s checks are never called.

Trigger: `bonsai job personal-codex --kind sensitive -f records.csv`; equivalently `job astra --kind sensitive --pool personal`. The selected row is personal. README:111–114 simultaneously promises sensitive material never reaches personal accounts and says names override both kinds.

Patch immediately before the named `return r`:

```python
if kind == "sensitive" and not r.get("institution"):
    raise SystemExit("bonsai: sensitive work requires an institution login")
```

Replace README:114 with: “A named target chooses that seat instead of auto routing. `--kind sensitive` still requires an institution seat.” Naming an institution seat for general work is an explicit choice and is consistent with the requested behavior; retain that exception and qualify “never carries everyday work” as an **auto-routing** rule. Rejecting personal+sensitive is a deliberate policy correction, not a claim the existing implementation differs from its documented override.

Test: `test_04_sensitive_named_personal_is_rejected`.

**5. The sandbox sentence promises isolation the flags do not provide. Sure.**

`headless_argv`, `bonsai:1012–1018`:

```python
"-s", "read-only"
"--permission-mode", "dontAsk"
```

README:132–134: “so a job can read what you give it and nothing else can happen on your machine without you”.

`dontAsk` denies actions that would prompt; it still permits actions needing no permission and previously allowed tools. In particular an existing allow rule can permit a file write or network fetch, and configured hooks have their own execution path. It is not a read-only sandbox. [Claude permissions](https://code.claude.com/docs/en/permissions#permission-modes).

Codex's read-only command sandbox restricts writes and normally command networking. `-C` selects the working directory, not a file-read allowlist. Readable paths outside it may be accessible under the effective policy. Hosted search, MCP/apps, inference/auth traffic and CLI session/output writes are separate from sandboxed shell networking. [Codex sandbox and network boundaries](https://learn.chatgpt.com/docs/agent-approvals-security).

Exact README replacement for the **current flags**:

> Jobs run the installed CLIs with the selected configuration directory. Codex is requested to use its read-only command sandbox; this does not restrict all file reads to `--cd` or disable hosted search and configured integrations. Claude uses `dontAsk`, which denies actions requiring a new permission prompt but permits already allowed actions. These flags do not limit a job to the files passed with `-f`. CLI settings, hooks, integrations, session logs, and requested output files remain relevant.

For a stricter Claude text-only pass, add `--tools "" --disallowedTools 'mcp__*' --strict-mcp-config --mcp-config '{"mcpServers":{}}' --setting-sources '' --no-session-persistence`, and disable hooks with `--settings '{"disableAllHooks":true}'` where supported. `--tools ""` alone does not remove MCP tools. Verify support against the installed version and retain managed policy. This is capability reduction, not a proof that the CLI itself performs no other reads or writes. Do not substitute `--bare`: current help says it skips OAuth/Keychain auth. [Claude CLI flags](https://code.claude.com/docs/en/cli-reference).

Test: `test_05_readme_does_not_promise_file_allowlisting`. This guards the false claim; a flag-membership assertion cannot test sandbox isolation.

**6. `_get` forwards credentials through arbitrary redirects, including HTTPS-to-HTTP. Sure conditional on a redirect.**

`_get`, `bonsai:312–314`:

```python
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
```

Python 3.9's default redirect handler copies every request header except content headers. A 302 from the usage/profile endpoint to another host sends `Authorization` and, for Codex, `ChatGPT-Account-Id` there. A downgrade can expose the credential in plaintext. I reproduced header forwarding without network access. This requires an endpoint, proxy, or redirect behavior that produces such a response; I did not establish an open redirect in either real provider.

Replace `_get` with a no-redirect transport, since all three endpoints are fixed:

```python
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(req, timeout=TIMEOUT) as response:
        return json.loads(response.read())
```

Do not stringify the resulting `HTTPError`; keep the existing numeric status mapping.

Test: `test_06_get_never_forwards_bearer_to_redirect` uses a fake urllib transport and the actual redirect handler, not sockets.

**7. Files default to 0644/0755; predictable `.tmp` enables clobbering and a deterministic race. Sure.**

`_write_json`, `bonsai:183–187`; `refresh:482`; `record_job:568–570`; `cmd_job:1047`:

```python
os.makedirs(os.path.dirname(path), exist_ok=True)
tmp = path + ".tmp"
with open(tmp, "w") as f:
...
with open(a.out, "w") as f:
```

With umask 022 I obtained 0644 files and a 0755 state directory. Cache contains account emails, organization names and login metadata; history contains pool identifiers and usage; ledger contains labels, provider, pool, PID and command path. Claude output can contain the sensitive material itself. Existing directory access may limit reachability, but the files are not owner-only. A symlink at `config.json.tmp` causes arbitrary target truncation. Two writers sharing `.tmp` reproducibly yield `FileNotFoundError` in one writer, and can corrupt or overwrite each other's content.

Replace `_write_json` and use the same primitive for final text output:

```python
def private_dir(path):
    os.makedirs(path, mode=0o700, exist_ok=True)
    if os.path.islink(path):
        raise SystemExit("bonsai: private directory must not be a symlink")
    os.chmod(path, 0o700)  # Only Bonsai-owned state/config/pool directories.

def atomic_text(path, text):
    parent = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".bonsai-", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def _write_json(path, obj):
    private_dir(os.path.dirname(os.path.abspath(path)))
    atomic_text(path, json.dumps(obj, indent=1, sort_keys=True, allow_nan=False))
```

For append files use `os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)`, `os.fchmod(fd, 0o600)`, and a lock around the whole append. `O_NOFOLLOW` is available on the supported Mac target; Windows needs an appropriate ACL/reparse-point implementation. Use 0700 on new pool directories; do not chmod arbitrary parent directories such as `~/.config` or a user's output directory. For Codex `-o`, allocate a private temporary result file and atomically publish it after success. Merely changing umask does not tighten existing files or stop symlinks.

Tests: `test_07_*`; execution/output lifecycle is also covered by finding 18.

**8. `Retry-After` can leak a response header in a traceback, crash probes, or hold a row forever. Sure.**

`probe_claude:394`, `probe_codex:430`:

```python
row["retry_after"] = _now() + float(e.headers.get("Retry-After") or 900)
```

An exception raised inside an `except HTTPError` handler does not reach its sibling `except Exception`. `Retry-After: Bearer SYNTHETIC_SECRET` raises `ValueError: could not convert string to float: 'Bearer SYNTHETIC_SECRET'`. This proves an arbitrary header value can reach stderr; it does **not** prove a provider normally reflects the bearer token there. A legitimate HTTP-date also crashes. `Infinity` persists as nonstandard JSON and `probe_all:444` reuses that row forever; `NaN` or a negative value bypasses backoff.

Add imports `math` and `email.utils`, and use this helper in both handlers:

```python
def retry_deadline(headers):
    raw = (headers or {}).get("Retry-After")
    delay = 900.0
    if raw:
        try:
            delay = float(raw)
        except (TypeError, ValueError, OverflowError):
            try:
                delay = email.utils.parsedate_to_datetime(raw).timestamp() - _now()
            except (TypeError, ValueError, OverflowError, OSError):
                delay = 900.0
    if not math.isfinite(delay):
        delay = 900.0
    return _now() + min(86400.0, max(180.0, delay))

# In each HTTPError handler:
row["retry_after"] = retry_deadline(e.headers)
```

Also distrust already cached deadlines:

```python
until = old.get("retry_after") if old else None
if (isinstance(until, (int, float)) and math.isfinite(until)
        and _now() < until <= _now() + 86400):
    rows.append(dict(old))
    continue
```

The one-day ceiling is a chosen local bound; it prevents an untrusted header from disabling a login indefinitely. Test: `test_08_retry_after_is_finite_bounded_and_never_echoed`.

**9. `LIMITED` is eligible; held rows are still run, and the fallback message lies. Sure.**

`route:511`, `pick:546–548`:

```python
r.get("state") not in ("OK", "LIMITED")
...
print("... taking the one with most room", file=sys.stderr)
return order[0]
```

Rows `{state:"LIMITED", wk:0, wk_at:1}` and `{state:"OK", wk:10, wk_at:2}` select the limited login. A provider's explicit rejection can reflect a cap not expressed by the two displayed percentages. With only `{wk:100,wk_at:1}` and `{wk:91,wk_at:2}`, both are held and `pick` chooses the **empty** login while saying “most room.” The held-first sort itself is correct when a usable login exists; the fallback is wrong.

Patch auto routing to accept only `state == "OK"`, and replace the all-held branch:

```python
if order[0]["held"]:
    raise SystemExit("bonsai: every eligible login is below the usable-room threshold")
```

If spending held quota is intentionally supported, make it an explicit option; then use `max(order, key=lambda r: r["left"])`. Named `LIMITED` rows currently also run; either refuse them or explicitly document the manual attempt, never silently fail over to another login.

`model_caps` is parsed at 334–343 but ignored by routing. Thus model-specific exhaustion is another possible limit the selected row can miss. Until model identity is passed through `pick` and caps are reliably mapped to model IDs, add to the route explanation: “Aggregate windows only; per-model eligibility is not verified.” Do not claim a display-name cap maps to an arbitrary model alias without provider evidence.

Tests: `test_09_*`.

**10. Malformed usage/auth data is sometimes invented as capacity and sometimes crashes outside the safe handler. Sure.**

`parse_codex_usage:355–358`:

```python
secs = w.get("limit_window_seconds") or 0
out = "5h" if secs <= 6 * 3600 else "wk"
row[out] = _pct(w.get("used_percent"))
```

Trigger: primary window is 95% used with duration 18000; secondary is 1% used with no duration. Secondary overwrites primary and the row becomes `5h=1`, hiding exhaustion. A string duration raises. A string `used_percent` becomes unknown rather than zero; that part is correct, but `room` can still route from the other known window without knowing whether the unknown window is exhausted.

`_pct:161` turns `NaN` into 100 and `-Infinity` into 0; the latter advertises a completely unused window. `probe_codex:408–413` accepts `tokens:null`, `tokens:[]`, or JWT payload `[]`, then calls `.get` outside its try block. These crash the entire gauge. Provider structure errors should fail one row, without dumping contents.

Replacement checks:

```python
# _pct, before clamping:
if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
    return None

# parse_codex_usage, instead of defaulting duration to zero:
secs = w.get("limit_window_seconds")
if (isinstance(secs, bool) or not isinstance(secs, (int, float))
        or not math.isfinite(secs) or secs <= 0):
    row["incomplete_usage"] = True
    continue  # Unknown window; never overwrite a known one.

# After parsing each recognized window in either provider:
if row[out] is None:
    row["incomplete_usage"] = True

# In route, before calculating room:
if r.get("incomplete_usage"):
    continue

# _jwt_claims, after decoding:
claims = json.loads(base64.urlsafe_b64decode(payload))
return claims if isinstance(claims, dict) else {}

# probe_codex, before any t.get / claims use:
if not isinstance(t, dict) or not isinstance(t.get("access_token"), str):
    row["state"] = "bad-credfile"
    return row
```

A malformed JWT need not itself be a hard auth failure—tokens may be opaque. It must never crash the probe. The claim-shape test is separate from malformed credential-container tests, so it does not require rejecting all opaque tokens. Guard JSON roots and nested objects throughout parsing, and put credential-file stat/read/shape handling inside the per-row error boundary. For genuinely unknown present windows, retain the `incomplete_usage` flag shown above and exclude that row from auto selection; absence alone is not proof a plan has both windows.

Tests: `test_10_*`. Claude utilization `1.0`, missing `seven_day`, and a limit without `scope` already behave correctly; see WHAT HOLDS.

**11. Parser behavior changes prompt meaning, discards pass input, and treats placement inconsistently. Sure.**

`main:1235–1240`:

```python
a, rest = ap.parse_known_args(argv)
...
a.prompt = " ".join(([a.prompt] if getattr(a, "prompt", None) else []) + rest)
```

Reproduced inputs:

| Input after `bonsai` | Result |
| --- | --- |
| `job codex review kind sensitive` | Prompt becomes `review kind sensitive`; kind remains general. A missing `--` is accepted as material. |
| `job codex --poo stanford review` | `--poo` abbreviates `--pool`; not rejected as a typo. |
| `job codex -o out - extra` | Prompt becomes literal `- extra`; stdin is not read. |
| `job codex -- -literal` | Accepted as a literal prompt. |
| `job codex -o out -- -literal` | Rejected as unrecognized `-- -literal`. |
| `pass codex material` | Parser accepts material, then `cmd_pass:1075` deletes it. |
| `run codex --pool stanford` | `REMAINDER` hands `--pool stanford` to Codex; Bonsai's pool remains auto. |

Unknown dashed options such as `--pol` are rejected; do not claim arbitrary dashed typos all become prompt text. Prompts beginning `-` need a reliable explicit boundary.

Patch: disable abbreviations on the root **and each subparser**, and remove the free-form leftovers join. To preserve the documented post-option prompt without silently joining arbitrary tokens, replace the parse block with this bounded grammar:

```python
raw = list(sys.argv[1:] if argv is None else argv)
literal = None
if raw and raw[0] == "job" and "--" in raw:
    cut = raw.index("--")
    literal = raw[cut + 1:]
    raw = raw[:cut]
    if len(literal) != 1:
        ap.error("job: after --, supply one quoted prompt")
a, rest = ap.parse_known_args(raw)
if a.cmd == "job":
    if literal is not None:
        if a.prompt is not None or rest:
            ap.error("job: supply one prompt")
        a.prompt = literal[0]
    elif rest:
        if a.prompt is not None or len(rest) != 1 or (rest[0].startswith("-") and rest[0] != "-"):
            ap.error("job: supply one quoted prompt; use -- for a leading dash")
        a.prompt = rest[0]
elif rest:
    ap.error("unrecognized arguments")
```

In addition, require the literal `--` separator for `run` and require all Bonsai flags before it, documenting that flags after it belong to the child. `run` does not have the same grammar as `job` and should not pretend to. Keep `-` alone as the stdin sentinel; reject `-` plus extra words.

Tests: `test_11_*`. These encode the stricter proposed grammar.

**12. File input is unbounded, byte limits are actually character limits, and implicit stdin can hang a file-only pass. Sure.**

`read_prompt:996–1003`:

```python
parts.append(sys.stdin.read())
with open(f, errors="replace") as fh:
    body = fh.read()
if len(body) > 400_000:
```

The entire file is read before truncation. A huge file can exhaust memory; a FIFO or device can block or never end. 400,000 Unicode characters can be much larger than 400 KB. Binary input is decoded with replacements and NULs remain, producing meaningless material and unnecessary spending. Every `-f` is allowed separately with no total prompt bound.

`cmd_pass` always clears `a.prompt`. With `-f draft` and an empty **closed pipe at EOF**, `read_prompt` reads `""`, then includes the file successfully; this is not an empty-prompt bug. With the pipe still open but empty it blocks before opening the file. With no files and EOF it raises the generic `read_prompt` error before `cmd_pass`'s own error. A closed stdin object with prompt `-` raises uncaught `ValueError`; a closed fd can raise `OSError`. No prompt plus a TTY correctly fails without trying to read the terminal.

Use an explicit stdin policy and a bounded regular-file read:

```python
# read_prompt stdin condition:
read_stdin = a.prompt == "-" or (not a.prompt and not a.file and not sys.stdin.isatty())
if read_stdin:
    try:
        parts.append(sys.stdin.read(1_600_001))
    except (OSError, ValueError):
        raise SystemExit("bonsai: stdin is unavailable") from None
    if len(parts[-1]) > 1_600_000:
        raise SystemExit("bonsai: stdin exceeds the prompt limit")

# Add import stat. For each file:
fd = os.open(f, os.O_RDONLY | os.O_NONBLOCK)
with os.fdopen(fd, "rb") as fh:
    if not stat.S_ISREG(os.fstat(fh.fileno()).st_mode):
        raise SystemExit("bonsai: -f requires a regular text file")
    raw = fh.read(400_001)
cut = len(raw) > 400_000
raw = raw[:400_000]
if b"\0" in raw:
    raise SystemExit("bonsai: binary file supplied to -f")
try:
    # Incremental decoder tolerates only an incomplete final character at the cap.
    body = codecs.getincrementaldecoder("utf-8")("strict").decode(raw, final=not cut)
except UnicodeDecodeError:
    raise SystemExit("bonsai: -f requires UTF-8 text") from None
if cut:
    body += "\n[... truncated by bonsai at 400000 bytes ...]"
```

Add `import codecs`, wrap open/stat errors in a static user-facing input error, and impose a total assembled byte limit. Validate material before `refresh` so a bad file does not first trigger usage probes. For `pass`, reject positionals (finding 11), keep `--brief` separate, and read implicit stdin only if no files were given; document that combining files and stdin requires an explicit option.

Tests: `test_12_*`.

**13. Text fences are forgeable; the anti-injection sentence is not an enforcement boundary. Sure for framing; possible for a model obeying the injected instruction.**

`read_prompt:1003`, `cmd_pass:1074–1079`:

```python
"===== FILE: %s =====\n%s\n===== END %s =====" % (f, body, f)
brief = ("\n\nThe author's brief for this pass: " + a.brief) if a.brief else ""
prompt = PASS_PROMPT + brief + "\n\n===== MATERIAL =====\n" + material
```

A file named `draft\n===== MATERIAL =====` forges prompt structure. A body can contain `===== END draft.md =====`, followed by a forged “author correction” telling the model to suppress findings or use its tools to inspect another path. All of it is one user prompt, alongside `PASS_PROMPT`. `--brief` can also contain fences and introduce apparent new sections. Tool access in finding 5 makes a successful injection more consequential. I did not run a model and do not claim a particular payload reliably succeeds.

Patch structural ambiguity, without calling it an injection cure:

```python
# Instead of filename-interpolated fences:
parts.append(json.dumps({"file": f, "content": body}, ensure_ascii=True))

# cmd_pass: brief and material are explicit encoded fields.
prompt = PASS_PROMPT + "\nThe following JSON contains untrusted review input:\n" + json.dumps(
    {"author_brief": a.brief or "", "material": material}, ensure_ascii=True)
```

Put the review policy in the provider's supported higher-priority instruction mechanism where possible; retain capability restrictions and do not execute model output. A user-supplied brief is allowed to steer focus, but it should not accidentally terminate a structural field. Encoding stops delimiter/newline ambiguity; it does not make adversarial language safe.

Tests: `test_13_*` only test structure. Add an adversarial model evaluation separately if claiming resistance to semantic injection; a deterministic unit test cannot establish it.

**14. The ledger loses pairings, mistakes reused PIDs for live jobs, and reports the wrong last completion. Sure.**

`read_jobs:576–590`:

```python
lines = f.readlines()[-limit * 2:]
by_id.setdefault(e["id"], {}).update(e)
...
if "exit" not in j and not _pid_alive(j.get("pid")):
```

Start A; finish 201 short jobs; finish A. The default 400-line suffix contains A's finish without its start, so its pool/provider/label disappear. A long-running start can disappear entirely. `readlines` still loads the whole file, so the suffix does not bound memory. Valid JSON of the wrong shape (`[]`, `{"no_id":true}`) crashes. Eight hex digits at `run_job:603` and `cmd_job:1041` give only 32-bit IDs; collisions merge unrelated jobs as history grows.

After a crash or reboot, a reused parent PID passes `os.kill(pid,0)` and makes an old job “running.” The stored PID belongs to Bonsai, not necessarily a surviving child. Start A, start B, finish B, finish A: insertion order remains A,B, so `render:778` calls B “last.” Its age at 779 is measured from start, not completion. `render` reads the ledger twice, permitting inconsistent running/done snapshots.

Use full `uuid.uuid4().hex`. Pair before limiting, validate shape, and order by each job's most recent event:

```python
def read_jobs(limit=200):
    if limit <= 0:
        return []
    by_id = {}
    try:
        with open(jobs_path(), encoding="utf-8") as f:
            for ln in f:
                try:
                    e = json.loads(ln)
                except ValueError:
                    continue
                if not isinstance(e, dict) or not isinstance(e.get("id"), str):
                    continue
                j = by_id.pop(e["id"], {})
                j.update(e)
                by_id[e["id"]] = j
    except FileNotFoundError:
        return []
    jobs = list(by_id.values())
    for j in jobs:
        if "exit" not in j:
            j["lost"] = not job_lock_held(j["id"])
    return jobs[-limit:]
```

`job_lock_held` should test a per-job advisory lock held by the Bonsai process for its entire execution, not a PID. On macOS, open `STATE/job-<full-id>.lock` privately and hold `fcntl.flock(fd, LOCK_EX)` until cleanup. The reader opens an existing lock, attempts `LOCK_EX|LOCK_NB`, returns false if acquired and true on `BlockingIOError`, then closes it; missing lock is false. Validate IDs against `[0-9a-f]{32}` before constructing the path. Legacy records with no lock must be called unverified/lost, not confidently live. The kernel releases locks on exit, preventing PID-reuse false positives. Never delete/recreate a lock while it is in use. A child surviving its parent is still an unresolved/orphaned job, not proof of normal execution.

Concrete reader helper (using `fcntl` on the supported Mac):

```python
def job_lock_held(jid):
    if not isinstance(jid, str) or not re.fullmatch(r"[0-9a-f]{32}", jid):
        return False
    try:
        fd = os.open(os.path.join(STATE, "job-" + jid + ".lock"),
                     os.O_RDWR | os.O_NOFOLLOW)
    except FileNotFoundError:
        return False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(fd)
```

Wrap each entire start/launch/finish lifecycle in `with state_lock("job-" + jid + ".lock"):` using finding 15's helper. Acquire that lock before recording the start. A missing/unreadable lock must never be interpreted as proof of liveness.

Add `finished_at: _iso(_now())` to completion events and render age from it (or legacy `at + seconds`). Read jobs once in `render`. Compact completed history under the ledger lock while retaining all unfinished records if bounded storage is needed.

For simultaneous appends, current small one-line `f.write` records commonly become one append write on macOS; I did not reproduce corruption of those ordinary records. It is not a general record-atomicity guarantee for arbitrary large writes, short writes, or concurrent compaction. Lock `record_job` around serialization/write/flush using the private append primitive from finding 7. Do not claim `O_APPEND` alone protects a multi-write record.

Tests: `test_14_*`; the failed launch lifecycle has a separate test in finding 18.

**15. Cache freshness is a check-then-act race, and `gauge --interval` only changes the displayed interval. Sure.**

`refresh:476–481`:

```python
cached = read_cache()
...
state = annotate(probe_all(cfg, cached), cfg)
_write_json(cache_path(), state)
```

Two processes can both read a stale cache and probe every login. The README's “second window ... never doubles the reads” is false. The `.tmp` race can additionally crash one gauge. `cmd_gauge:806` computes `--interval`, but calls `refresh(cfg)` with the unchanged config at 808/813: `--interval 900` displays fifteen minutes while probing every configured five minutes.

Patch: on the supported Mac, acquire an interprocess `fcntl.flock` on a private `STATE/probe.lock` **before reading the cache**, then re-read and hold the lock through probe/cache/history publication. Concurrent forced callers should compare the cache generation they saw before waiting and reuse a generation another waiter just produced; serial `--fresh` requests may still force refresh. An in-process-only lock is insufficient. The core lock wrapper is:

```python
@contextlib.contextmanager
def state_lock(name):
    private_dir(STATE)
    fd = os.open(os.path.join(STATE, name),
                 os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)
```

Add `contextlib` and `fcntl`; wrap the whole refresh body in `with state_lock("probe.lock"):`. Apply equivalent Windows locking before supporting concurrent Windows use. In `cmd_gauge`, immediately after calculating `interval`, add:

```python
cfg = {**cfg, "interval": interval}
```

`annotate` deliberately mutates rows. A normally loaded cache is a new JSON object each call, so this does not by itself mutate the on-disk cache. It can mutate an in-memory `previous` row reused by backoff; copy such rows as shown in finding 8, or clone in `annotate` if callers need independent snapshots. I found no independent wrong-login exploit from this mutation in the current CLI.

Tests: `test_15_*`.

**16. Direct calls ignore the supplied usage policy because `_CFG` is populated only by `main`. Sure.**

`cfg_flag:209`, `probe_all:438`, `main:1244`:

```python
return bool(((_CFG.get(section) or {}).get(key, True)))
_CFG.update(cfg)
```

`probe_all({"usage_reads":{"codex":False}})` still calls the provider when imported or used by tests: `_CFG` is empty and defaults to true. Existing tests load config but never install it in `_CFG`. Repeated calls to `main` update rather than replace global state. String `"false"` is also truthy; `config --set usage_reads.codex='"false"'` visually looks disabled to some users but isn't.

Patch: pass `cfg` through `probe_claude(pool, dir, cfg)` and `probe_codex(pool, dir, cfg)`; remove `_CFG`:

```python
def cfg_flag(cfg, section, key):
    value = (cfg.get(section) or {}).get(key, True)
    if not isinstance(value, bool):
        raise SystemExit("bonsai: usage-read switches must be JSON booleans")
    return value
```

Update the two calls in `probe_all` and the two `cfg_flag` uses. If optional cfg defaults are kept for backward compatibility, load config explicitly rather than silently enabling reads. Claude's existing switch only skips its consumer usage endpoint after reading the profile; it is not an all-network-off switch. Institution treatment in the comment is not implemented by a pool's flag: the branch uses the provider-reported plan.

Test: `test_16_probe_all_honors_passed_config_without_main`.

**17. Config output is an unrestricted echo, and displayed strings can contain terminal controls. Sure, conditional on supplied configuration/data.**

`cmd_config:1159`:

```python
print(json.dumps(cfg, indent=1, sort_keys=True))
```

`load_config` accepts any key and `--set` writes it. `bonsai config --set access_token='"SYNTHETIC_SECRET"'` writes and prints it. A credential-bearing URL stored in an arbitrary value is also printed. This is not an automatic path from `auth.json` or the Keychain into config: Bonsai never copies those blobs there. It is a real exception to an unconditional “no token can ever be printed/written” promise, and makes support requests for the “whole config” unsafe.

Minimal output patch: show a schema projection instead of arbitrary keys, and validate that same schema before saving/loading. For example, output only known top-level keys, only `name` and provider-specific institution metadata within logins, two strings with valid provider enums for model entries, and validated booleans/numbers for policy fields. Do **not** silently accept arbitrary values under the allowed containers.

```python
allowed = set(DEFAULT_CONFIG)
if set(cfg) - allowed:
    raise SystemExit("bonsai: config contains unsupported keys; remove them before displaying it")
# Run structural validation of each allowed value here before save/print.
```

A strict schema does not detect a token intentionally put in a display name. Narrow README:188 to: “Bonsai's usage probes do not deliberately print or persist credential blobs; config values and CLI output are user-controlled and may contain sensitive information.” Avoid claims that arbitrary child output can be guaranteed token-free.

`render:754,772,777–779`, `cmd_doctor:895–898`, `cmd_route:935`, and `cmd_jobs:1091` also print external names/labels without escaping controls. A newline or ESC sequence can spoof rows or manipulate the terminal. Truncating to eleven characters does not neutralize an escape sequence. Apply this to **data fields**, before Paint inserts intentional color sequences:

```python
def display_text(value):
    return "".join(c if c.isprintable() else "\\u%04x" % ord(c) for c in str(value))
```

Tests: `test_17_*`; filename control-character containment also has `test_13_newline_filename_is_escaped`.

**18. Claude's output branch loses job completion on exceptions and destroys a previous answer on failure. Sure.**

`cmd_job:1045–1051`:

```python
p = subprocess.run(..., capture_output=True)
with open(a.out, "w") as f:
    f.write(p.stdout)
if p.returncode != 0:
    sys.stderr.write(p.stderr)
```

A failed CLI returning empty stdout truncates a previous result. Missing executable, bad cwd, `PermissionError`, `KeyboardInterrupt`, or output write failure skips the completion event. `run_job` handles two cases but not other `OSError`s. A nonexistent cwd is misreported as an uninstalled executable. Claude output is captured entirely in memory. With `--cd` and relative `-o`, Claude writes relative to Bonsai's cwd while Codex handles its output under child behavior; normalize this contract explicitly.

Patch the duplicated execution paths into one lifecycle: create the start record and hold its job lock; initialize `code=1`; launch/capture in a `try`; translate launch errors to static messages/codes; record completion including `finished_at` in `finally`; publish output only after success. Relevant replacement lines for Claude:

```python
code = 1
try:
    p = subprocess.run(argv, env=child_env(provider, row["pool"]), cwd=cd,
                       input=text, text=True, capture_output=True)
    code = p.returncode
    if code == 0:
        code = 1  # Publishing the result can itself fail.
        atomic_text(os.path.abspath(a.out), p.stdout)
        code = 0
    else:
        print("bonsai: child command failed (exit %d)" % code, file=sys.stderr)
except KeyboardInterrupt:
    code = 130
except OSError:
    code = 127
    print("bonsai: could not launch command or publish output", file=sys.stderr)
finally:
    record_job({"id": record["id"], "exit": code,
                "finished_at": _iso(_now()), "seconds": round(_now() - t0, 1)})
return code
```

For large output, stream into a private temporary file and publish that after success instead of retaining stdout in RAM. Normalize a nonempty `a.out` with `os.path.abspath` before building either CLI argv. Error details can be captured in a private diagnostic file by explicit opt-in; printing arbitrary child stderr cannot support a no-token-output guarantee. Normal stdout may also contain secrets the model was allowed to read. `codex -o` does not inherently suppress final stdout. [Codex noninteractive output](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable).

Tests: `test_18_*`.

**19. Timestamp unit guessing is ambiguous, and nonfinite numbers survive into later crashes. Sure for ambiguity/nonfinite behavior.**

`_when_ts:127`:

```python
return float(v) / 1000.0 if v > 1e11 else float(v)
```

`100000000000` is treated as seconds (year 5138); `100000000001` is treated as milliseconds (1973). This is a discontinuity, but no magnitude heuristic can distinguish all valid seconds from all valid milliseconds. A 1973 timestamp is not a plausible future quota reset in this application. `NaN` and infinity pass through and later crash `_iso`, `_age`, or sorting/rendering assumptions. `_age(-100)` clamps to `<1m`; that is intentional, not an arithmetic bug, though it hides an already-expired reset as imminent.

Patch numeric timestamps to reject nonfinite values, then use explicit units where the provider schema supplies them. If accepting the existing mixed-unit heuristic for compatibility, bound interpreted dates to the application's documented operational range rather than claiming universal timestamp support:

```python
if isinstance(v, (int, float)) and not isinstance(v, bool):
    x = float(v)
    if not math.isfinite(x):
        return None
    x = x / 1000.0 if x > 1e11 else x
    return x if 946684800 <= x <= 4102444800 else None  # 2000 through 2100
```

Apply the range check consistently to parsed ISO values and reject timezone-naive reset strings if the provider has not specified their timezone. Do not change the threshold to 1e12 and pretend the ambiguity disappears. Display a passed reset as `due` separately from `_age` if desired.

Test: `test_19_nonfinite_timestamp_is_unknown`; ISO strings and negative `_age` are covered by a passing holds test.

**20. Machine labels overstate the measurements; Windows reports fictitious swap and mishandles unknown power. Sure for semantics; Windows execution verified with mocks only.**

`machine_stats:638`:

```python
st["cpu"] = min(100.0, os.getloadavg()[0] / ncpu * 100.0)
```

Load average divided by core count is not measured CPU utilization. The board can display 100% after work has stopped, or label queue pressure as current CPU use. Replace the field with `st["load_per_core"] = os.getloadavg()[0] / ncpu`, render it as `LOAD/core`, or sample actual CPU counters across time. Do not invent a CPU percentage.

Mac memory is an estimate of non-free/non-inactive/non-speculative pages, not Activity Monitor memory pressure. The page-size regex correctly handles Apple Silicon's 16384-byte page size. The battery regex handles ordinary `charging`, low discharging percentages, and appended warning lines; a desktop without a battery produces no percentage and renders `·`, without crashing. I could not break these requested examples.

Windows `bonsai:690`:

```python
st["swap_gb"] = max(0.0, (m.ullTotalPageFile - m.ullAvailPageFile)
                    - (m.ullTotalPhys - m.ullAvailPhys)) / 2**30
```

The `PageFile` fields are commit limits/availability, not bytes currently stored in the page file. Subtracting physical usage does not measure swap. Remove this assignment; leave swap unknown until using the correct metric. [MEMORYSTATUSEX semantics](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/ns-sysinfoapi-memorystatusex).

At 697–699, `ACLineStatus=255` becomes false (battery power), and `BatteryFlag & 128` is ignored. Replace with:

```python
kernel = ctypes.windll.kernel32
if kernel.GetSystemPowerStatus(ctypes.byref(p)):
    if p.BatteryFlag != 255 and not (p.BatteryFlag & 128) and 0 <= p.BatteryLifePercent <= 100:
        st["batt"] = int(p.BatteryLifePercent)
    if p.ACLineStatus in (0, 1):
        st["ac"] = p.ACLineStatus == 1
```

Render missing `ac` as `?`, not as `batt`. [SYSTEM_POWER_STATUS semantics](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-system_power_status).

Set explicit function prototypes (`argtypes=[POINTER(...)]`, `restype=wintypes.BOOL`; `GetTickCount64.argtypes=[]`, `restype=c_ulonglong`) and check failures separately so one exception does not discard remaining metrics. The existing structure layouts, `dwLength`, and 64-bit tick return type are correct on Windows; absence of argtypes is not evidence of pointer truncation when passing `byref`. Naming the fourth power byte `Reserved1` instead of modern `SystemStatusFlag` is outdated, not an ABI offset bug. No CPU figure on Windows is already disclosed.

Tests: `test_20_*` plus `test_holds_mac_battery_and_apple_silicon_page_size`.

**21. Pool names are paths, so a login can escape its pool root. Sure.**

`pool_dir:218`, `cmd_login:907–909`:

```python
return os.path.join(POOLS_HOME, root, pool)
pool = a.email
d = pool_dir(provider, pool)
os.makedirs(d, exist_ok=True)
```

`bonsai login ../.codex --codex` targets the default `.codex` directory through `.codex-pools/../.codex`; an absolute argument ignores the configured pool root. A typo or generated command can therefore replace another login instead of creating an isolated seat. Newlines also become terminal/prompt data. No email or path-component validation occurs. Discovery follows symlinked pool directories, so apparent pools can alias the same credential directory.

Add this before joining a non-default pool, and reject symlinked discovered pool directories if isolation is claimed:

```python
if (not isinstance(pool, str) or not pool or pool in (".", "..")
        or os.path.isabs(pool) or "/" in pool or "\\" in pool
        or any(ord(c) < 32 or ord(c) == 127 for c in pool)):
    raise SystemExit("bonsai: pool must be one nonempty directory name")
```

`default` remains an explicit documented special case. If labels may be arbitrary Unicode, keep that policy separate from directory-component validation. Test: `test_21_pool_path_cannot_escape_root`.

**WHAT HOLDS**

- Normal credential blobs flow from `.credentials.json`/Keychain or Codex `auth.json` to local token parsing and request headers; there is no deliberate credential-blob field in cache, history, or ledger.
- Ordinary HTTP errors record a numeric status, not the body, URL, headers, or reason. Generic probe exceptions record only the exception class. The escaping `Retry-After` handler is the identified exception.
- Keychain subprocess stdout/stderr are captured; `claude_blob` does not print them, including its timeout/error branches.
- `cmd_doctor` prints statuses and configured labels/model IDs, not credential blobs. Its Codex “ok” is only file existence, so it is not authentication verification.
- `cmd_config` does not read or merge CLI credential files; its leak requires sensitive data in the user-controlled config itself.
- The held flag precedes reset time in the sort, so a usable row beats a held row even when the held row resets sooner.
- `wk_at=None` sorts after a known reset without a comparison error. Its explanation misleadingly says `<1m`; use `unknown` instead of subtracting zero for that text.
- `last_good` is for display; an auto-route does not revive a `re-login` row from those percentages. Stale data is not visibly dated per row and is dropped after a second failed probe, but it does not make that dead row auto-eligible.
- A sole institution Claude row does not become a general auto fallback.
- Two matching prefixes raise ambiguity; a `personal` display label colliding with a pool literally named `personal` also raises. Neither silently chooses a login. Exact pool IDs matching another pool's prefix can also be rejected; that is availability friction, not wrong-login selection.
- A named institution target really does bypass general `kind`; that is an explicit destination choice. The sensitive-to-personal exception is finding 4.
- `job astra --model opus` fails when `resolve_model` sees the provider conflict. Raw model IDs are not provider-validated, but they do not change the selected provider; the CLI may reject them.
- Claude utilization uses 0–100 correctly; missing `seven_day` stays absent; a weekly limit without `scope` is skipped.
- String `used_percent` stays unknown; ISO `reset_at` parses; negative `_age` clamps without crashing.
- Empty non-TTY stdin plus `-f` succeeds; no material plus a TTY fails without hanging.
- Desktop/no-battery, normal charging, low battery with an extra warning line, and Apple Silicon 16 KB `vm_stat` pages passed synthetic checks.
- Windows structs and the explicitly declared `GetTickCount64` return width are not broken in the ways a generic ctypes warning would suggest.
- The current board test `assertNotIn("\n", line)` after `splitlines()` is tautological; the passing suite does not test terminal-control safety, real sandbox behavior, or effective credential precedence.

**VERDICT**

**Do not ship.** The current code can route a supposedly institution-bound job through inherited credentials or the wrong CLI configuration, can mark one provider's personal login institution because another provider shares its email, and permits named personal targets to bypass `--kind sensitive`. Credential forwarding through redirects, public-readable output/state, and the false sandbox promise compound those risks. Fix the blocking routing/authentication and data-boundary defects first, then the deterministic parsing, backoff, file, ledger and concurrency failures. The existing passing tests do not exercise those boundaries. The proposed patches and red regression tests are review material, not a claim that the implementation has been repaired or that a paid end-to-end login test has been performed.
