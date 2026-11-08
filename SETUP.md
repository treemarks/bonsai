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
routed. Bonsai asks you to acknowledge this notice once, when you add your first institution
account (or prints it once before your first job, if that comes first), and prints a one-line
reminder on every chat-driven job to an institution account. **If an agent sets this up for you, it must show you this notice in its
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

No GitHub account is involved: the clone is an anonymous download over HTTPS, and nothing in
Bonsai talks to GitHub afterwards except `bonsai update`, which is the same download again. If you
were handed the folder instead (a zip, AirDrop, a USB stick), put it at `~/code/bonsai` and run the
lines from `mkdir` on; `bonsai update` then tells you it is not a checkout, and a newer folder
replaces the old one the same way.

`bonsai doctor` lists what is installed and which logins it can see, prints the install line for
anything missing, and exits non-zero until `git`, `claude` and `codex` all answer. Exit 0 means
the three tools answered their version checks, nothing more: read the login lines yourself. Before
step 5 it shows the two `default` pools as `no-login`; that is expected.

## 5. Sign in

This section assumes you have never signed in to a command-line tool. Each sign-in is the same
shape: a command in Terminal, a page that opens in your browser, and Terminal noticing when the
page is done. Nothing is typed into Terminal except the commands shown (and, once, `I understand`).
You never type a password into Terminal; passwords go only into the browser pages.

**Before you start: the accounts must exist.** A personal Claude or ChatGPT account you can sign
in to on the web, and, for Stanford, accounts that Stanford has provisioned. Stanford's seats are
requested from the university, not created at claude.ai or chatgpt.com; if you have not requested
them yet, do that first, and expect the invitation to take a little time:

