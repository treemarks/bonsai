# Manual installation

[Home](../README.md) · [Setup](../SETUP.md) · [Usage](USAGE.md) · [Accounts & data](ACCOUNTS.md)

Bonsai is one Python file with no dependencies beyond what a Mac already has (Apple's
`python3`, 3.9 or newer) and the two CLIs it drives. **[SETUP.md](../SETUP.md)** is the complete
walk for a Mac with nothing on it, written so a chat or a coding agent can follow it; the short
form:

```bash
xcode-select --install                                  # git and python3, if `git --version` fails
curl -fsSL https://claude.ai/install.sh | bash          # Claude Code (`claude`)
# Codex: SETUP.md step 3 (the release binary; no Homebrew or Node needed; or `brew install codex`)
git clone https://github.com/treemarks/bonsai ~/code/bonsai
mkdir -p ~/.local/bin && ln -sf ~/code/bonsai/bonsai ~/.local/bin/bonsai
touch ~/.zshrc; grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' ~/.zshrc || printf '%s\n' 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
bonsai install-skill                                    # so a new chat knows "ask ChatGPT ..."
bonsai doctor
```

`bonsai doctor` lists what is installed and which logins it can see, says what to do next, and
exits non-zero until the tools are there. Your existing `~/.claude` and `~/.codex` sign-ins show
up as the pool called `default`, labelled **personal** on the board. An older copy in
`~/code/bonsai` moves forward with `bonsai update`; SETUP step 4 has the four lines for a copy
from before version 0.3.

On Windows, see [WINDOWS.md](WINDOWS.md).
