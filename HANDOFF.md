# Handoff: Bonsai on a MacBook Air with a personal Claude Pro and two Stanford seats

For the friend this was built for. Paste this file and `SETUP.md` to Claude Code (or read them
yourself); either way the steps are the same.

## What you end up with

- A board (`bonsai gauge`) with one row per login — your personal Claude, your Stanford Claude,
  your Stanford Codex, and your personal ChatGPT if you sign that in too — showing how much of
  each week's and each five-hour window is left, when each resets, and your Air's own load on the
  row beneath. It is the Treemarks pool gauge in miniature.
- Routing: `bonsai job stanford-codex ...` runs a job on that seat; `bonsai job astra ...` or
  `sol ...` runs on whichever personal login has the most perishable room; `bonsai pass astra -f
  draft.md` has a second model try to break your draft.
- Claude Code that understands the words: after `bonsai install-skill`, "route this to my
  Stanford Codex", "ask Astra", "adversarial pass from Sol on this" each become the right
  `bonsai` command, run under the login you named, never the one the chat is signed into.

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
2. `bonsai doctor` should list `git`, `claude`, `codex` with versions, `keychain readable`, and
   your three (or four) logins. If something is missing it prints the install line.
3. `bonsai gauge --once`. The first time, macOS asks once per Claude login whether `security` may
   read the credential; click **Always Allow**.
4. `bonsai install-skill`, then open Claude Code anywhere and say: *"ask astra whether this plan
   holds"*. Watch it run `bonsai job astra ...` and read the answer back.

## Everyday use

```bash
bonsai gauge                                          # leave it open in a Terminal tab
bonsai job stanford-codex -f notes.md -o out.md "..." # a job on the Stanford seat
bonsai job astra -o out.md "..."                      # personal login, Astra
bonsai pass sol -f draft.md -o draft.pass.md          # adversarial pass on the draft
bonsai route                                          # why a job would go where
```

Or just say it in Claude Code. The words it knows are in `~/.claude/skills/bonsai-route/SKILL.md`
after `install-skill`; edit them if you use different ones.

## Where the lines are

- Stanford classifies data as Low, Moderate or High Risk and says which tools are approved for
  which; the Claude for Education page and the June 30 notice are linked from the README. Use the
  seat for what Stanford gave it to you for; put nothing on your personal login that Stanford says
  may not go there; and ask your department's IT or privacy office when in doubt. Bonsai routes;
  it does not decide what may go where.
- Everything is your own logins on your own Mac. Don't copy a pool folder anywhere.
- The usage numbers come from the same surfaces the CLIs' `/usage` screens read. They are not
  documented APIs; the day a provider changes one, the row says so instead of showing a number.
  The README's "Terms of use" section says what Bonsai reads and lets you turn the Claude read off.

## If something is off

`bonsai doctor` first. `locked` means the Keychain is locked to that shell (SSH); run it in
Terminal on the Air. `re-login` means the sign-in lapsed; run the `bonsai login` line again.
Tests: `/usr/bin/python3 -m unittest discover -s ~/code/bonsai/tests`. Issues go to
github.com/treemarks/bonsai.
