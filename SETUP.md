# Setting up Bonsai on a Mac that has nothing on it

Written so that a person, or the coding agent they paste it to, can follow it top to bottom on a
fresh macOS 26 or 27 install. Every step says how to check whether it is already done. Windows
is later; the last section says what is already in place for it.

**Read this before anything else.** When you ask a chat you are already in (Claude Code or Codex,
on your own account) to run a job on an institution account such as Stanford's Claude or ChatGPT
Edu, that chat can see the task and the results, and handles them under its own account and
settings. Choosing the institution account for the job does not give the chat the institution's
protections. So only route work that is allowed in the chat you started from; ordinary personal
work is fine, and you remain responsible for what you share. For protected information —
confidential student records, research interviews, health records, anything your institution
classes Moderate or High Risk — open a tool and account your institution approves for that
information yourself, outside the chat, and do not bring protected results back into the chat. An
institution login alone does not establish approval (at Stanford, Claude is not approved for PHI
at all). Bonsai does not check files for protected information; it refuses a job that declares
`--data moderate|high|phi` before it reads a file, wherever it runs from, and undeclared data is
routed. Bonsai prints this notice before your first job and at `install-skill`, asks you to
acknowledge it when you add an institution account, and prints a one-line reminder on every
chat-driven job to one. **If an agent sets this up for you, it must show you this notice in its
reply before routing any work; completing a browser sign-in does not acknowledge it.**

## What Bonsai needs

| Need | Why | Comes from | Check |
|---|---|---|---|
| Apple's Command Line Tools: `git`, `python3` 3.9+ | Bonsai is one Python file, standard library only; `git` clones it | `xcode-select --install` (step 1) | `/usr/bin/git --version && /usr/bin/python3 -c 'import sys; assert sys.version_info >= (3, 9); print(sys.version)'` |
| `claude` (Claude Code) | every Claude job and identity read runs through it | Anthropic's native installer (step 2) | `"$HOME/.local/bin/claude" --version` |
| `codex` (Codex CLI) | every Codex job and usage read runs through it | OpenAI's release binary (step 3) | `"$HOME/.local/bin/codex" --version` |
| a ChatGPT login with Codex access and/or a Claude login | the seats the jobs run on | you (step 5) | `codex login status`; `claude auth status` |
| network to `api.anthropic.com` and `chatgpt.com` | the CLIs themselves | — | — |

Nothing else: no Homebrew, no Node, no pip packages, no Treemarks code. Homebrew and npm are
optional alternatives in steps 2 and 3, not requirements. The stock macOS tools Bonsai calls
(`security`, `sysctl`, `vm_stat`, `pmset`, `tar`, `curl`) are on every Mac.

**Not supported yet:** a Codex configured to keep credentials in the keyring
(`cli_auth_credentials_store = "keyring"`); Bonsai reads only Codex's default file storage.

## 1. Command Line Tools (git and python3)

Check: `git --version && python3 --version` — both answer, python3 is 3.9 or newer.

If either is missing, macOS offers to install the tools the first time you run `git` or
`python3` in Terminal; accept the dialog, or run it yourself:

```bash
xcode-select --install
```

The Terminal prompt comes back before the installer is done. Stop here until the installer window
says it has finished (a few minutes), then open a **new** Terminal window and rerun the check.

## 2. Claude Code

Check: `"$HOME/.local/bin/claude" --version` (plain `claude --version` works after step 4 puts
that folder on your PATH).

Native installer, no Homebrew or Node needed:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

It puts `claude` in `~/.local/bin` (step 4 puts that folder on your PATH). Alternatives:
`brew install --cask claude-code`, or `npm install -g @anthropic-ai/claude-code` if you already
have Node.

## 3. Codex CLI

Check: `"$HOME/.local/bin/codex" --version` (plain `codex --version` after step 4).

The release binary, for whichever chip the Mac has, needing nothing else installed:

```bash
(
  set -eu
  case "$(uname -m)" in arm64) arch=aarch64 ;; x86_64) arch=x86_64 ;; *) echo "unsupported chip" >&2; exit 1 ;; esac
  tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
  asset="codex-${arch}-apple-darwin"
  curl -fSL "https://github.com/openai/codex/releases/latest/download/${asset}.tar.gz" -o "$tmp/codex.tar.gz"
  tar -xzf "$tmp/codex.tar.gz" -C "$tmp"
  mkdir -p "$HOME/.local/bin"
  install -m 755 "$tmp/$asset" "$HOME/.local/bin/codex"
)
```

Alternative, if you already have Homebrew: `brew install codex`.

## 4. Bonsai

```bash
git clone https://github.com/treemarks/bonsai ~/code/bonsai
mkdir -p ~/.local/bin && ln -sf ~/code/bonsai/bonsai ~/.local/bin/bonsai
touch ~/.zshrc
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' ~/.zshrc || printf '%s\n' 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
bonsai doctor
```

