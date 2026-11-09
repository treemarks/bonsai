# Handoff: Bonsai on a Mac with one personal plan and an institution's seats

For whoever is setting Bonsai up on their own machine; Stanford is the worked example
institution. Paste this file and `SETUP.md` to Claude Code (or read them yourself); either way
the steps are the same.

## First, the one thing to know

When you ask the chat you are in — Claude Code, on your personal account — to run a job on
your Stanford Claude or Stanford Codex account, that chat can see the task and the results, and
handles them under your personal account and its settings. Choosing the Stanford account for the
job does not give your personal chat Stanford's protections.

So only route work that is fine in your personal chat anyway; ordinary personal work, a family
project with names in it, is fine, and you remain responsible for what you share. For protected
information — confidential student records, research interviews, health records, anything Stanford
classes Moderate or High Risk — open a tool and account Stanford approves for that information
yourself, outside the chat, and do not bring the results back into the chat. A Stanford login alone
is not approval: Stanford's Claude, for example, is not approved for PHI at all (its AI API Gateway
is). Bonsai does not check your files; it refuses a job that declares `--data moderate|high|phi`
before it reads a file, and otherwise routes what you give it. It asks you to acknowledge this
notice once, when you add your first Stanford account; after that it does not ask again (a one-line
reminder rides on each chat-driven job to a Stanford account).

**If you let Claude Code do the setup for you from this file:** it must show you this notice in
its reply before it routes any work. Finishing a browser sign-in does not count as having read it.

(For terminal users there is a weak workaround: `bonsai run --pool stanford -- claude` opens a
Claude Code session *on* the Stanford account in your Terminal. It protects nothing by itself; it
only keeps the work in a Stanford-signed session *if you type there yourself*, and it does not make
that account approved for any particular data. If a chat launches it, the output comes back to the
chat.)

## What you end up with

