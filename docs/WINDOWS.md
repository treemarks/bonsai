# Bonsai on Windows

Bonsai is built and used on Macs. On Windows, its tests pass on GitHub's Windows machines (Python 3.9, 3.12
and 3.13), but nobody has yet run a real job there with real sign-ins. If you try it, please tell us what
happened, good or bad.

## Install (PowerShell)

Open a new PowerShell window after each install, so it sees what the install added.

1. **Python.** `winget install Python.Python.3.12`. Check `py -3 --version`. Don't rely on a `python3` that
   opens the Microsoft Store.
2. **Git.** `winget install Git.Git`. Claude Code also uses its Git Bash.
3. **Claude Code.** `irm https://claude.ai/install.ps1 | iex`
4. **Codex.** `winget install OpenJS.NodeJS.LTS`, then `npm.cmd install -g @openai/codex`. Bonsai starts
   npm's Codex by running its own script with Node, never through its `codex.cmd` file. If you'd rather use the
   downloaded `codex-…-windows-msvc.exe`, rename it to `codex.exe` and put it in a folder on your PATH.
   (Claude Code installed through npm isn't supported; use step 3.)
5. **Bonsai.** `git clone https://github.com/treemarks/bonsai "$HOME\bonsai"`
6. **A `bonsai` command.** This makes two small launchers in `%USERPROFILE%\.local\bin` and puts that folder
   on your PATH. One launcher is for PowerShell and CMD, the other for Git Bash, which Claude Code uses:

   ```powershell
   $bin = "$HOME\.local\bin"; New-Item -ItemType Directory -Force $bin | Out-Null
   $user = [Environment]::GetEnvironmentVariable("Path", "User")
   if (";$user;" -notlike "*;$bin;*") { [Environment]::SetEnvironmentVariable("Path", "$user;$bin", "User") }
   '@py -3 "%USERPROFILE%\bonsai\bonsai" %*' | Set-Content "$bin\bonsai.cmd" -Encoding ascii
   "#!/bin/sh`nexec py -3 ""`$HOME/bonsai/bonsai"" ""`$@""`n" | Set-Content "$bin\bonsai" -Encoding ascii -NoNewline
   ```

7. Open a new window and run `bonsai doctor`. Then follow [SETUP.md](../SETUP.md) from the sign-ins on.

## What is different on Windows

- **Where things live.** Logins are in `%USERPROFILE%\.claude-pools` and `%USERPROFILE%\.codex-pools`.
  Bonsai's state is in `%LOCALAPPDATA%\bonsai\state` and its settings in `%APPDATA%\bonsai\config.json`.
- **Sign-ins are files.** Claude Code keeps a login in a file inside that login's folder, not in a keychain.
  Windows doesn't apply Bonsai's Mac-style private file modes, so anything running as you can read those
  files. A routed job is started with its tools turned off, so the model is given no way to open them.
- **Garbled symbols.** Bonsai reads and writes UTF-8. If the board's symbols look garbled, or you pipe a prompt
  in with accents or other scripts, first run
  `$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)` in that PowerShell window.
- **`~` in paths.** Bonsai expands `~` in `-f` and `-o` itself, so `-o ~/Bonsai/answer.md` works in CMD and
  PowerShell too.
- **Signing out.** The logout lines Bonsai prints are PowerShell.
- **A refused job.** A job runs in a temporary folder inside your home folder. If your home folder holds a
  `CLAUDE.md`, `AGENTS.md` or `.git`, Bonsai refuses the job, because the CLIs would read it. The message
  says what to move.

## Not working on Windows yet

- Codex logins saved in the Windows Credential Manager show as signed out. Sign in with Codex's default
  file storage instead.
- Running Bonsai from inside a Codex session's Windows sandbox is untested.
- WSL 2 is untested. Inside WSL, install the Linux versions of Python, Claude Code and Codex, and follow
  SETUP.md as on a Mac.
