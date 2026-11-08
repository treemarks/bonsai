# Bonsai — a little Treemarks

**One board for every AI login on your Mac — your personal Claude or ChatGPT and your
institution's seats — and one command that runs a job on the one you name.**

Stanford (the worked example here) gives students and staff Claude for Education and ChatGPT Edu
seats under the university's agreements with Anthropic and OpenAI. Most students also have a
personal account. Bonsai lets several sign-ins live on one Mac and work together:

- every login is its own saved CLI sign-in, kept apart (a **pool**);
- one board shows each login's room left this week and this five-hour window, when each resets,
  and your Mac's own load on the row beneath;
- a job is **routed**: `bonsai job stanford-codex ...` runs it on that seat, `bonsai job astra ...`
  picks the personal login with the most perishable room, `bonsai pass astra -f draft.md` has a
  second model try to break your draft;
- Claude Code learns the words: *"route this to my Stanford Codex"*, *"ask Sol"*, *"adversarial
  pass from Astra on this"* become the right command, run under the login you named.

Bonsai is the one-machine version of the pool router that schedules [Treemarks](https://treemarks.ai)'
grading fleet. Same board, same routing rule, no fleet.

> **The one thing to know.** When you ask a chat (Claude Code or Codex, on your own account) to
> run a job on your institution account, that chat can see the task and the results, and handles
> them under its own account and settings. Choosing the institution account for the job does not
> give the chat the institution's protections. So only route work that is allowed in the chat you
> started from: Bonsai allows ordinary personal work, including a family project with names in it,
> and you remain responsible for what you share. For protected information — confidential student
> records, research interviews, health records, anything your institution classes Moderate or High
> Risk — open a tool and account your institution approves for that information yourself, outside
> the chat; an institution login alone does not establish approval (at Stanford, for example,
> Claude is not approved for PHI at all; the AI API Gateway is). Bonsai does not check files for
> protected information: it refuses a job that declares `--data moderate|high|phi` before it reads a
> file, wherever it is run from; undeclared data is routed. It prints this notice before your first
> job, at `install-skill`, and when you add an institution account, and a one-line reminder on every
> chat-driven job to one.

Bonsai is an independent Treemarks project. It is not endorsed by Stanford, Anthropic or OpenAI;
Stanford appears here as an example institutional configuration, with links to its public pages.

## Install

Bonsai is one Python file with no dependencies beyond what a Mac already has (Apple's
`python3`, 3.9 or newer) and the two CLIs it drives. **[SETUP.md](SETUP.md)** is the complete
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

## Sign your institution seats in as their own pools

```bash
bonsai login you@stanford.edu --claude --institution    # opens the Claude sign-in page; pick the Stanford org
bonsai login you@stanford.edu --codex  --institution    # opens the ChatGPT sign-in; pick the Stanford workspace
```

The first `--institution` prints the notice above and, in a Terminal, asks you to type
`I understand` (typed into that Terminal window, then Return); the date is recorded. That is the
only time it asks: the second login, later logins and the first job do not repeat it (only a new
version of the notice prints again, once, without the prompt). If an agent
runs the setup for you, the notice reaches the agent's output, not your eyes: the skill tells the
agent to relay it before its first route, and HANDOFF.md tells you to expect that. Each login lands
in `~/.claude-pools/you@stanford.edu` or
`~/.codex-pools/you@stanford.edu`, the directories the CLIs call `CLAUDE_CONFIG_DIR` and
`CODEX_HOME`. Nothing is copied between pools; Claude's credential stays in your login Keychain,
Codex's in its own `auth.json`, exactly where the CLIs put them. The institution flag is recorded
per provider, when that sign-in completes; it is your declaration (Bonsai cannot read your
institution's contracts), and it marks the seat `⌂` on the board so that `auto` routing uses it
only for `--kind sensitive` work and never for everyday jobs. `⌂` means "marked institution by
you": a successful sign-in does not verify that you picked the university workspace, and neither
proves approval for any data; check the account and organization `bonsai doctor` shows. `--name
<label>` changes the label
(default `stanford` for a stanford.edu address, else the domain). A second personal login is
`bonsai login other@gmail.com --claude` with no flag.

After each sign-in Bonsai prints what actually signed in (for Claude the e-mail, organization and
plan from `claude auth status`; for Codex the e-mail, plan type such as `edu_pro`, and the last
four characters of the ChatGPT account id, which is the workspace) and refuses to record a sign-in
whose e-mail is not the one asked for, printing the exact sign-out line instead. One e-mail with
two ChatGPT workspaces is two pools: `--pool stanford-pro --name stanford-pro` for the second;
two pools showing one workspace id are the same workspace signed in twice. Logins are named
exactly (`stanford`, `stanford-pro`, or the e-mail), never by prefix, and routing words (`auto`,
`codex`, `openai`, `astra`, ...) are refused as pool names. `--device-auth` (Codex) uses the
one-time-code sign-in when the browser callback on port 1455 cannot complete.

## The board

```
bonsai gauge          # live; q quits
bonsai gauge --once   # one frame, for a script or a screenshot
```

```
ACCOUNTS   ant = Claude   oai = Codex   ⌂ = institution seat           as of 2m ago   refresh in 3m
  LOGIN       VIA                          %LEFT RESET   5H    RESET   PLAN     STATE
  ⌂stanford   oai ████████████████████░░░░ 83%   2d13h   100%  ·       edu      ok
  ⌂stanford   ant ························ ·     ·       ·     ·       enterpr  signed-in
   personal   oai ███████████████░░░░░░░░░ 62%   6d4h    100%  ·       plus     ok
   personal   ant ························ ·     ·       ·     ·       pro      signed-in

MACHINE    ACTIVITY                 LOAD   MEM%   SWAP   BATT      UP
  air        job×1 pass:astra        0.8    61%    1GB    84% batt  3d2h    last: astra ok 14m ago
```

Rows sort by the weekly reset that comes soonest, because that room is the most perishable:
capacity unspent at the reset is gone. The bar and `%LEFT` are the weekly window; `5H` is the
five-hour one. Green, yellow and red turn at 50% and 20% left. Codex rows carry numbers (from
Codex itself); Claude rows read `signed-in` with the account's plan unless you turn the Claude
usage read on (below). `LOAD` is the one-minute load average per core, not a CPU percentage.
`STATE` says when a login needs attention: `re-login` (the sign-in lapsed), `locked` /
`keychain-timeout` (with Claude reads on: the credential could not be read in this shell — over
SSH, or the allow dialog went unanswered), `no-plan`, `limited` (the provider has stopped calls
until the reset), `offline`, `cli-missing`, `unknown`.

The board probes each login at most once per interval (default five minutes, floor three), under
a lock so a second window or a script waits for the first probe instead of adding its own, and
renders from the cache in between. `--fresh` probes now.

## Routing

```bash
bonsai route                  # both providers: the order for general work and for sensitive work
bonsai route codex --fresh    # one provider, probe now
```

Two kinds of work, two orders:

- **general** (the default) — personal logins only, soonest weekly reset first. A login under 10%
  room is held; a login the provider has stopped (`limited`) is out until its reset; a login
  whose usage could not be read is not ranked. An institution seat never carries general work by
  `auto`; name it if you mean it.
- **sensitive** — institution seats only, never a personal login, even a named one. Read the box
  at the top first: `sensitive` is about *purpose* (university work goes to the university
  account); it keeps the job off personal logins and does nothing about what the chat that sent
  it can see, which is why declared protected data (`--data moderate|high|phi`) is refused.

A **named** target (`stanford-codex`) means that seat, for general work. When every eligible login
is held, Bonsai stops and says when the soonest window resets; it never moves a job to another
login to get around a limit. With Claude usage reads off and several signed-in Claude logins,
`auto` takes the CLI's own login (`default`), then the first by name, and says so; name one with
`--pool` or turn the read on to rank them.

Which default is right for Stanford work? Stanford's own pages say the seat is for its teaching
and research mission, including ordinary low-risk work, so a student doing coursework may want
the seat first: `bonsai config --set default_kind=sensitive` makes `auto` prefer institution
seats, and `personal-codex` / `personal-claude` still name the personal login when you mean it.

### Jobs

```bash
bonsai job stanford-codex -f notes.md -o answer.md "Summarize the themes in these interview notes"
bonsai job astra -o out.md "Is this argument sound? <paste>"   # alias picks the provider; auto picks the login
bonsai job sol@stanford -f draft.md -o review.md "..."         # alias on a named login
bonsai job codex --effort high -o plan.md - < brief.md          # stdin
bonsai job codex -o out.md -- "-starts with a dash"             # -- before a prompt that starts with -
```

Targets: `claude` / `codex` (auto login), `<login>-claude` / `<login>-codex` (`stanford-codex`,
`personal-claude`), a model alias (`astra`, `sol`, `opus`, `sonnet`, `haiku`; edit them with
`bonsai config --set 'models.astra=["codex","gpt-6-astra"]'`), or `<alias>@<login>`. The
company, the product and the CLI name the same seat: `stanford-openai`, `stanford-chatgpt` and
`stanford-gpt` are `stanford-codex`; `stanford-anthropic` is `stanford-claude`. A login signed in
under its own `--pool` name (a second workspace of one account, say `stanford-pro`) is
`stanford-pro-codex`.

`-f` puts each file into the prompt as a JSON object (name and content; UTF-8 text only, 400 KB
each, 1.6 MB in all). `-o` writes the model's final message to a file, atomically, and leaves the
old file alone if the job fails. `--cd` sets the working directory the model is told about.
`--data low|moderate|high|phi|restricted` says what the material is: `moderate`, `high` and `phi`
are refused before any file is read, wherever the command runs from (a Terminal is no more a sign
of approval than a chat is; the refusal says what to do instead); `restricted` (payment-card data,
CUI, export-controlled material: approved for no AI tool) is refused everywhere; `low` and no
declaration route. `--dry-run` prints the command and spends nothing.

**What a job can do on your machine.** A Codex job runs `codex exec` in Codex's read-only
sandbox, signed in with ChatGPT (`forced_login_method="chatgpt"`, never an API key). A Claude job
runs `claude -p` with every tool switched off (`--tools ""`, MCP servers excluded, hooks disabled,
no session saved): the model answers from the prompt and the `-f` files and has no way to read,
write, run or fetch anything. These are the CLIs' own capability switches, not a sandbox Bonsai
built; the CLIs' configuration, logs and network behaviour are theirs. Bonsai itself phones nobody
except, for Codex usage, Codex's own app-server on your machine.

### Adversarial passes

```bash
bonsai pass astra -f PLAN.md -o PLAN.pass-astra.md --brief "the budget section"
bonsai pass opus@stanford -f thesis_ch3.md -o ch3.pass.md
```

A pass asks a second model to break the material: numbered findings, most serious first, each
with the quoted claim, why it fails, a confidence and what would settle it; then what held; then a
one-paragraph verdict. No praise, no rewriting. The brief and the material travel as a JSON object
so neither can pretend to be the instructions. Use a different model family from the one that
wrote the draft.

### Any command, under a login

```bash
bonsai run --pool stanford -- codex          # an interactive Codex session on that seat, in this Terminal
bonsai run --pool stanford -- claude         # the same for Claude Code
bonsai run --pool auto --provider claude -- claude -p "..."
```

Everything after `--` belongs to the command; Bonsai's own flags go before it. A wrapper that is
not `claude` or `codex` itself needs `--provider`. **This is a weak workaround, not a protection:**
it keeps the work in a seat-signed session only if a person types there; if a chat launches it,
the output comes back to the chat.

## Teach Claude Code the words

```bash
bonsai install-skill
```

This prints the notice, then writes `~/.claude/skills/bonsai-route/SKILL.md`. It never overwrites
an edited one: then it says **NOT UPDATED**, exits 2, and leaves the new version beside it as
`SKILL.md.new` for you to review and move over (`bonsai doctor` says whether the installed skill
matches this version). From then on, in any Claude Code session:

> route this to my stanford codex (or: my stanford chatgpt, my stanford openai) · send it to my
> stanford claude (my stanford anthropic) · ask astra whether the proof holds · call an
> adversarial pass from sol on this draft · use my personal account

...and Claude Code runs the matching `bonsai` command, writes the result to a file beside the
material, and reads it back to you. The skill carries the rule from the box at the top: before its
first route in a session it tells you, in its reply, that a routed job is still seen by the chat;
told the material is protected (it treats "class grades", "patient records", "confidential
interviews" as that, and asks when a description is ambiguous), it does not route, does not open
the files, and says to use an approved tool and account yourself. It does not detect protected
information; undeclared data is routed. Read the file once — it is what your agent will do with the
words — and if you will use Bonsai with university data, someone in your unit should review it
first: Stanford asks that of repeatable AI workflows and skills. Codex users: the same table works
as a section of your `AGENTS.md`, with the same caveat.

## What Bonsai reads, and what it never does

- **Identity.** Claude: `claude auth status --json` under each pool — Claude Code answers with the
  account, organization and plan; Bonsai reads no credential. Codex: the e-mail claim of the
  stored id token, as a label.
- **Codex usage** comes from Codex's own `app-server` (`account/rateLimits/read`), started under
  the pool's `CODEX_HOME`; Codex holds and refreshes the credential and Bonsai never sees it.
- **Claude usage is off by default.** Anthropic's published terms say OAuth sign-in on Free, Pro,
  Max and Ultra plans is for Claude Code and Anthropic's own apps, and Claude Code offers no
  command that reports usage. If you turn the read on (`bonsai config --set usage_reads.claude=true`),
  Bonsai reads the token Claude Code stored (macOS asks you to allow that once per login), asks
  Anthropic's usage surface under its own name (`User-Agent: bonsai/<version>`; the same surface
  Claude Code's `/usage` screen reads), once per interval, and never follows a redirect with the
  token. Whether that is ordinary use of your login is your call; the default is no.
- **What is stored**, all of it owner-only (0600) under `~/.local/state/bonsai/`: the last probe
  (account e-mail, plan and organization labels, percentages, reset times), a history of
  percentages, and a job ledger (labels, pool, exit codes, seconds). No token, prompt or output.
  Config values you set are yours and are printed back by `bonsai config`; unknown keys are refused.
  The CLIs keep their own session transcripts under their config directories (a Claude job runs
  with `--no-session-persistence`); job output files go where `-o` says.
- **Jobs run the official CLIs.** Every job is `claude` or `codex` itself, started with that
  pool's config directory and an environment that carries only the basics (PATH, HOME, locale,
  proxy settings): no parent session marks, no API keys or tokens, no provider endpoint overrides,
  so a job can only bill the login it was given through the CLI's own sign-in.
- **No sharing.** A pool is your own sign-in on your own machine. Don't copy a pool directory to
  another person or machine; sign in there instead. Each login stays subject to its own purpose
  and its own limits; Bonsai never rotates to another login to get past a stop.

## Terms of use

Each login is yours under its provider's terms, and an institution seat is yours under your
institution's agreement as well. Read them; Bonsai cannot read them for you.

- Anthropic: [Consumer Terms](https://www.anthropic.com/legal/consumer-terms) (personal plans),
  [Commercial Terms](https://www.anthropic.com/legal/commercial-terms) (Team, Enterprise and
  Education organizations), [Usage Policy](https://www.anthropic.com/legal/aup), and Claude
  Code's [legal and compliance](https://code.claude.com/docs/en/legal-and-compliance) and
  [data usage](https://code.claude.com/docs/en/data-usage) pages.
- OpenAI: [Terms of Use](https://openai.com/policies/row-terms-of-use/) (personal plans),
  [Services Agreement](https://openai.com/policies/services-agreement/) (Enterprise, Business,
  Edu), [Usage Policies](https://openai.com/policies/usage-policies), and
  [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540).
- Stanford: [Claude for Education](https://uit.stanford.edu/service/claude),
  [ChatGPT Edu](https://uit.stanford.edu/service/openai-chatgpt-edu),
  [the June 30 notice](https://uit.stanford.edu/news/new-ai-tools-stanford-arrive-june-30),
  [Data risk classifications](https://uit.stanford.edu/guide/riskclassifications),
  [Responsible agentic AI](https://uit.stanford.edu/security/agenticai), and the
  [Computer and Network Usage Policy](https://adminguide.stanford.edu/chapters/computing/computer-and-network-usage/computer-and-network-usage-policy).

What those pages say, as read on 2026-11-08 (check them; they change): the institution
workspaces come with no-training commitments for ordinary use; they do not promise zero retention
or local processing. Stanford approves ChatGPT Edu for Low, Moderate and High Risk data and PHI,
and Claude Code for Low to High with PHI only through Stanford's AI API Gateway; no AI tool is
approved for payment-card data, CUI or export-controlled material; and connectors, plugins and
skills need their own review. Stanford approves tools, not every configuration of them. The honest
sentence about a routed Bonsai job is: the same account and tool Stanford approved, driven
headless, with the task written and the answer read by whatever asked for it.

## Development

```bash
/usr/bin/python3 -m unittest discover -s tests                        # stock macOS python, no network, no real logins
/usr/bin/python3 -m unittest review/test_astra_regressions.py         # the adversarial review's 51 acceptance tests
BONSAI_POOLS_HOME=/tmp/fakehome BONSAI_STATE=/tmp/bonsai-state ./bonsai gauge --once --no-color
```

`BONSAI_POOLS_HOME` points discovery at another home (the tests use a synthetic one);
`BONSAI_STATE` and `BONSAI_CONFIG` move the cache and config. Standard library only; one file.
`review/` holds the terms digest, the briefs of the five adversarial passes this release was
checked against, and the tests they produced. Bonsai is MIT-licensed. It began as a handoff for a
friend with a MacBook Air, a personal Claude Pro and two Stanford seats, who wanted the Treemarks
pool gauge in miniature.