`bonsai doctor` lists what is installed and which logins it can see, prints the install line for
anything missing, and exits non-zero until `git`, `claude` and `codex` all answer. Exit 0 means
the three tools answered their version checks, nothing more: read the login lines yourself. Before
step 5 it shows the two `default` pools as `no-login`; that is expected.

## 5. Sign in

Your everyday logins first, so the CLIs themselves work:

```bash
claude          # follow the sign-in in the browser; then /exit
codex           # follow the sign-in in the browser; then Ctrl-C
```

Those become the `personal` row on the board. Then each institution account as its own pool.
These are separate saved sign-ins: adding Stanford does not change the account of any chat you
have open.

```bash
bonsai login you@stanford.edu --claude --institution
bonsai login you@stanford.edu --codex  --institution
```

The first `--institution` prints the notice from the top of this file and asks you to type
`I understand` — into this Terminal window, then Return (not into the browser or a chat). When
the command is run by a script or an agent rather than a person, the notice is printed and the
sign-in proceeds without that prompt, which is why the agent must show you the notice itself.
Each line then opens the provider's sign-in page in your browser; pick the institution organization
or workspace when asked. The account is recorded as an institution account for that provider only
when its sign-in completes.

Then `bonsai doctor` again: it should now show each login as `signed in as ...` with its account
and organization, the Stanford ones marked `⌂ institution (marked by you; workspace approval not
verified)`. Check the account and organization shown: your university e-mail and the `⌂` mark do
not prove you picked the university workspace, and neither proves approval for any data.

## 6. Check it works

```bash
bonsai gauge --once                  # the board, one frame
bonsai route                         # which login each kind of work would take
bonsai job codex --dry-run "hi"      # the exact command a job would run, nothing spent
bonsai job codex -o /tmp/hi.md "Reply with exactly: ok" && cat /tmp/hi.md
```

The last line needs a personal ChatGPT login with Codex access (`bonsai route codex` lists an
eligible login for general work). With only an institution Codex seat, test
`bonsai job stanford-codex -o /tmp/hi.md "Reply with exactly: ok"` instead; Claude sign-in is
needed only for Claude jobs.

Optional, and worth a minute's thought: `bonsai install-skill` prints the notice and teaches
Claude Code the routing words. Read the file it writes: it is what the agent will do with the words,
including stopping when it recognizes protected data and relaying the notice before its first
route. It does not detect protected information; undeclared data is routed. If you will use Bonsai
with university data, someone in your unit should review that file first; Stanford asks that of
repeatable AI workflows and skills. If the command says **NOT UPDATED**, Claude Code is still
using an older or edited skill; review the `.new` file it left and move it over yourself.

Run the tests any time: `/usr/bin/python3 -m unittest discover -s ~/code/bonsai/tests`.

## If the board says...

- `signed-in` on a Claude row with no numbers: normal. Bonsai does not read Claude's usage unless
  you turn that on (README §What Bonsai reads); it shows the login's plan from Claude Code itself.
  It confirms the sign-in only; it does not measure remaining usage or certify any data approval.
- `re-login`: the sign-in lapsed; run the same `bonsai login` line (or `claude` / `codex`) again.
- `locked` or `keychain-timeout` (only with Claude usage reads on): the credential could not be
  read in this shell — over SSH, or the macOS allow dialog went unanswered. Run the board in a
  Terminal window on the Mac itself and, when macOS asks whether `security` may read the item,
  choose **Always Allow** (your Mac login password).
- `limited`: the provider has stopped calls on that login until the reset shown; Bonsai does not
  route around it.
- `cli-missing`: `claude` or `codex` is not on PATH in this shell; open a new Terminal window.

## Updating

```bash
cd ~/code/bonsai && git pull
```

The CLIs update themselves (`claude update`; `codex` tells you when a newer release exists; the
release-binary install in step 3 can be run again).

## Windows (later)

The platform-specific parts are kept apart and the Windows branches exist, but the Windows release
still needs implementation work and testing. In place now:

- Credentials: Claude Code on Windows keeps the OAuth blob in `%USERPROFILE%\.claude\.credentials.json`
  (and in each pool's folder); Codex keeps `auth.json` in `CODEX_HOME`. Bonsai reads the file
  first and the Keychain only on macOS, and only when Claude usage reads are on.
- Paths: pools under `%USERPROFILE%\.claude-pools\` and `.codex-pools\`; state under
  `%LOCALAPPDATA%\bonsai\state`, config under `%APPDATA%\bonsai\config.json`.
- Liveness without `os.kill` (a Win32 process query), `msvcrt` keyboard and locks, ANSI colours
  switched on at start, memory/battery/uptime through the Win32 API (no CPU or swap figure).
- Installers: `irm https://claude.ai/install.ps1 | iex` for Claude Code; the
  `codex-*-pc-windows-msvc.exe` release for Codex; `winget install Git.Git`,
  `winget install Python.Python.3.12`.

Still to do for Windows: a `bonsai.cmd` launcher (the shebang and `ln -sf` are not a Windows
install), UTF-8 handling of console pipes, `codex.exe`/`codex.cmd` discovery in every path, and a
run on a real machine. `bonsai doctor` will say so when it has been done.
