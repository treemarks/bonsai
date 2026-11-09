# Using Bonsai

[Home](../README.md) · [Setup](../SETUP.md) · [Usage](USAGE.md) · [Accounts & data](ACCOUNTS.md)

After setup you work in your agent: Claude Code (the **Code** tab of the Claude desktop app, or
`claude` in Terminal) or Codex. Ask in words; the skill turns them into the `bonsai` command:

| You say | Bonsai runs |
|---|---|
| "route this to my stanford codex" | `bonsai job stanford-codex -f notes.md -o ~/Bonsai/notes.md "..."` |
| "ask astra whether the proof holds" | `bonsai job astra ...`, on the login `auto` picks |
| "adversarial pass from sol on this draft" | `bonsai pass sol -f draft.md -o ~/Bonsai/draft.pass.md` |
| "debate this with sol", "have chatgpt argue with you about this" | [a debate](#a-debate) |
| "have the other model critique this" | `bonsai pass other -f draft.md -o ~/Bonsai/draft.pass.md` (Claude asks a ChatGPT model, Codex asks Claude) |
| "show my board" | `bonsai gauge --once` |
| "update bonsai" | `bonsai update --dry-run`, then `--yes --to <commit>` on your word |

Answers are saved under `~/Bonsai/`. The chat says *done, saved to* the file, with a two- or
three-line summary, and reads you the whole answer only when you ask.

## The board

<img src="images/bonsai-gauge.png" alt="The Bonsai gauge with sample figures: personal and Stanford logins for ChatGPT and Claude, and this Mac's load." width="760">

```
bonsai gauge          # live; Ctrl-C quits
bonsai gauge --once   # one frame, for a script or a screenshot
```

Each row is a login, coloured by provider (orange Anthropic, purple OpenAI, named on the top row; without colour a
`VIA` column says `ant` or `oai`). Rows sort by the weekly reset that comes soonest, because that room is the most
perishable: capacity unspent at the reset is gone. The bar and `%LEFT` are the weekly window; `5H` is the five-hour
one; green, yellow and red turn at 50% and 20% left. `PLAN` is the account's plan. `PROMO` counts the usage resets
OpenAI has granted a ChatGPT login (`2x`: two). Codex rows carry numbers from Codex itself. Claude rows show numbers as
last reported by Claude Code: each Claude job reports how much of the week is used, and when you open the board a
login whose last reading is older than 15 minutes is asked with Claude Code's `/usage` (no model call). A Claude row
with no reading yet shows `unavailable`: unknown, never full. A login that needs attention shows it where its bar
would be: `re-login` (the sign-in lapsed), `limited` (stopped until the reset), `no-login`, `unknown`. A provider you
never signed in is left off. The board probes each login at most once per interval (default five minutes), and
`--fresh` probes now.

The `MACHINE` line is this Mac: `MODEL` is what it is running (a Bonsai job, or a model Ollama has loaded, or a
local model process such as Whisper or llama.cpp), then CPU, GPU, memory, swap, disk and battery.

## Which login a job takes

A job goes to the login you name (`stanford-codex`, `personal-claude`), or, with `auto`, to the
one a single setting picks:

```bash
bonsai config --set prefer=soonest       # the default: whichever login's room resets first
bonsai config --set prefer=institution   # the institution seats first, then the rest
bonsai config --set prefer=personal      # personal logins first, the seats when those wait
```

Stanford's own pages say its seats are for the university's teaching and research mission,
ordinary low-risk work included, so a student doing coursework may want `prefer=institution`.
`personal-codex` and `personal-claude` still name the personal login when you mean it.

Room left at a reset is lost, so `auto` passes over a login only while its tighter window (the
week or the five hours, whichever has less left) is under 10% early in that window; the floor
shrinks to nothing as that window's reset nears. Before a job goes to a Claude login whose
reading is older than 15 minutes, Bonsai asks Claude Code's `/usage` first, so a job does not walk
into a login that has run out; a login running low or out is said in one line. Naming a login spends what it has above zero. A
login with nothing left, one the provider has stopped (`limited`) and one that is signed out or
signed in as another account are never used, named or not; Bonsai never moves a job to another
login to get around a stop.
`bonsai job codex --dry-run "..."` says which login a job would take and why, and spends nothing.

## Jobs

```bash
bonsai job stanford-codex -f notes.md -o ~/Bonsai/themes.md "Summarize the themes in these notes"
bonsai job astra -o ~/Bonsai/argument.md "Is this argument sound? <paste>"   # an alias picks the provider
bonsai job sol@stanford -f draft.md -o ~/Bonsai/review.md "..."             # an alias on a named login
bonsai job codex --effort high -o ~/Bonsai/plan.md - < brief.md              # the task on stdin
```

Targets: `claude` / `codex` (auto login), `<login>-claude` / `<login>-codex` (`stanford-codex`,
`personal-claude`), a model alias (`astra`, `sol`, `opus`, `sonnet`, `haiku`; edit them with
`bonsai config --set 'models.astra=["codex","gpt-6-astra"]'`), or `<alias>@<login>`. The
company, the product and the CLI name the same seat: `stanford-openai`, `stanford-chatgpt` and
`stanford-gpt` are `stanford-codex`; `stanford-anthropic` is `stanford-claude`. A second
workspace signed in under its own `--pool` name (say `stanford-pro`) is `stanford-pro-codex`.

`-f` puts each file into the task as a JSON object (UTF-8 text only, 400 KB each, 1.6 MB in all).
`-o` writes the model's final message to a file, only when the job succeeds (until then it waits in a
private file). `--data low|moderate|high|phi|restricted` says what the material is: `moderate`, `high`
and `phi` are refused before any file is read, wherever the command runs from; `restricted`
(payment-card data, CUI, export-controlled material) is refused everywhere; `low` and no
declaration route. `--dry-run` says which login and prints the command, and spends nothing.

