# Accounts & data

[Home](../README.md) · [Setup](../SETUP.md) · [Usage](USAGE.md) · [Accounts & data](ACCOUNTS.md)

## Sign your institution seats in as their own pools

```bash
bonsai login you@stanford.edu --claude --institution    # opens the Claude sign-in page; pick the Stanford org
bonsai login you@stanford.edu --codex  --institution    # opens the ChatGPT sign-in; pick the Stanford workspace
```

The first `--institution` prints the [routing notice below](#routing-notice) and, in a Terminal, asks you to type
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

## Routing notice

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

Bonsai is for one person's own accounts on one machine, each used under its vendor's terms.
It is not for pooling other people's logins, sharing an account, or routing anyone else's
requests through your plan.

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