- **Stanford Claude** (Claude for Education): request it at
  [uit.stanford.edu/service/claude](https://uit.stanford.edu/service/claude). *Standard* is free to
  anyone with a SUNet ID; *Premium* (paid, on a PTA or student account) adds quota and the Fable
  models. Once it exists you sign in at claude.ai with your `@stanford.edu` address and **Continue
  with SSO**.
- **Stanford ChatGPT, which includes Codex** (ChatGPT Edu): request it at
  [uit.stanford.edu/service/openai-chatgpt-edu](https://uit.stanford.edu/service/openai-chatgpt-edu).
  Two tiers, and they are two separate workspaces you will see side by side at sign-in: **Stanford
  University Plus (Edu)** is the free *Standard* tier, with ChatGPT Plus-level usage limits;
  **Stanford University Pro (Edu)** is the paid *Pro* tier (PTA or student account), with Pro-level
  limits. Both include Codex. Most students have Plus. A sign-in binds to one of them; if you have
  both and want both on the board, step 5d shows the second sign-in.
- Stanford's own pages, not Bonsai, say what each account is approved for; `bonsai doctor` prints
  these two pointers whenever no institution login is set up.

If you cannot sign in to `claude.ai` or `chatgpt.com` with an account in a normal browser tab, the
CLI cannot sign in with it either; sort that out first.

**Which account is which.** On a MacBook with a personal Claude Pro and two Stanford seats you
will do four sign-ins: personal Claude (step 5a), personal ChatGPT if you have one (5b), Stanford
Claude (5c), Stanford ChatGPT (5d). Each browser page asks you to sign in; use the account that
step names, and if the browser is already signed in to another account on that site, the page
may skip straight to a choice of accounts or workspaces: choose the one the step names.

### 5a. Personal Claude: `claude`

```bash
claude
```

1. The first run asks **Choose the text style that looks best with your terminal**: press Return
   to accept the default.
2. **Select login method:** lists **Claude account with subscription**, **Anthropic Console
   account** and **3rd-party platform**. Choose the first (your Pro, Max, Team or Education account
   on claude.ai); Console is API billing and 3rd-party is for cloud providers. Move with the arrow
   keys, confirm with Return.
3. Your browser opens on claude.ai. Sign in with your personal account (the one you use at
   claude.ai), then approve the request to let Claude Code use it. If the browser does not open,
   press `c` in Terminal to copy the link and paste it into a browser yourself.
4. Two endings are normal: the browser says you can close the tab and Terminal shows
   **Login successful. Press enter to continue**; or the browser shows a code instead, which you
   paste into Terminal at **Paste code here if prompted >**, then Return.
5. Press Return, answer any remaining setup question with Return, then type `/exit` and Return to
   leave Claude Code.

Check: `claude auth status` prints a block of lines; `"loggedIn": true` and your e-mail should be
among them.

### 5b. Personal ChatGPT, if you have one: `codex`

```bash
codex
```

1. The first screen, **Choose how you want to use Codex.**, lists **Sign in with ChatGPT**
   ("Usage included with Plus, Pro, Business, and Enterprise plans"), **Sign in with Device Code**
   ("Sign in from another device with a one-time code"), **Provide your own API key** ("Pay for
   what you use") and **Use Amazon Bedrock**. Press Return on the first. (Device Code is the
   fallback described below; the API-key and Bedrock options bill separately and are not what you
   want.)
2. Your browser opens on OpenAI's sign-in. Sign in with your personal ChatGPT account.
3. If that account belongs to more than one workspace, the page says **Select a workspace** and
   lists them, each with a small building or person icon. For this step choose your *personal*
   workspace, not a Stanford one, then **Continue**.
4. The browser says you are signed in and can return to the terminal; Terminal shows
   **Successfully logged in.** and **Press Enter to continue.** Press Return, then Ctrl-C (hold
   Control, press C) once or twice to leave Codex.

Check: `codex login status` prints `Logged in using ChatGPT`.

If the browser never opens, or shows a connection error for a `localhost` address after you sign
in, run `codex login --device-auth` instead: it prints a short code and a link; open the link,
sign in, type the code. (Codex's browser sign-in listens on your own Mac at port 1455; VPNs and
some campus networks block that page.)

Those two are the `personal` rows on the board. Now the Stanford accounts, each as its own pool.
These are separate saved sign-ins: adding Stanford does not sign anything else out, and does not
change the account of any chat you have open.

### 5c. Stanford Claude: `bonsai login ... --claude --institution`

```bash
bonsai login you@stanford.edu --claude --institution
```

1. This first `--institution` prints the notice from the top of this file and asks you to type
   `I understand` — into this Terminal window, then Return (not into the browser or a chat). It
   asks once, on this first login only; the second Stanford login and everything after it do not
   ask again. (When a script or an agent runs this rather than a person, the notice is printed and
   the sign-in proceeds without that prompt, which is why the agent must show you the notice
   itself.)
2. Terminal prints a link and opens it in your browser; your Stanford address is already filled
   in. If the browser does not open, copy the link from Terminal and paste it into a browser.
3. On the claude.ai page choose **Continue with SSO** (not the password box): that is how
   Stanford's Claude for Education signs in. The Stanford login (SUNet ID and password, then the
   two-step prompt) follows. If the page offers more than one organization, choose Stanford's.
   If SSO is not offered, run the same line again with `--sso` added.
4. Approve the request to let Claude Code use the account. As in 5a, either the browser finishes
   on its own or it shows a code to paste into Terminal.
5. Terminal says `signed in` and then prints what Bonsai recorded. The line ends with a reminder
   to check what `bonsai doctor` shows for this login.

### 5d. Stanford ChatGPT (Codex): `bonsai login ... --codex --institution`

```bash
bonsai login you@stanford.edu --codex --institution
```

1. The browser opens on OpenAI's sign-in. Enter your `@stanford.edu` address; it sends you through
   the Stanford login (SUNet ID, password, two-step).
2. The page says **Select a workspace** and lists what that address holds. Stanford's free
   Standard tier appears as **Stanford University Plus (Edu)**; the paid tier as **Stanford
   University Pro (Edu)**. Pick the one you have (Plus, for most students) and press
   **Continue**. Each sign-in binds to one workspace; the two are separate accounts with separate
   usage limits, and Codex's own rule for switching is to sign out and in again.
3. The browser says you are signed in; Terminal prints what Bonsai recorded.

If you have both workspaces and want both on the board, sign in a second time into a pool of its
own; the second sign-in is the same walk with the other workspace chosen:

```bash
bonsai login you@stanford.edu --codex --institution --pool stanford-pro --name stanford-pro
```

It shows on the board as `stanford-pro` and is the target `stanford-pro-codex`. If the page says
the workspace does not exist, Stanford's FAQ says that is the browser's cache: open a private
window and sign in there with your `sunetid@stanford.edu` address.

### Then check

`bonsai doctor` should now show each login as `signed in as ...` with its account and
organization, the Stanford ones marked `⌂ institution (marked by you; workspace approval not
verified)`. Read the account and organization on each line: your university e-mail and the `⌂`
mark do not prove you picked the university workspace, and neither proves approval for any data.
A login that signed in but shows `no-login` or `re-login` was recorded without a completed sign-in;
run its line again.

Where the sign-ins live: Claude keeps each pool's credential in your login Keychain, Codex in the
pool folder's `auth.json`. Signing out is `bonsai run --pool stanford -- codex logout` (Codex) or
`bonsai run --pool stanford -- claude auth logout` (Claude); personal logins sign out with the
CLIs' own `codex logout` and `claude auth logout`.

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
bonsai update
```

That is a fast-forward `git pull` of the checkout; it prints the old and new version, and tells
you to run `bonsai install-skill` when the skill Claude Code uses is older than the new version
(the skill install never overwrites a skill you edited; it leaves a `.new` file). Claude Code
knows this too: "update bonsai" in a session runs the same thing. The CLIs update themselves
(`claude update`; `codex` tells you when a newer release exists; the release-binary install in
step 3 can be run again).

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
