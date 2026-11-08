# Bonsai — a little Treemarks

**Keep your personal Claude or ChatGPT for everyday work. Send the work that touches
protected data to your institution's seat. See both on one board.**

Stanford gives students and staff Claude and ChatGPT seats under Stanford's own agreements
with Anthropic and OpenAI: your prompts stay out of model training, and the data-handling terms
are the university's, not a consumer account's. Most students also have a personal account they
work in all day. Bonsai is the small tool that lets the two cooperate on one Mac:

- every login is its own saved CLI sign-in, kept apart (a **pool**);
- one board shows how much room each login has left this week and this five-hour window, and
  when each resets, with your Mac's own load on the row beneath;
- a job is **routed**: `bonsai job stanford-codex ...` runs it on that seat, `bonsai job astra ...`
  picks the login with the most perishable room, and `bonsai pass astra -f draft.md` has a second
  model try to break your draft;
- Claude Code learns the words: *"route this to my Stanford Codex"*, *"ask Sol"*, *"adversarial
  pass from Astra on this"* become the right command, run under the right login, never the one
  the chat itself is signed into.

Bonsai is the one-machine version of the pool router that runs [Treemarks](https://treemarks.ai)'
grading fleet, which spreads work across a dozen Claude and Codex logins and institution seats.
Same rules, no fleet: one Mac, your logins, your data stays where it belongs.

> **Your institution's rules come first.** Bonsai routes; it does not decide what data may go
> where. Stanford classifies data as Low, Moderate or High Risk and publishes which AI tools are
> approved for which
> ([Stanford UIT: AI tools and data risk](https://uit.stanford.edu/security/ai)). Use the seat
> for what your institution provisioned it for; keep each login's terms of use (links below);
> and when in doubt, ask your department's IT or privacy office before the data leaves your hands.

## Install

Bonsai is one Python file with no dependencies beyond what a Mac already has (Apple's
`python3`, 3.9 or newer) and the two CLIs it drives. **[SETUP.md](SETUP.md)** is the complete
walk for a Mac with nothing on it, written so a coding agent can follow it; the short form:

```bash
xcode-select --install                                  # git and python3, if `git --version` fails
curl -fsSL https://claude.ai/install.sh | bash          # Claude Code (`claude`)
brew install codex                                      # or the release binary; SETUP.md §3
git clone https://github.com/treemarks/bonsai ~/code/bonsai
mkdir -p ~/.local/bin && ln -sf ~/code/bonsai/bonsai ~/.local/bin/bonsai
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
bonsai doctor
```

`bonsai doctor` lists what is installed and which logins it can see, and prints the install line
for anything missing. Your existing `~/.claude` and `~/.codex` sign-ins show up as the pool called
`default`, labelled **personal** on the board. Windows: the platform-specific parts are already
kept apart (SETUP.md's last section says what is in place); a tested Windows release comes later.

## Sign your institution seats in as their own pools

```bash
bonsai login you@stanford.edu --claude --institution    # opens the Claude sign-in page; pick the Stanford org
bonsai login you@stanford.edu --codex  --institution    # opens the ChatGPT sign-in; pick the Stanford workspace
```

Each one lands in `~/.claude-pools/you@stanford.edu` or `~/.codex-pools/you@stanford.edu`, the
directories the CLIs call `CLAUDE_CONFIG_DIR` and `CODEX_HOME`. Nothing is copied between pools;
Claude's credential stays in your login Keychain, Codex's in its own `auth.json`, exactly where the
CLIs put them. `--institution` marks the seat so that `auto` routing uses it only for
`--kind sensitive` work and never for everyday jobs. The board labels it `stanford` (or
`--name <label>`).

A second personal login (a Max plan beside a Pro, say) is `bonsai login other@gmail.com --claude`
with no flag.

## The board

```
bonsai gauge          # live; q quits
bonsai gauge --once   # one frame, for a script or a screenshot
```

```
ACCOUNTS   ant = Claude   oai = Codex   ⌂ = institution seat           as of 2m ago   refresh in 3m
  LOGIN       VIA                          %LEFT RESET   5H    RESET   PLAN    STATE
  ⌂stanford   oai ████████████████████░░░░ 83%   2d13h   100%  ·       edu     ok
  ⌂stanford   ant ██████████████████░░░░░░ 76%   2d13h   100%  ·       team    ok
   personal   ant ████████░░░░░░░░░░░░░░░░ 34%   5d20h   91%   3h12m   pro     ok
   personal   oai ███████████████░░░░░░░░░ 62%   6d4h    100%  ·       plus    ok

MACHINE    ACTIVITY                 CPU%   MEM%   SWAP   BATT      UP
  air        job×1 pass:astra        23%    61%    1GB    84% batt  3d2h    last: astra ok 14m ago
```

Rows sort by the weekly reset that comes soonest, because that room is the most perishable:
capacity unspent at the reset is gone. The bar and `%LEFT` are the weekly window; `5H` is the
five-hour one. Green, yellow and red turn at 50% and 20% left. `STATE` tells you when a login
needs attention: `re-login` (the sign-in lapsed; run `bonsai login` again), `locked` (the login
Keychain is locked to this shell, which happens over SSH; unlock it in a terminal on the Mac),
`no-plan` (a free organization the usage surface does not serve), `limited` (the provider is
refusing calls until the reset), `offline`.

The board probes each login at most once per interval (default five minutes, floor three) and
renders from the cache in between, so a second window or a script never doubles the reads.

## Routing

```bash
bonsai route                  # both providers: the order for general work and for sensitive work
bonsai route codex --fresh    # one provider, probe now
```

Two kinds of work, two orders:

- **general** (the default) — personal logins only, soonest weekly reset first, a login under
  10% room waits at the end. An institution seat never carries everyday work.
- **sensitive** — institution seats only. Data under the institution's agreements never reaches
  a personal login.

A **named** target overrides both: `stanford-codex` means that seat, full stop.

### Jobs

```bash
bonsai job stanford-codex -f notes.md -o answer.md "Summarize the themes in these interview notes"
bonsai job stanford-claude --kind sensitive -f export.csv -o report.md "Describe the distribution; no row-level values"
bonsai job astra "Is this argument sound? <paste>"        # a model alias picks the provider; auto picks the login
bonsai job sol@stanford -f draft.md -o review.md "..."   # alias on a named login
bonsai job codex --effort high -o plan.md - < brief.md    # stdin
```

Targets: `claude` / `codex` (auto login), `<login>-claude` / `<login>-codex` (`stanford-codex`,
`personal-claude`), a model alias (`astra`, `sol`, `opus`, `sonnet`, `haiku`; edit them with
`bonsai config --set 'models.astra=["codex","gpt-6-astra"]'`), or `<alias>@<login>`.

`-f` inlines files into the prompt (400 KB each, then truncated). `-o` writes the model's final
message to a file. `--cd` sets the working root the model sees. `--dry-run` prints the command
and spends nothing. Codex jobs run `codex exec` in its **read-only** sandbox; Claude jobs run
`claude -p` with `--permission-mode dontAsk`, so a job can read what you give it and nothing else
can happen on your machine without you.

### Adversarial passes

```bash
bonsai pass astra -f PLAN.md -o PLAN.pass-astra.md --brief "the budget section"
bonsai pass opus@stanford -f thesis_ch3.md -o ch3.pass.md
```

A pass asks a second model to break the material: numbered findings, most serious first, each
with the quoted claim, why it fails, a confidence and what would settle it; then what held; then a
one-paragraph verdict. No praise, no rewriting. Use a different model family from the one that
wrote the draft.

### Any command, under a login

```bash
bonsai run --pool stanford -- codex exec "..."
bonsai run --pool auto --provider claude -- claude -p "..."
bonsai run --pool stanford -- codex          # an interactive Codex session on that seat
```

## Teach Claude Code the words

```bash
bonsai install-skill
```

This writes `~/.claude/skills/bonsai-route/SKILL.md`. From then on, in any Claude Code session:

> route this to my stanford codex · ask astra whether the proof holds · call an adversarial pass
> from sol on this draft · run that on stanford, it has student data · use my personal account

...and Claude Code runs the matching `bonsai` command, writes the result to a file beside the
material, and reads it back to you. The job runs under the login you named, never the one the
chat is signed into. The skill's table of words is in the file; edit it to taste.

Codex users: the same table works as a section of your `AGENTS.md`.

## What Bonsai reads, and what it never does

- **Usage reads.** Bonsai asks each provider's own usage surface, the one the CLIs' `/usage`
  screens read (Anthropic's `oauth/usage`, ChatGPT's `wham/usage`), with the token the CLI
  stored, and says who it is: `User-Agent: bonsai/<version>`. It never presents itself as
  Claude Code or as a browser. These are the CLIs' surfaces, not documented public APIs: they
  can change without notice, and a login hammered with reads gets a 429. Bonsai reads each login
  at most once per interval, backs off on 429 for the time the provider names, and treats every
  failure as "unknown", never as "empty". The read is a choice: `bonsai config --set
  usage_reads.claude=false` (or `.codex`) turns it off, and the row then reads `signed-in` with
  no numbers. Anthropic's terms for Free/Pro/Max logins say OAuth sign-in is for Claude Code and
  Anthropic's own apps; a once-per-interval look at your own usage percentages is the one thing
  Bonsai does with that token, and whether that is "ordinary use" is yours to judge, so the
  switch is there.
- **Tokens stay put.** Bonsai reads the credential where the CLI keeps it (Keychain, `auth.json`),
  uses it for the read and keeps nothing: no token is printed, logged, cached or written anywhere.
  The state directory (`~/.local/state/bonsai/`) holds percentages, timestamps, and a job
  ledger with labels and exit codes.
- **Jobs run the official CLIs.** Every job is `claude` or `codex` itself, started with that
  pool's config directory. Bonsai is not a client of either API and does not speak to a model.
- **No sharing.** A pool is your own sign-in on your own machine. Don't copy a pool directory to
  another person or machine; sign in there instead.
- **No network but the two providers.** Bonsai phones nobody else: no telemetry, no update check.

## Terms of use

Each login is yours under its provider's terms, and an institution seat is yours under your
institution's agreement as well. Read them; Bonsai cannot read them for you.

- Anthropic: [Consumer Terms](https://www.anthropic.com/legal/consumer-terms) (personal plans),
  [Commercial Terms](https://www.anthropic.com/legal/commercial-terms) (Team, Enterprise and
  Education organizations), [Usage Policy](https://www.anthropic.com/legal/aup), and the Claude
  Code [legal and data-use notes](https://docs.anthropic.com/en/docs/claude-code/data-usage).
- OpenAI: [Terms of Use](https://openai.com/policies/terms-of-use) (personal plans),
  [Business Terms](https://openai.com/policies/business-terms) and the
  [Education](https://openai.com/chatgpt/education/) program, [Usage Policies](https://openai.com/policies/usage-policies),
  and Codex's [data and sandbox notes](https://developers.openai.com/codex/).
- Stanford: [UIT on AI tools and data risk](https://uit.stanford.edu/security/ai),
  [Data risk classifications](https://uit.stanford.edu/guide/riskclassifications),
  the [Computer and Network Usage Policy (Admin Guide 6.2.1)](https://adminguide.stanford.edu/chapters/computing/computer-and-network-usage-policy).

In plain terms: use an institution seat for the work the institution gave it to you for; do not
put data on a personal login that the institution says may not go there; do not share logins;
and expect the usage read to break one day, loudly, when a provider changes its surface.

## Development

```bash
/usr/bin/python3 -m unittest discover -s tests     # stock macOS python
BONSAI_POOLS_HOME=/tmp/fakehome BONSAI_STATE=/tmp/bonsai-state ./bonsai gauge --once --no-color
```

`BONSAI_POOLS_HOME` points discovery at another home (tests use a synthetic one);
`BONSAI_STATE` and `BONSAI_CONFIG` move the cache and config. Standard library only; one file.

Bonsai is MIT-licensed. It began as a handoff for a friend with a MacBook Air, a personal Claude
Pro and two Stanford seats, who wanted the Treemarks pool gauge in miniature.
