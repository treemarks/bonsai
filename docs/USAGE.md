# Using Bonsai

[Home](../README.md) · [Setup](../SETUP.md) · [Usage](USAGE.md) · [Accounts & data](ACCOUNTS.md)

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
usage read on ([details](ACCOUNTS.md#what-bonsai-reads-and-what-it-never-does)). `LOAD` is the one-minute load average per core, not a CPU percentage.
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
- **sensitive** — institution seats only, never a personal login, even a named one. Read [Accounts & data](ACCOUNTS.md) first: `sensitive` is about *purpose* (university work goes to the university
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
material, and reads it back to you. The skill carries the rule from [Accounts & data](ACCOUNTS.md): before its
first route in a session it tells you, in its reply, that a routed job is still seen by the chat;
told the material is protected (it treats "class grades", "patient records", "confidential
interviews" as that, and asks when a description is ambiguous), it does not route, does not open
the files, and says to use an approved tool and account yourself. It does not detect protected
information; undeclared data is routed. Read the file once — it is what your agent will do with the
words — and if you will use Bonsai with university data, someone in your unit should review it
first: Stanford asks that of repeatable AI workflows and skills. Codex users: the same table works
as a section of your `AGENTS.md`, with the same caveat.

