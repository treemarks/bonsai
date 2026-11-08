# Handoff: Bonsai on a MacBook Air with a personal Claude Pro and two Stanford seats

For the friend this was built for. Paste this file and `SETUP.md` to Claude Code (or read them
yourself); either way the steps are the same.

## First, the one thing to know

Bonsai lets the chat you are in — Claude Code, on your personal Pro login — send a job to your
Stanford Claude or Stanford Codex seat. That job goes **through** the chat: the chat writes the
task, Bonsai runs it on the seat, and the chat reads the answer, on your personal login. So the
Stanford seat's protections (Stanford's agreement, no training, its data-risk approvals) cover the
seat's own call and nothing else. Routing does not give your personal chat Stanford's protections.

Use Bonsai for work you are happy to have in your personal chat anyway. For PHI, PII, student
records or anything Stanford classes Moderate or High Risk, do not route a job: use Stanford's
tools directly, as a person — Stanford's Claude or ChatGPT Edu in the browser, or a Terminal
window you open yourself and sign in to the seat. Bonsai will say this when you add the seats,
refuse a chat-driven job that declares such data (`--data moderate|high|phi`) before it reads a
file, and remind you on every chat-driven job to a seat.

(For terminal users there is a weak workaround: `bonsai run --pool stanford -- claude` opens a
Claude Code session *on* the seat in your Terminal. It protects nothing by itself; it only keeps
the work in a Stanford-signed session *if you type there yourself*. If a chat launches it, the
output comes back to the chat.)

## What you end up with

- A board (`bonsai gauge`) with one row per login — personal Claude, Stanford Claude, Stanford
  Codex, and personal ChatGPT if you sign that in — showing how much of each week's and each
  five-hour window is left, when each resets, and your Air's own load on the row beneath. It is the
  Treemarks pool gauge in miniature. (Claude rows show the plan and `signed-in` rather than
  percentages unless you turn Claude usage reads on; the README says why.)
- Routing: `bonsai job stanford-codex ...` runs a job on that seat; `bonsai job astra ...` or
  `sol ...` runs on whichever personal login has the most perishable room; `bonsai pass astra -f
  draft.md` has a second model try to break your draft.
- Claude Code that understands the words: after `bonsai install-skill`, "route this to my
  Stanford Codex", "ask Astra", "adversarial pass from Sol on this" each become the right
  `bonsai` command, and "this has student data" makes it stop and tell you to use Stanford's tools
  directly instead.

## Your three logins, as pools

| You say | The login | Bonsai's name for it | How it gets there |
|---|---|---|---|
| "my Claude" | personal Claude Pro | `personal` (ant) | already there once `claude` is signed in |
| "my Stanford Claude" | Claude for Education seat | `stanford` (ant) ⌂ | `bonsai login you@stanford.edu --claude --institution` |
| "my Stanford Codex" / "Stanford ChatGPT" | ChatGPT Edu seat | `stanford` (oai) ⌂ | `bonsai login you@stanford.edu --codex --institution` |

The `⌂` marks an institution seat: `auto` routing uses it only for `--kind sensitive` work and
never for everyday jobs; a named target (`stanford-codex`) always means that seat. Your personal
Pro carries everyday work. If you add a personal ChatGPT login later (`codex`, sign in), it joins
the board as `personal` (oai).

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
  which; the Claude for Education page and the June 30 notice are linked from the README. Bonsai
  routes; it does not decide what may go where, and a routed job never gets the seat's protections
  for the chat that asked.
- Everything is your own logins on your own Mac. Don't copy a pool folder anywhere.
- The usage numbers come from the CLIs themselves (Codex's own app-server; Claude's `auth status`).
  Bonsai reads a stored Claude token only if you turn that on, and the README says what Anthropic's
  terms say about that.

## If something is off

`bonsai doctor` first. `re-login` means the sign-in lapsed; run the `bonsai login` line again.
`limited` means the provider has stopped that login until the reset shown. Tests:
`/usr/bin/python3 -m unittest discover -s ~/code/bonsai/tests`. Issues go to
github.com/treemarks/bonsai.