A job prints its id when it starts and stops itself after 20 minutes (`--timeout MINUTES`, or
`bonsai config --set job_timeout=MINUTES`; 0 for no limit). `bonsai jobs` shows how long a running
job has run and how each one ended (ok, failed, timeout, cancelled); `bonsai cancel <id>` stops one
and everything it started. Nothing is published on a timeout or a cancel. A job's own messages go
to a private file, named in one line if it fails; a job that stops because its login ran out of
usage says so.

**What a job can do: answer, nothing else.** It runs in an empty private folder with no web, no
shell and no tools. A Codex job runs `codex exec` in the read-only sandbox with the shell tool
off, keeps no session, ignores your Codex config and rules, and is signed in with ChatGPT, never
an API key. A Claude job runs `claude -p` in safe mode (your CLAUDE.md, skills, plugins, hooks and
servers stay out) with every tool denied and at most three turns. Codex's read-only sandbox blocks
writes, not reads, which is why the folder is empty. With those switches, files are meant to reach
a job only through `-f`; what each CLI version can still read has not been measured. These are the
CLIs' own switches, not a sandbox Bonsai built.

## Adversarial passes

```bash
bonsai pass astra -f PLAN.md -o ~/Bonsai/PLAN.pass-astra.md --brief "the budget section"
bonsai pass opus@stanford -f thesis_ch3.md -o ~/Bonsai/ch3.pass.md
```

A pass asks a second model to break the material: numbered findings, most serious first, each
with the quoted claim, why it fails, a confidence and what would settle it; then what held; then a
one-paragraph verdict. No praise, no rewriting. The prompt marks the material as something to
critique, not instructions to follow; a determined document can still try to steer the model. Use a
different model family from the one that wrote the draft.

To get a corrected draft after the review, ask your agent for a follow-up job with the draft and
the findings; `-o` saves the model's reply as a file. For a design handoff, send the specification
in a job and ask for a concept plan in Markdown, HTML or SVG; HTML and SVG can carry a visual
preview of the plan. The README's studio rendering is illustrative artwork; a job has no tools, so it
makes no pictures itself.

## A debate

Asked for a debate, the chat writes its case into `~/Bonsai/debate-<topic>.md`. Bonsai sends that
transcript to the model you named (`sol`, `astra` or any ChatGPT model, on the login `prefer`
picks) for a critique (`bonsai pass <model> --round N`), the chat answers in the same file, and so
on. Two critique rounds by default: the second tests the answers to the first, and a third mostly
repeats them. It stops early when a critique finds no new objection; ask for three or four rounds
if you want them (four is the most). At the end the chat shows what it takes from the debate and
what it rejects, and a two-line summary. [The Mars exchange](MARS-DEBATE.md) is one.

## Teach your agent the words

```bash
bonsai install-skill
```

This writes the skill for each agent on your Mac: `~/.claude/skills/bonsai-route/SKILL.md` for
Claude Code and `~/.agents/skills/bonsai-route/SKILL.md` for Codex; quit and reopen your agent to
load it. It replaces a skill you have not edited and keeps the old one as `SKILL.md.prev`. An edited one it
leaves alone: it says **NOT UPDATED** and puts the new version beside it as `SKILL.md.new` for you
to review and move over. `bonsai doctor` says whether the installed skill matches this version.

The skill carries the rule from [Accounts & data](ACCOUNTS.md): before its first route in a
session it tells you, in its reply, that a routed job is still seen by the chat; told the
material is protected (it treats "class grades", "patient records", "confidential interviews" as
that, and asks when a description is ambiguous), it does not route, does not open the files, and
says to use an approved tool and account yourself. It does not detect protected information;
undeclared data is routed. Jobs have no web, so the skill says so before routing a task that asks
to look something up. Read the file once: it is what your agent will do with the words. If you
will use Bonsai with university data, someone in your unit should review it
first; Stanford asks that of
repeatable AI workflows and skills.

From Codex: Codex runs commands in a sandbox with no network and no Keychain, so a job cannot start
inside it; Bonsai stops with one line, and you approve running bonsai outside the sandbox when Codex
asks.

## Updating

`bonsai update` fetches, prints the list of new commits, and merges only when you type yes
(`--yes` answers for you; `--dry-run` stops after the list; `--to <commit>` stops if the published
commit moved since you read the list). Nothing new runs before you agree.
Then run `bonsai install-skill` if it says so.
