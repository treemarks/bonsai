# Set up Bonsai on your Mac

Hi, I'm Bonsai 🪴. I let your coding agent ask your other AI accounts (your Stanford Claude and ChatGPT seats,
or a personal Claude or ChatGPT) and show how much each has left. Give this file to Claude Code or Codex and say
*"help me set up Bonsai"*. It takes about 40 minutes once your accounts exist.

**What will happen:** your helper checks which accounts you have, helps you request any Stanford seat you're
missing, installs the tools and Bonsai's skill, starts each sign-in and tests it. Setup adds a `bonsai` command and
saves sign-ins on this Mac. **You** complete every browser sign-in, choose workspaces and submit seat requests.
No GitHub account is needed, nor Homebrew, and personal subscriptions are optional.

**Before you route work:** a job you route from a chat goes through that chat, so a Stanford seat doesn't
give that chat Stanford's protections. Bonsai doesn't check files for private data; for protected
information, use a Stanford-approved tool directly.

> **For the coding agent.** You are helping someone set up Bonsai on their Mac. Do this, in order:
>
> 1. Say what will happen (above), and that they do every browser step. Check that you can run commands on this
>    Mac; if not, guide them through their own Terminal ("By hand" below), one command at a time.
> 2. Ask in one message: which agent will use Bonsai (the Claude app, Claude Code in Terminal, or Codex) and
>    whether it is signed in; their Stanford e-mail; which accounts they want Bonsai to use (a Stanford
>    Claude seat, a Stanford ChatGPT seat, a personal Claude, a personal ChatGPT) and, for each Stanford
>    seat they want, whether it is active, requested, missing or unsure; and whether a personal account already
>    uses their Stanford e-mail. A Bonsai sign-in does not sign the agent itself in: if it isn't, sign it in
>    first with an account it accepts.
> 3. For a wanted seat that is missing or unsure, walk them through "Request a seat" below: open the page, explain
>    it; they attest and submit. Keep installing while a request is pending, and leave that seat's sign-in for
>    later. If no account is usable yet, finish the install and report setup as waiting for the seat.
> 4. Do steps 1 to 4, skipping what each step's check shows is done; step 4 installs the skill (setup isn't
>    finished until `bonsai install-skill` succeeds; NOT UPDATED means resolve it first). After step 4, run
>    `~/.local/bin/bonsai`: your shell started before it.
> 5. Do step 5 for the accounts they have. They run 5a and 5b in their own Terminal; you may start 5c and 5d in
>    the background and show them the link to open in a private window, then wait for `recorded as`.
> 6. Do step 6: one job per account, by its own target. Then have them quit and reopen the agent, and in a new chat
>    say *"ask chat to reply with ok"* (or *"ask claude to reply with ok"* if they have no ChatGPT account). Setup is
>    done when that runs bonsai and answers `ok`; until then, report it as waiting for that check.
> 7. Last, show them the board (`bonsai gauge`, or ask first), tell them that's the command for it, and ask
>    whether they'd like it each time they open Terminal; on a yes, add
>    `command -v bonsai >/dev/null && bonsai gauge --once` to their `~/.zshrc`.
>
> Put their real address in every command; never a placeholder (chat apps put a Run button on commands, and a
> placeholder runs as typed). **Never** submit a request or attestation, choose a workspace, accept a purchase or
> migration, or ask for a password, a code or a credential file. Never route protected data. Keep each reply
> short: what is done, and the next step.

## Request a seat

Stanford's seats are requested from the university, not created at claude.ai or chatgpt.com:

1. **Already have one?** Sign in at claude.ai or chatgpt.com with your Stanford e-mail; if Stanford's login opens
   a Stanford workspace, you have that seat.
2. **A personal account on your Stanford e-mail?** Read UIT's migration guidance on the page below first: the
   invitation can start a migration that cannot be undone. That choice is yours.
