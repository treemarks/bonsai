# Accounts & data

[Home](../README.md) · [Setup](../SETUP.md) · [Usage](USAGE.md) · [Accounts & data](ACCOUNTS.md)

## Routing notice

Bonsai prints this once, before your first sign-in or your first job:

```text
Before your first job (shown once; nothing to type):
  - A job you route from a chat goes through that chat (details from your conversation can go with it),
    outside Stanford's protections.
  - Fine for ordinary work. For private data (student records, health records), use
    a Stanford-approved tool directly.
    https://uit.stanford.edu/guide/riskclassifications
  - Bonsai doesn't check your files for private data.
```

At Stanford, for example, PHI goes only through Stanford's approved routes (such as its AI API Gateway); Bonsai's sign-in route is not one of them.

- **What travels.** The chat writes the task and reads the answer. The task and the `-f` files
  go to the login that runs the job; the answer comes back to the chat. Your chat and its history
  stay where they are; the job is a separate one-off call on the other login.
- **What routing saves.** Long work runs on another login's room instead of your chat's. The task and
  the answer still pass through your chat.

Bonsai is an independent Treemarks project. It is not endorsed by Stanford, Anthropic or OpenAI;
Stanford appears here as an example institutional configuration, with links to its public pages.

## Sign your institution seats in as their own pools

```bash
bonsai login you@stanford.edu --claude --institution    # opens the Claude sign-in page; pick the Stanford org
bonsai login you@stanford.edu --codex  --institution    # opens the ChatGPT sign-in; pick the Stanford workspace
```

Open the sign-in link in a private window, so the browser cannot finish it with an account it is
already signed in to; nothing is typed in Terminal to acknowledge the notice. Each login lands in
`~/.claude-pools/you@stanford.edu` or `~/.codex-pools/you@stanford.edu`, the folders the CLIs call
`CLAUDE_CONFIG_DIR` and `CODEX_HOME`. Nothing is copied between pools; Claude's credential stays
in your login Keychain, Codex's in its own `auth.json`, exactly where the CLIs put them.

`--institution` marks the seat `⌂` on the board. The mark is your declaration: a successful
sign-in does not verify that you picked the university workspace, and neither proves approval for
any data. `auto` spends a marked seat like any login, in the order your `prefer` setting gives
([Usage](USAGE.md), "Choosing an account"); a named target (`stanford-codex`) always means that
seat.

After each sign-in Bonsai prints what actually signed in (for Claude the e-mail, organization and
plan; for Codex the e-mail, plan type such as `edu_pro`, and a short workspace id). If the e-mail
is not the one asked for, the pool is marked and no job uses it until you sign it in again as the
right account. One e-mail with two ChatGPT workspaces is two pools: `--pool stanford-pro --name
stanford-pro` for the second; two pools showing one workspace id are the same workspace signed in
twice. Logins are named exactly (`stanford`, `stanford-pro`, or the e-mail), never by prefix, and
routing words (`auto`, `codex`, `openai`, `astra`, ...) are refused as names. `--device-auth`
(Codex) uses the one-time-code sign-in when the browser callback on port 1455 cannot complete.

## What Bonsai reads and stores

- **Identity:** `claude auth status` under each pool (Claude Code answers with the account,
  organization and plan; Bonsai reads no credential). For Codex, Bonsai reads the pool's
  `auth.json` to check a sign-in exists and takes the e-mail, plan and workspace from its id token,
  as labels; it never prints or stores the token.
- **Codex usage** comes from Codex's own app-server, started under the pool's `CODEX_HOME`;
  Codex sends the request and refreshes the credential itself.
- **Claude usage** comes from Claude Code itself: the usage each Claude job reports, and Claude
  Code's `/usage` (no model call) for a login whose reading is older than 15 minutes, when a job is
  about to go to it or you open the board. Bonsai reads no stored Claude token.
- **Stored** under `~/.local/state/bonsai/`, in files and folders Bonsai gives owner-only permission bits (it does
  not check access lists, the folders above them, or Windows permissions): the last probe (e-mail, plan and
  organization labels, percentages, reset times), the latest Claude usage readings, a job ledger (labels, pool, outcomes, seconds) and a failed job's own messages (they
  can quote your task). No token. A job's answer is held there privately until it is published to the file you named
  (or printed); a crash can leave that staging file behind.
- **Jobs** are `claude` or `codex` themselves, with that pool's config folder and an environment
  of basics only (PATH, HOME, locale, proxy): no API keys, tokens or endpoint overrides, so the
  one login a job is handed is the one it was given.
- **Network:** Bonsai's own is `git fetch` (during an update, and once a day from the live board in a terminal, to
  see whether a new version is out) and, for the board's MODEL column, a request to Ollama on this Mac
  (`http://127.0.0.1:11434`, no proxy). Everything else is the CLIs'. A job has no web unless you add `--web`
  (ChatGPT jobs, never with `-f`): then it may search OpenAI's cached web index, its searches go to OpenAI, it opens
  no live page, and Codex's code-mode host (its JavaScript runner, how it reaches search) is on for that job. A
  planted-token test with it on read nothing, though its patch tool can test whether a guessed line is in a file. An update you approve runs the new code, so
  update only from github.com/treemarks/bonsai (Bonsai prints the source and merges exactly the commits it listed).
- **What stays on this Mac:** sign-ins in each login's folder (anything running as you can read file-based ones;
  separate folders choose an account, they don't wall one off); the job ledger (ids, times, login, outcome, not your
  prompts); a failed job's own messages in Bonsai's state folder (they can quote the task); and the answer files you
  asked for. Keep these folders out of synced drives if that matters to you.
- **Files you attach:** `-f` refuses sign-in and key files (the login folders, `~/.ssh`, `auth.json` and the like),
  even through a link; it does not look for other private data.
- **Which account a login is.** A sign-in that comes back as another e-mail is refused. Bonsai does not yet record
  which workspace a login was meant for, so a login that changes workspace under the same e-mail is not caught;
  `bonsai doctor` shows what each login reports.
- **No sharing.** A pool is your own sign-in on your own machine. Don't copy a pool folder to
  another person or machine; sign in there instead.

## Terms of use

Each login is yours under its provider's terms, and an institution seat is yours under your
institution's agreement as well. Read them; Bonsai cannot read them for you.

Bonsai is for one person's own accounts on one machine, each used under its vendor's
terms. It is not for pooling other people's logins, sharing an account, or routing anyone else's
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
sentence about a routed Bonsai job is: a Stanford account and tool, in a configuration Stanford
has not reviewed, driven headless, with the task written and the answer read by whatever asked
for it.
