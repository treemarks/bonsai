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

Run the `git clone` line first and stop if it reports an error; the lines after it assume the
folder exists (if `~/code/bonsai` already exists, look at what is in it before going on). These
public HTTPS downloads need no GitHub account: the clone, a normal `bonsai update` from the same
public origin, and the Codex release archive in step 3. They do need network access to GitHub and
its download hosts. If anything ever prompts you for a GitHub username, stop: check the address,
the network or proxy, and the checkout's remote, rather than creating an account or pasting a
token. If you were handed the folder instead (a zip, AirDrop, a USB stick), put it at
`~/code/bonsai` and run the lines from `mkdir` on; `bonsai update` then tells you it is not a
checkout, and a newer copy goes into a different empty folder before you point the launcher at it
(a zip can also drop the executable bit: if `/usr/bin/python3 ~/code/bonsai/bonsai --version`
works but `bonsai` says permission denied, `chmod +x ~/code/bonsai/bonsai`).

`bonsai doctor` lists what is installed and which logins it can see, prints the install line for
anything missing, and exits non-zero until `git`, `claude` and `codex` all answer. Exit 0 means
the three tools answered their version checks, nothing more: it does not test download or sign-in
connectivity, and a failed install or update is diagnosed by that command's own error. Before
sign-in you may see no login rows at all, or `default` rows marked `no-login`; an already
signed-in row on a Mac someone else set up is one to check before you reuse it.

## 5. Sign in

This section assumes you have never signed in to a command-line tool. Each sign-in is the same
shape: a command in Terminal, a page that opens in your browser, and Terminal noticing when the
page is done. Open Terminal, copy one command at a time (without the surrounding backticks), press
Return, and wait until the command finishes and the prompt comes back before the next one. Replace
`you@stanford.edu` with your own Stanford address everywhere below. Passwords and two-step codes
belong in the browser, never in Terminal or in a chat; the one thing a provider may ask you to type
into Terminal is a one-time login code it shows you in the browser, and that goes only into that
command's own prompt.

Some screens are conditional or come in a different order than listed: the quoted labels were
read out of Claude Code 2.1.303 and Codex 0.159.0, but this sequence has not been run from a fresh
account end to end. So choose options by their words, not their position, read any question you
were not told to expect instead of pressing Return through it, and sign in only to accounts you
already have (skip a personal provider you do not use; nothing here needs a purchase). Before you
approve any browser page, check the e-mail it shows and, for ChatGPT, the workspace. If it is the
wrong account or you are unsure, cancel that attempt (Ctrl-C in Terminal), open the command's new
login link in a private browser window, and try again.

**If someone else, or Claude Code, is setting this up for you:** they can run the commands and
start each sign-in; you complete every browser page yourself (e-mail, password, two-step,
workspace, approve) and tell them which workspace you chose. They must not choose a workspace,
request an account, or accept a purchase or an account migration for you, and you never send them
a password, a code or a credential file. Run the personal sign-ins (5a, 5b) in your own Terminal
window, not inside an agent's terminal tool.

**Before you start: the accounts must exist.** You need only the accounts you intend to use: a
personal Claude and a personal ChatGPT are each optional, and a Stanford account must be
provisioned by Stanford before its sign-in. Stanford's seats are requested from the university,
not created at claude.ai or chatgpt.com, and the request is yours to submit (Stanford asks you for
your own attestation). If you have not requested them yet, do that first and expect provisioning
to take a little time:

- **Stanford Claude** (Claude for Education): request it at
  [uit.stanford.edu/service/claude](https://uit.stanford.edu/service/claude). *Standard* is free
  for eligible active students, faculty, staff and postdocs (affiliate eligibility differs) and
  includes Claude Code; *Premium* adds usage and the Fable models and is paid (rates and
  commitment terms: [uit.stanford.edu/rates/claude](https://uit.stanford.edu/rates/claude)). Once
  provisioned you sign in at claude.ai with your `@stanford.edu` address and **Continue with SSO**.
- **Stanford ChatGPT, which includes Codex** (ChatGPT Edu): request it at
  [uit.stanford.edu/service/openai-chatgpt-edu](https://uit.stanford.edu/service/openai-chatgpt-edu).
  Start with *Standard* if you are eligible for the no-cost tier; *Pro* is optional, paid, and
  higher-usage ([uit.stanford.edu/rates/openai-chatgpt-edu](https://uit.stanford.edu/rates/openai-chatgpt-edu)).
  Paid tiers bill an approved university funding account (a PTA) or an eligible student's tuition
  account; nothing in this guide needs one. At sign-in the picker has shown two workspaces,
  **Stanford University Plus (Edu)** and **Stanford University Pro (Edu)**; Plus appears to be
  Standard, but UIT has not confirmed that mapping for this guide, and you may have only one. If
  you already use a personal ChatGPT or Claude account on your Stanford e-mail, read UIT's
  migration guidance before requesting: the invitation can start a migration that cannot be
  cancelled, and that choice is yours, not a setup step.
- Stanford's own pages, not Bonsai, say what each account is approved for; `bonsai doctor` prints
  the request page for any provider that has no institution login here.

If you cannot sign in to `claude.ai` or `chatgpt.com` with an account in a normal browser tab, the
CLI cannot sign in with it either; sort that out first (web access shows the account exists, not
that the CLI is entitled; that is the sign-in's job to find out).

**Which account is which.** On a MacBook with a personal Claude Pro and two Stanford seats you
will do four sign-ins: personal Claude (step 5a), personal ChatGPT if you have one (5b), Stanford
Claude (5c), Stanford ChatGPT (5d). Each browser page asks you to sign in; use the account that
step names, and if the browser is already signed in to another account on that site, the page
may skip straight to a choice of accounts or workspaces: choose the one the step names.

### 5a. Personal Claude: `claude`

```bash
claude
```

1. If asked **Choose the text style that looks best with your terminal**, pick one with the arrow
   keys and press Return. If instead you land in a chat or at a login menu, that is fine; screens
   may come in another order, and a Claude Code that was already set up skips this.
2. If asked **Select login method:**, highlight **Claude account with subscription** (your Pro,
   Max, Team or Education account on claude.ai) with the arrow keys and press Return; not
   **Anthropic Console account** (API billing), not **3rd-party platform**. If you are told you are
   already signed in, check which account before going on. If asked about an API key, stop and use
   the subscription sign-in instead.
3. A browser tab opens on claude.ai (if it does not, Terminal says how to copy the link; use that).
   Check the e-mail shown is your personal account before you approve Claude Code. If the page
   shows someone else's account, switch accounts there, or open this attempt's link in a private
   window.
4. Keep Terminal open. Either the browser finishes and Terminal shows **Login successful. Press
   enter to continue**, or the browser shows a login code, which you paste only into Terminal's
   **Paste code here if prompted >** and press Return. Wait for Terminal to say it succeeded; an
   error is not success.
5. Read each remaining question; do not accept a permission you do not recognize just to finish.
   Once you reach Claude's chat input, type `/exit` and press Return.

Check: `claude auth status` prints a block of lines; `"loggedIn": true` and your e-mail should be
among them.

### 5b. Personal ChatGPT, if you have one: `codex`

```bash
codex login
```

1. If a menu headed **Choose how you want to use Codex.** appears, highlight **Sign in with
   ChatGPT** ("Usage included with Plus, Pro, Business, and Enterprise plans") with the arrow keys
   and press Return. Do not pick **Provide your own API key** or **Use Amazon Bedrock**: those
   bill separately. (**Sign in with Device Code** is the fallback described below.) `codex login`
   usually skips the menu and goes straight to the browser.
2. Terminal prints **Starting local login server on http://localhost:1455.** and a link, and the
   browser opens it. Check the e-mail shown and sign in to your own personal ChatGPT account; if
   the page offers another person's account, switch, or open this attempt's link in a private
   window.
3. If asked to **Select a workspace**, choose your *personal* workspace for this step and press
   **Continue**. If no personal workspace is offered, or you cannot tell which it is, stop here;
   do not choose a Stanford workspace to get through.
4. Wait for Terminal to print **Successfully logged in** and return to the prompt. (If you ran the
   full `codex` app instead, it shows **Press Enter to continue.**, then its chat; press Return,
   then Ctrl-C to leave.)

Check: `codex login status` prints `Logged in using ChatGPT`.

If the browser never opens, or after you sign in it shows a connection error for a `localhost`
address, finish or cancel that command first (Ctrl-C), then run `codex login --device-auth`: it
prints a short code and a link; open the link, sign in, type the code. Codex's browser sign-in
returns to your own Mac on port 1455, which a local firewall, VPN or proxy setting can block, and
device-code sign-in works only if your account or workspace allows it.

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
2. Terminal prints **Opening browser to sign in…**, then **If the browser didn't open, visit:**
   and a long `claude.com` link, then waits at **Paste code here if prompted >**. Your browser
   opens that link with your Stanford address already filled in. If it does not open, copy the
   whole link from Terminal (triple-click selects the line) and paste it into a browser.
3. Check the browser shows your Stanford e-mail (the command's e-mail is a hint to the page, not
   proof of the account it signs in). Choose **Continue with SSO** if it is offered: that is how
   Stanford's Claude for Education signs in, and the Stanford login (SUNet ID, password, two-step)
   follows; if an organization choice appears, choose Stanford's. If the intended account is not
   available, cancel this attempt with Ctrl-C and run the same line again with `--sso` added; if it
   still is not, the account is not provisioned yet (UIT, not Bonsai).
4. Approve only the intended Stanford account. As in 5a, either the browser finishes on its own or
   it shows a code to paste into Terminal's own prompt.
5. Wait for the command to finish. Terminal prints `recorded as stanford` and `signed in as` the
   e-mail, organization and plan Claude Code reports for the pool. If the e-mail is not the one you
   asked for, Bonsai records nothing and prints the sign-out line to run before trying again.

### 5d. Stanford ChatGPT (Codex): `bonsai login ... --codex --institution`

```bash
bonsai login you@stanford.edu --codex --institution
```

1. Terminal prints **Starting local login server on http://localhost:1455.** and **If your
   browser did not open, navigate to this URL to authenticate:** with an `auth.openai.com` link,
   and the browser opens it. Enter your `@stanford.edu` address; it sends you through the Stanford
   login (SUNet ID, password, two-step). If your browser is already signed in to chatgpt.com, the
   page may skip the password and go straight to the next step; check that the address shown at
   the top is your Stanford one, and use **Cancel** and a private window if it is not.
2. If a **Select a workspace** page appears, choose the exact Stanford workspace you were
   provisioned and press **Continue**. Two labels have been seen there: **Stanford University
   Plus (Edu)** and **Stanford University Pro (Edu)**; Plus appears to be Stanford's free Standard
   tier and Pro the paid one, but UIT has not confirmed that mapping for this guide, and you may
   have only one of them. If you cannot tell which is yours, stop and ask UIT rather than guess.
   Each sign-in binds to one workspace; Codex's own rule for switching is to sign out and in again.
3. Wait for the command to finish: Terminal prints **Successfully logged in**, then `recorded as
   stanford` and `signed in as` the e-mail, plan (`edu_pro`, for example) and a short workspace id.
   If the e-mail is not the one you asked for, Bonsai records nothing and prints the sign-out line
   to run before trying again. Bonsai cannot name the workspace; the plan and the id are the only
   clues it has, so confirm against what you chose in the browser.

If you have both workspaces and want both on the board, sign in a second time into a pool of its
own, choosing the other workspace in the browser:

```bash
bonsai login you@stanford.edu --codex --institution --pool stanford-pro --name stanford-pro
```

It shows on the board as `stanford-pro` and is the target `stanford-pro-codex`; `stanford-codex`
still means the first pool (names match exactly, never by prefix). If both pools show the same
workspace id in `bonsai doctor`, you signed into the same workspace twice: sign the second one out
(the exact line is below) and repeat with the other workspace chosen. If the page says the
workspace does not exist, Stanford's FAQ says the browser's cache is the likely cause: cancel the
command, run it again, and open its new link in a private window with your `sunetid@stanford.edu`
address; if that fails too, the workspace is not provisioned (UIT).

If the Stanford Codex browser sign-in cannot complete (the `localhost` page never loads), the
one-time-code route keeps the sign-in in the same pool:

```bash
bonsai login you@stanford.edu --codex --institution --device-auth
```

It works only if the workspace allows device-code sign-in; otherwise it says so, and the fix is
the browser route from another network, not a bare `codex login` (which would sign in your
personal pool).

### Then check

Run `bonsai doctor` and read each line against the account you meant. For Claude it shows the
e-mail, the organization and the plan Claude Code reports; for Codex the e-mail, the plan and a
short workspace id. The Stanford ones carry `⌂ institution (marked by you; workspace approval not
verified)`: the e-mail, the plan and the `⌂` mark do not prove which workspace you chose, and
nothing here proves approval for any data; what you confirmed in the browser is the record. A pool
that shows `no-login` after a sign-in you completed means the credential was stored somewhere
Bonsai does not read (Codex keyring storage) or the sign-in went to another pool; do not keep
signing in to the default account to make it green. Then `bonsai gauge --once --fresh` for a board
that re-probes every login.

Where the sign-ins live, and how to undo one: Claude keeps each pool's credential in your login
Keychain, Codex in the pool folder's `auth.json`. The exact sign-out line names the pool folder
(no routing, no usage check in the way); replace the address with the pool you mean:

```bash
CODEX_HOME="$HOME/.codex-pools/you@stanford.edu" codex logout
```

```bash
CLAUDE_CONFIG_DIR="$HOME/.claude-pools/you@stanford.edu" claude auth logout
```

(`stanford-pro` in place of the address for that pool; personal logins sign out with the CLIs'
own `codex logout` and `claude auth logout`.) Signing out is a deliberate change to an account;
do it for the pool you mean, not as blanket cleanup.

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
  you turn that on ([details](docs/ACCOUNTS.md#what-bonsai-reads-and-what-it-never-does)); it shows the login's plan from Claude Code itself.
  It confirms the sign-in only; it does not measure remaining usage or certify any data approval.
- `re-login`: the sign-in lapsed; run the same `bonsai login` line (or `claude` / `codex`) again.
- `locked` or `keychain-timeout` (only with Claude usage reads on): the credential could not be
  read in this shell — over SSH, or the macOS allow dialog went unanswered. Run the board in a
  Terminal window on the Mac itself and, when macOS asks whether `security` may read the item,
  choose **Always Allow** (your Mac login password).
- `limited`: the provider has stopped calls on that login until the reset shown; Bonsai does not
  route around it.
- `cli-missing`: `claude` or `codex` was not found from this shell. Run the full-path version
  check from step 2 or 3: if it fails, install the CLI; if it works, this shell (or the agent's) is
  missing `~/.local/bin` on its PATH; a new Terminal window usually has it.
- `no-login` after a sign-in you completed: the credential went to another pool, or Codex is
  configured to keep credentials in the keyring, which Bonsai does not read. Check the pool, not
  the account.

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