- A board (`bonsai gauge`) with one row per login — personal Claude, Stanford Claude, Stanford
  Codex, and personal ChatGPT if you sign that in — showing how much of each week's and each
  five-hour window is left, when each resets, and your Air's own load on the row beneath. It is the
  Treemarks pool gauge in miniature. (Claude rows show the plan and `signed-in` rather than
  percentages unless you turn Claude usage reads on; [the usage guide](docs/USAGE.md#the-board) says why.)
- Routing: `bonsai job stanford-codex ...` runs a job on that seat; `bonsai job astra ...` or
  `sol ...` runs on whichever personal login has the most perishable room; `bonsai pass astra -f
  draft.md` has a second model try to break your draft.
- Claude Code that understands the words: after `bonsai install-skill`, "route this to my
  Stanford Codex", "ask Astra", "adversarial pass from Sol on this" each become the right
  `bonsai` command, and "this has student data" makes it stop and tell you to use Stanford's tools
  directly instead.

## Your logins, as pools

| You say | The login | Bonsai's name for it | How it gets there |
|---|---|---|---|
| "my Claude" | personal Claude | `personal` (ant) | already there once `claude` is signed in |
| "my Stanford Claude" / "my Stanford Anthropic" | Claude for Education seat | `stanford` (ant) ⌂ | `bonsai login you@stanford.edu --claude --institution` |
| "my Stanford Codex" / "Stanford ChatGPT" / "Stanford OpenAI" | ChatGPT Edu seat | `stanford` (oai) ⌂ | `bonsai login you@stanford.edu --codex --institution` |

Those are the same seats under different names: `stanford-codex`, `stanford-chatgpt` and
`stanford-openai` are one target, `stanford-claude` and `stanford-anthropic` another. You do not
need to know which CLI serves which; say the company or the product and Bonsai picks the CLI.

The `⌂` means "marked institution by you": `auto` routing uses such an account only for
`--kind sensitive` work and never for everyday jobs; a named target (`stanford-codex`) always
means that account. The mark does not verify that you picked the Stanford workspace at sign-in
(check what `bonsai doctor` shows) and does not mean approval for any data. Your personal account
carries everyday work. If you add a personal ChatGPT login later (`codex`, sign in), it joins the
board as `personal` (oai).

**Never signed in to a CLI before?** That is what `SETUP.md` §5 is for: conditional sign-in
instructions that name each screen you may meet and what to choose on it, including the ChatGPT
"Select a workspace" page (two labels seen there: *Stanford University Plus (Edu)* and *Stanford
University Pro (Edu)*) and the Claude page where you choose **Continue with SSO** for the Stanford
account. The exact first-run order of the CLIs has not been verified from a fresh account, so choose
by the words on the screen, not by position.

**If Claude Code does the setup for you:** it runs the commands and starts each sign-in; you
complete every browser page yourself (e-mail, password, two-step, workspace, approve) and tell it
which workspace you chose. It must not choose a workspace, request an account, or accept a purchase
or an account migration for you, and you never send it a password, a code or a credential file.
Run the personal sign-ins (SETUP §5a, §5b) in your own Terminal window, not in its terminal tool.
After each sign-in Bonsai prints the e-mail (and for Codex the plan and a short workspace id) that
actually signed in, and refuses to record a different e-mail than the one asked for.

**Don't have the Stanford accounts yet?** They are requested from Stanford, not created at
claude.ai or chatgpt.com, and the request is yours to submit:
[Claude for Education](https://uit.stanford.edu/service/claude) (Standard free for eligible active
students, faculty, staff and postdocs, includes Claude Code; Premium paid, more usage and the Fable
models) and [ChatGPT Edu](https://uit.stanford.edu/service/openai-chatgpt-edu) (Standard free if
eligible; Pro optional and paid; both include Codex). Paid tiers bill a PTA or an eligible
student's tuition account, and nothing in Bonsai needs one. The *Plus (Edu)* workspace appears to
be Standard, but UIT has not confirmed that mapping; choose the workspace you were provisioned.
If you already use a personal account on your Stanford e-mail, read UIT's migration guidance
before requesting. Claude Code knows all this: ask it "how do I get Stanford Codex".

**No GitHub account needed.** The clone in `SETUP.md` §4, `bonsai update` and the Codex release
download are anonymous HTTPS downloads from GitHub's public hosts; if anything asks you for a
GitHub username, stop and check the network rather than make an account. If someone hands you the
folder instead, drop it at `~/code/bonsai` and skip the clone. Later, `bonsai update` (or "update
bonsai" in Claude Code) pulls the newest version onto the checkout it runs from and says when to
re-run `bonsai install-skill`; it refuses to touch a checkout a shell has redirected git away from.

## The steps

1. Follow `SETUP.md` from the top: Command Line Tools, Claude Code, Codex, Bonsai, sign-ins. On a
   clean Air this is about ten minutes, most of it the Command Line Tools download.
2. `bonsai doctor` should list `git`, `claude`, `codex` with versions and your three (or four)
   logins as `signed in as ...`. If something is missing it prints the install line.
3. `bonsai gauge --once`.
4. `bonsai install-skill`, then open Claude Code anywhere and say: *"ask astra whether this plan
   holds"*. Watch it run `bonsai job astra ...` and read the answer back.

## Everyday use

```bash
bonsai gauge                                          # leave it open in a Terminal tab
bonsai job stanford-codex -f notes.md -o out.md "..." # a job on the Stanford seat (goes through your chat if a chat asked)
bonsai job astra -o out.md "..."                      # personal login, Astra
bonsai pass sol -f draft.md -o draft.pass.md          # adversarial pass on the draft
bonsai route                                          # why a job would go where
```

Or just say it in Claude Code. The words it knows are in `~/.claude/skills/bonsai-route/SKILL.md`
after `install-skill`; read it once, and edit it if you use different words.

## Where the lines are

- Stanford classifies data as Low, Moderate or High Risk and says which tools are approved for
  which; the Claude for Education page and the June 30 notice are linked from [Accounts & data](docs/ACCOUNTS.md#terms-of-use). Bonsai
  routes; it does not decide what may go where, and a routed job never gets the seat's protections
  for the chat that asked.
- Everything is your own logins on your own Mac. Don't copy a pool folder anywhere.
- The usage numbers come from the CLIs themselves (Codex's own app-server; Claude's `auth status`).
  Bonsai reads a stored Claude token only if you turn that on, and [Accounts & data](docs/ACCOUNTS.md#what-bonsai-reads-and-what-it-never-does) says what Anthropic's
  terms say about that.

## If something is off

`bonsai doctor` first. `re-login` means the sign-in lapsed; run the `bonsai login` line again.
`limited` means the provider has stopped that login until the reset shown. Tests:
`/usr/bin/python3 -m unittest discover -s ~/code/bonsai/tests`. Issues go to
github.com/treemarks/bonsai.
