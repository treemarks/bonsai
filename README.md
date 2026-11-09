<img src="docs/images/bonsai.svg" alt="A little green bonsai in a terracotta pot" width="120">

# Bonsai — a little Treemarks

[Get started](#get-started) · [Usage](docs/USAGE.md) · [Accounts & data](docs/ACCOUNTS.md) · [Help](https://github.com/treemarks/bonsai/issues)

Bonsai is a **model and account router** that helps you make better use of the AI accounts you
already have. Most of us default to personal logins and don't take advantage of Stanford's
[Claude for Education](https://uit.stanford.edu/service/claude) and
[ChatGPT Edu](https://uit.stanford.edu/service/openai-chatgpt-edu).

After setup, you can ask in natural language to **have models debate a question**, **give your
work an adversarial pass**, or **send a request to another account**. Here's what that looks like.

### 1. Have the models debate a question

<img src="docs/images/use-case-1-mars.png" alt="Example request: claude, when do you think we're gonna get to Mars? can you debate this with ChatGPT? In a real Bonsai trial, Codex forecast 2042, Claude chose 2044 and questioned return readiness, and Codex became less confident about its deadline." width="640">

[Read the Mars exchange](docs/MARS-DEBATE.md), condensed from a real trial. These are forecasts, not mission dates.

### 2. Ask for an adversarial pass

<img src="docs/images/use-case-2-homework.png" alt="hey thanks for the help on my LCA homework, can u send it to chatgpt for an adversarial pass before we turn it in? The agent asks ChatGPT to challenge the reasoning and point out what needs another look." width="640">

### 3. Use another account

<img src="docs/images/use-case-3-routing.png" alt="can you route this conversation to my Stanford Claude? The agent sends the relevant context and next question to that account, then brings the reply back here." width="640">

## Get started

**Download [SETUP.md](https://raw.githubusercontent.com/treemarks/bonsai/main/SETUP.md), drop it into Claude, and say “help me set up Bonsai.”**

You'll be prompted to sign in to the institution accounts you want to use. Claude Code can run
setup on your Mac; a regular Claude chat can walk you through it.

Your original chat can still see routed tasks and replies. For protected information, use your
institution's approved tools directly. [More about accounts and data](docs/ACCOUNTS.md).

---

Made by [Treemarks](https://treemarks.ai). Independent of Stanford, Anthropic and OpenAI.
[Manual setup](docs/INSTALL.md) · [Development](docs/DEVELOPMENT.md) · [MIT license](LICENSE)
