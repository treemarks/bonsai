<img src="docs/images/bonsai.svg" alt="A little green bonsai in a terracotta pot" width="120">

# Bonsai — a little Treemarks

[Get started](#get-started) · [Usage](docs/USAGE.md) · [Accounts & data](docs/ACCOUNTS.md) · [Help](https://github.com/treemarks/bonsai/issues)

Bonsai is a **model and account router** that helps you make better use of the AI accounts you
already have. Most of us default to personal logins and don't take advantage of Stanford's
[Claude for Education](https://uit.stanford.edu/service/claude) and
[ChatGPT Edu](https://uit.stanford.edu/service/openai-chatgpt-edu).

After setup, you can prompt in natural language to **have models debate a question**, **give your
work an adversarial pass**, **turn a file into a plan**, or **reword something verbose**.
Here's what that looks like.

### 1. Have the models debate a question

<img src="docs/images/use-case-1-mars-blog.png" alt="You ask Claude when humanity will get to Mars and to debate ChatGPT. Claude picks 2044, Codex picks 2042, and Claude challenges return readiness. Claude says 2042 is too soon before proving people can get home. You conclude: ok i pick 2043. please update my blog post!" width="640">

[Adapted from a recorded Mars debate](docs/MARS-DEBATE.md).

### 2. Ask for an adversarial pass

<img src="docs/images/use-case-2-homework-compact.png" alt="Illustrative LCA homework review: ChatGPT spots that Claude counted combustion instead of the total fuel cycle. A follow-up correction returns the revised homework as an attachment." width="640">

### 3. Turn a file into a plan

<img src="docs/images/use-case-3-architecture-compact.png" alt="Illustrative design handoff: Claude provides a design-specification file. You ask ChatGPT for architectural plans based on it, and the reply includes a document with a concept-plan preview." width="640">

### 4. Reword something verbose

<img src="docs/images/use-case-4-reword-compact.png" alt="Hypothetical conversation: Claude’s garden invitation adds annual-event history, past locations, organizers and logistics in progressively smaller type. ChatGPT condenses it to the time, location, welcome and tools." width="640">

<img src="docs/images/bonsai-gauge.png" alt="The Bonsai gauge: personal and Stanford logins for ChatGPT and Claude, with how much each has left and when it resets, and this Mac's load; sample figures." width="760">

`bonsai gauge`, with sample figures. [How to read it](docs/USAGE.md#the-board).

## Get started

**Download [SETUP.md](https://raw.githubusercontent.com/treemarks/bonsai/main/SETUP.md), drop it into Claude, and say “help me set up Bonsai.”**

You'll be prompted to sign in to the institution accounts you want to use. Claude Code can run
setup on your Mac; a regular Claude chat can walk you through it.

Your original chat can still see routed tasks and replies. For protected information, use your
institution's approved tools directly. [More about accounts and data](docs/ACCOUNTS.md).

**_Currently only tested on Mac OS. Looking for testers for Windows, please let us know your results if you try it!_**

---

Made by [Treemarks](https://treemarks.ai). Not affiliated with or endorsed by Stanford, Anthropic or OpenAI.
Claude and ChatGPT are trademarks of their respective owners.
[Manual setup](docs/INSTALL.md) · [Development](docs/DEVELOPMENT.md) · [MIT license](LICENSE)