3. **Request it.** Your helper can open the page and explain it; you attest and submit (Stanford asks for your own
   attestation):
   - **Stanford Claude** (Claude for Education): [uit.stanford.edu/service/claude](https://uit.stanford.edu/service/claude)
   - **Stanford ChatGPT, which includes Codex** (ChatGPT Edu):
     [uit.stanford.edu/service/openai-chatgpt-edu](https://uit.stanford.edu/service/openai-chatgpt-edu)
4. **Wait for the invitation.** Provisioning takes a little time. Setup goes on meanwhile; that seat's sign-in
   (step 5c or 5d) waits for it. `bonsai doctor` prints these pages for any seat it hasn't seen.

Stanford's pages, not Bonsai, say what each account is approved for.

## By hand

**Opening Terminal.** Press Cmd-Space, type `Terminal`, press Return. The line that ends in `%` is the prompt.
Copy one command at a time (without the surrounding backticks), paste it after the `%`, press Return, and wait
for the `%` to come back before the next one. Every step says how to check whether it is already done. Screen
labels are quoted from Claude Code 2.1.303 and Codex 0.159.0; later versions may word them differently, so choose
options by their words, not their position.

## Read this first

Bonsai prints this once, before your first sign-in or your first job:

```text
Before your first job (shown once; nothing to type):
  - A job you route from a chat goes through that chat (details from your conversation can go with it),
    outside Stanford's protections.
  - Fine for ordinary work. For private data (student records, health records), use
    a Stanford-approved tool directly.
    https://uit.stanford.edu/guide/riskclassifications
  - Bonsai doesn't check your files for private data.
```

At Stanford, PHI goes only through Stanford's approved routes (such as its AI API Gateway); Bonsai's sign-in route is not one of them.

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

Skip this step if you have no Claude account.

Check: `claude --version`, or `"$HOME/.local/bin/claude" --version` (it answers once installed).

If you have Homebrew (`brew --version` answers), use it: it checks the download's digest.

```bash
brew install --cask claude-code
```

Otherwise Anthropic's own installer, which needs nothing else and trusts its download over HTTPS:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

It puts `claude` in `~/.local/bin` and may print a yellow note that `~/.local/bin` is not on your PATH: ignore it,
step 4 fixes that. (`npm install -g @anthropic-ai/claude-code` also works if you already use Node.)

## 3. Codex CLI

Skip this step if you have no ChatGPT account.

Check: `codex --version`, or `"$HOME/.local/bin/codex" --version`.

If you have Homebrew, use it (it checks the download's digest):

```bash
brew install codex
```

Otherwise the release binary, for whichever chip the Mac has, needing nothing else installed:

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

This trusts OpenAI's release page over HTTPS and checks nothing more; Homebrew, above, also checks a digest.

## 4. Bonsai

Check first: if `~/code/bonsai` already exists, run `~/code/bonsai/bonsai --version`. If it is 0.5 or newer, run
`~/code/bonsai/bonsai update` instead of cloning. If it is older (0.2.x), move it aside and clone a fresh copy;
your sign-ins and settings live outside that folder and carry over:

```bash
mv ~/code/bonsai ~/code/bonsai-old-$(date +%Y%m%d%H%M)
```

Then (or, with no `~/code/bonsai` yet, straight away):

```bash
git clone https://github.com/treemarks/bonsai ~/code/bonsai
mkdir -p ~/.local/bin && ln -sf ~/code/bonsai/bonsai ~/.local/bin/bonsai
touch ~/.zshrc
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' ~/.zshrc || printf '%s\n' 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
~/.local/bin/bonsai install-skill
~/.local/bin/bonsai doctor
```

Run the `git clone` line first and stop if it reports an error; the lines after it assume the folder exists. If
anything asks for a GitHub username, stop and check the address and the network; never create an account or paste a
token to get past it. If your shell is bash (`echo $SHELL` ends in `bash`), add the same `export PATH=...` line to
`~/.bash_profile` too.

`bonsai install-skill` is part of setup, not an extra: it writes the skill that tells Claude Code (and Codex, if
installed) to answer "ask chatgpt" with Bonsai, at `~/.claude/skills/bonsai-route/SKILL.md` (and
`~/.agents/skills/bonsai-route/SKILL.md`). Without it, a new chat does not know Bonsai is there.

A Terminal window or agent session opened before this step does not find `bonsai` yet (`command not found`): open
a new window, or use `~/.local/bin/bonsai` there.

`bonsai doctor` lists what is installed and which logins it can see, and says what to do next. Its exit status is a
tools check only (git and at least one provider's CLI answer): it does not mean a login works, the skill is current or
a job succeeds. Before you sign in it shows no logins, or `default` rows marked `no-login`, and a line for each
institution account it hasn't seen, with the page where it is requested: a pointer, not an error.

## 5. Sign in

Each sign-in is the same shape: a command in Terminal, a page that opens in your browser, and
Terminal noticing when the page is done. Replace `you@stanford.edu` with your own Stanford address
everywhere below. Passwords and two-step codes go in the browser, never in Terminal or a chat.
Read any question you were not told to expect instead of pressing Return through it.

**About codes.** Usually the browser finishes on its own. Only when Terminal is waiting at its own
**Paste code here if prompted >** and the browser shows a code, paste the code there. If the
browser shows a code after Terminal has finished, you do not need it: close the tab. Never paste a
code at the `%` prompt.

**Which account is which.** Each step names its account, one of the four at the top. Before you
approve any browser page, check the e-mail it shows and, for ChatGPT, the workspace; if it is the
wrong account, cancel (Ctrl-C in Terminal) and open the command's new link in a private window. An
account that cannot sign in at `claude.ai` or `chatgpt.com` in a browser cannot sign in here either.

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
4. Keep Terminal open until it shows **Login successful. Press enter to continue** (codes: see
   above). An error is not success.
5. Read each remaining question; do not accept a permission you do not recognize just to finish.
   Once you reach Claude's chat input, type `/exit` and press Return.

Check: `claude auth status` prints a block of lines; `"loggedIn": true` and your e-mail should be
among them.

### 5b. Personal ChatGPT: `codex`

**If you skip this** (no personal ChatGPT), `codex`, `astra` and `sol` jobs run on your
Stanford ChatGPT seat from 5d instead; nothing else changes.

```bash
codex login
```

1. If a menu headed **Choose how you want to use Codex.** appears, highlight **Sign in with
   ChatGPT** ("Usage included with Plus, Pro, Business, and Enterprise plans") with the arrow keys
   and press Return. Do not pick **Provide your own API key** or **Use Amazon Bedrock**: those
   bill separately. `codex login` usually skips the menu and goes straight to the browser.
2. Terminal prints **Starting local login server on http://localhost:1455.** and a link, and the
   browser opens it. Check the e-mail shown and sign in to your own personal ChatGPT account; if
   the page offers another person's account, switch, or open this attempt's link in a private
   window.
3. If asked to **Select a workspace**, choose your *personal* workspace for this step and press
   **Continue**. If no personal workspace is offered, or you cannot tell which it is, stop here;
   do not choose a Stanford workspace to get through.
4. Wait for Terminal to print **Successfully logged in** and return to the prompt.

Check: `codex login status` prints `Logged in using ChatGPT`.

If the browser never opens, or shows a connection error for a `localhost` address, cancel
(Ctrl-C) and run `codex login --device-auth`: open the link it prints, sign in, type its code.

Those two are the `personal` rows on the board. Now the Stanford accounts, each as its own pool.
These are separate saved sign-ins: adding Stanford does not sign anything else out, and does not
change the account of any chat you have open.

### 5c. Stanford Claude: `bonsai login ... --claude --institution`

Open a private window in your browser first (Safari: File > New Private Window; Chrome: File >
New Incognito Window) and leave it open: a browser already signed in to a personal claude.ai
can otherwise finish this sign-in with the wrong account.

```bash
bonsai login you@stanford.edu --claude --institution
```

1. The first time, Bonsai prints the notice from the top of this file; there is nothing to type.
2. Terminal prints **Opening browser to sign in…**, then **If the browser didn't open, visit:**
   and a long `claude.com` link, and waits at **Paste code here if prompted >**. Close the tab that
   opened by itself, copy the whole link from Terminal (triple-click selects the line) and paste
   it into the private window.
3. Check the browser shows your Stanford e-mail (the command's e-mail is a hint to the page, not
   proof of the account it signs in). Choose **Continue with SSO** if it is offered: that is how
   Stanford's Claude for Education signs in, and the Stanford login (SUNet ID, password, two-step)
   follows; if an organization choice appears, choose Stanford's. If the intended account is not
   available, cancel this attempt with Ctrl-C and run the same line again with `--sso` added; if it
   still is not, the account is not provisioned yet (UIT, not Bonsai).
4. Approve only the intended Stanford account. As in 5a, the browser usually finishes on its own
   (codes: see above).
5. Wait for the command to finish. Terminal prints `recorded as stanford` and `signed in as` the
   e-mail, organization and plan Claude Code reports for the pool. If the e-mail is not the one you
   asked for, Bonsai marks the pool so no job uses it and prints a sign-out line: run the same
   `bonsai login` line again in a private window to replace it, or the sign-out line if you stop.

### 5d. Stanford ChatGPT (Codex): `bonsai login ... --codex --institution`

Open a private window first, as in 5c: close the tab that opens by itself and paste the link
Terminal prints into the private window.

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
   If the e-mail is not the one you asked for, Bonsai marks the pool so no job uses it and prints
   the sign-out line to run before trying again. Bonsai cannot name the workspace; the plan and the id are the only
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

Run `bonsai doctor` and read each line against the account you meant: for Claude the e-mail,
organization and plan; for Codex the e-mail, plan and a short workspace id. The Stanford ones
carry `⌂ institution (marked by you; workspace approval not verified)`: that mark is your
declaration, and nothing here proves approval for any data. A pool marked `✗ signed in as another
account` is refused by every job until you sign it in again in a private window.

## 6. Check it works

```bash
bonsai gauge --once                         # the board, one frame
bonsai job codex --dry-run "hi"             # which login a job would take, and why; nothing runs
bonsai job codex -o ~/Bonsai/hi.md "Reply with exactly: ok" && cat ~/Bonsai/hi.md
bonsai job claude -o ~/Bonsai/hi.md "Reply with exactly: ok" && cat ~/Bonsai/hi.md
```

Run the lines for the providers you have; each prints `ok`. To try each login by name, use its target: `stanford-codex`, `stanford-claude`,
`personal-codex`, `personal-claude`. A login you did not sign in to is refused with its name.

## 7. Check your agent knows the words

Step 4 installed the skill; `bonsai install-skill` again refreshes it (after an update, say).

```bash
bonsai install-skill
```

It writes the skill for each agent on your Mac (Claude Code's and Codex's); quit and reopen your
agent to load it. Read it once: it is what your agent will do with the words. If you will use Bonsai with university data,
someone in your unit should review it first; Stanford asks that of
repeatable AI workflows and skills. **NOT UPDATED** means you
edited the skill: review the `.new` file beside it and move it over yourself.

Use it in the **Code** tab of the Claude desktop app, `claude` in Terminal, or Codex; a chat at
claude.ai cannot reach your Mac. In Codex, approve running bonsai outside its sandbox when it asks.
Try *"show my board"*, then *"ask sol to reply with ok"*.

## If you see...

- a yellow note that `~/.local/bin` is not in your PATH (step 2): step 4 fixes it.
- **Your organization may apply global configuration to Claude Code** (after 5c): your
  institution's managed settings. Expected.
- **job ... started; `bonsai cancel ...` stops it**: every job says this. It stops itself after 20
  minutes; `bonsai jobs` shows it running.
- **... is running low on ... usage** or **... has run out**: that login's week is nearly or fully
  used; a named job there waits for its reset, `auto` takes another login.
- **the tool's own messages are in ...**: a job failed; that private file holds what the CLI said
  (your institution's Codex policy warnings, for one).
- `unavailable` on a Claude row: no usage reading yet. It fills in after a Claude job, or when you
  open the board ([details](docs/ACCOUNTS.md#what-bonsai-reads-and-stores)).
- `re-login`: the sign-in lapsed; run the same `bonsai login` line (or `claude` / `codex`) again.
- `limited`: the provider has stopped calls on that login until the reset shown; Bonsai does not
  route around it.
- `cli-missing`: `claude` or `codex` was not found from this shell. Run the full-path check from
  step 2 or 3: if it fails, install the CLI; if it works, this shell (or the agent's) is missing
  `~/.local/bin` on its PATH; a new Terminal window usually has it.
- `no-login` after a sign-in you completed: the credential went to another pool, or Codex keeps
  credentials in the keyring (`cli_auth_credentials_store = "keyring"`), which Bonsai does not
  read. Check the pool, not the account.

## Undoing a sign-in

Claude keeps each pool's credential in your login Keychain, Codex in the pool folder's
`auth.json`. The sign-out line names the pool folder; replace the address with the pool you mean:

```bash
CODEX_HOME="$HOME/.codex-pools/you@stanford.edu" codex logout
```

```bash
CLAUDE_CONFIG_DIR="$HOME/.claude-pools/you@stanford.edu" claude auth logout
```

Personal logins sign out with the CLIs' own `codex logout` and `claude auth logout`. Signing out
is a deliberate change to an account; do it for the pool you mean, not as blanket cleanup.

## Updating

```bash
bonsai update
```

It fetches, prints the list of new commits, and merges only when you type yes; nothing new runs
before that. Then `bonsai install-skill` if it says so. In Claude Code, *"update bonsai"* shows you
the same list first. The CLIs update themselves (`claude update`; `codex` says when a newer release
exists, and step 3 can be run again).

Windows is next; this release is for macOS.
