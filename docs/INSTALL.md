# Manual installation

[Home](../README.md) · [Setup](../SETUP.md) · [Usage](USAGE.md) · [Accounts & data](ACCOUNTS.md)

## Install

Bonsai is one Python file with no dependencies beyond what a Mac already has (Apple's
`python3`, 3.9 or newer) and the two CLIs it drives. **[SETUP.md](../SETUP.md)** is the complete
walk for a Mac with nothing on it, written so a coding agent can follow it; the short form:

```bash
xcode-select --install                                  # git and python3, if `git --version` fails
curl -fsSL https://claude.ai/install.sh | bash          # Claude Code (`claude`)
# Codex: SETUP.md §3 (the release binary; no Homebrew or Node needed; or `brew install codex`)
git clone https://github.com/treemarks/bonsai ~/code/bonsai
mkdir -p ~/.local/bin && ln -sf ~/code/bonsai/bonsai ~/.local/bin/bonsai
touch ~/.zshrc; grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' ~/.zshrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
bonsai doctor
```

`bonsai doctor` lists what is installed and which logins it can see, prints the install line for
anything missing, and exits non-zero until the tools are there. Your existing `~/.claude` and
`~/.codex` sign-ins show up as the pool called `default`, labelled **personal** on the board.
Windows: the platform-specific parts are kept apart and the Windows branches exist; the Windows
release still needs work and a real run (SETUP.md's last section).

