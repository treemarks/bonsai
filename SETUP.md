# Setting up Bonsai on a Mac that has nothing on it

Written so that a person, or the coding agent they paste it to, can follow it top to bottom on a
fresh macOS 26 or 27 install. Every step says how to check whether it is already done. Windows
is later; the last section says what is already in place for it.

## What Bonsai needs

| Need | Why | Comes from |
|---|---|---|
| `python3` 3.9+ | Bonsai is one Python file, standard library only | Apple's Command Line Tools (step 1); macOS has had 3.9 there since Monterey |
| `git` | to clone this repository | Command Line Tools (step 1) |
| `claude` | Claude Code, the CLI every Claude job runs through | Anthropic's native installer (step 2) |
| `codex` | Codex CLI, the CLI every Codex job runs through | OpenAI's release binary or Homebrew (step 3) |
| a Claude login and/or a ChatGPT login | the seats the jobs run on | you (step 5) |
| network to `api.anthropic.com` and `chatgpt.com` | the CLIs and the usage reads | — |

Nothing else: no Homebrew, no Node, no pip packages, no Treemarks code. Homebrew is an
alternative route in steps 2 and 3, not a requirement. The stock macOS tools Bonsai calls
(`security`, `sysctl`, `vm_stat`, `pmset`) are on every Mac.

## 1. Command Line Tools (git and python3)

Check: `git --version && python3 --version` — both answer, python3 is 3.9 or newer.

If either is missing, macOS offers to install the tools the first time you run `git` or
`python3` in Terminal; accept the dialog, or run it yourself:

```bash
xcode-select --install
```

Wait for the installer to finish (a few minutes), then open a **new** Terminal window.

## 2. Claude Code

Check: `claude --version`.

Native installer, no Homebrew or Node needed:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

It puts `claude` in `~/.local/bin`; the installer tells you if that folder is not on your PATH
(step 4 fixes it). Alternatives: `brew install --cask claude-code`, or
`npm install -g @anthropic-ai/claude-code` if you already have Node.

## 3. Codex CLI

Check: `codex --version`.

Either of these; the first needs nothing else installed:

```bash
# A. the release binary (Apple Silicon; use x86_64 for an Intel Mac)
mkdir -p ~/.local/bin && cd /tmp && curl -fsSLO https://github.com/openai/codex/releases/latest/download/codex-aarch64-apple-darwin.tar.gz \
  && tar -xzf codex-aarch64-apple-darwin.tar.gz && mv codex-aarch64-apple-darwin ~/.local/bin/codex && chmod +x ~/.local/bin/codex
```

```bash
# B. Homebrew (install Homebrew first from https://brew.sh if you want this route)
brew install codex
```

## 4. Bonsai

```bash
git clone https://github.com/treemarks/bonsai ~/code/bonsai
mkdir -p ~/.local/bin && ln -sf ~/code/bonsai/bonsai ~/.local/bin/bonsai
grep -q '.local/bin' ~/.zshrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
bonsai doctor
```

`bonsai doctor` lists what is installed and which logins it can see, and prints the install
line for anything missing. It should show `git`, `claude`, `codex` with versions and `keychain
readable`.

## 5. Sign in

Your everyday logins first, so the CLIs themselves work:

```bash
claude          # follow the sign-in; then /exit
codex           # follow the sign-in; then Ctrl-C
```

Those become the `personal` row on the board. Then each institution seat as its own pool:

```bash
bonsai login you@stanford.edu --claude --institution
bonsai login you@stanford.edu --codex  --institution
```

Each opens the provider's sign-in page in your browser; pick the institution organization
or workspace when asked. **First board on macOS:** `bonsai gauge --once` reads each Claude
login's credential from your login Keychain, and macOS asks once per login whether to allow
it (the item was created by `claude`, so `security` has to be allowed). Click **Always Allow**,
with your Mac login password, and it never asks again. Over SSH the Keychain is locked and the
row reads `locked`; run the board in a Terminal on the Mac itself.

## 6. Check it works

```bash
bonsai gauge --once               # the board, one frame
bonsai route                      # which login each kind of work would take
bonsai job codex --dry-run "hi"   # the exact command a job would run, nothing spent
bonsai job codex -o /tmp/hi.md "Reply with exactly: ok" && cat /tmp/hi.md
bonsai install-skill              # teach Claude Code the routing words
```

Run the tests any time: `/usr/bin/python3 -m unittest discover -s ~/code/bonsai/tests`.

## Updating

```bash
cd ~/code/bonsai && git pull
```

The CLIs update themselves (`claude update`; `codex` tells you when a newer release exists).

## Windows (later)

The code already keeps its platform-specific parts apart, so a Windows release is a matter of
testing, not redesign:

- Credentials: Claude Code on Windows keeps the OAuth blob in `%USERPROFILE%\.claude\.credentials.json`
  (and in each pool's folder); Codex keeps `auth.json` in `CODEX_HOME` on every platform. Bonsai
  reads the file first and the Keychain only on macOS.
- Paths: pools under `%USERPROFILE%\.claude-pools\` and `.codex-pools\`; state under
  `%LOCALAPPDATA%\bonsai\state`, config under `%APPDATA%\bonsai\config.json`.
- Machine row: memory, battery and uptime through the Win32 API (ctypes); no CPU figure yet.
- Keyboard: `msvcrt` instead of termios; ANSI colours are switched on at start.
- Installers: `irm https://claude.ai/install.ps1 | iex` for Claude Code; the
  `codex-*-pc-windows-msvc.exe` release for Codex; `winget install Git.Git` and
  `winget install Python.Python.3.12`.

None of this has been run on a Windows machine yet; `bonsai doctor` will say so when it has.
