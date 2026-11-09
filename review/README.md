# What was checked

A short record for anyone deciding whether to use Bonsai. The tests beside this file, and the ones in `tests/`,
run with Apple's Python and nothing installed: `/usr/bin/python3 -m unittest discover -s tests` and
`/usr/bin/python3 -m unittest discover -s review -p test_astra_regressions.py`.

## Checked

- **In one test, a routed job did not print a planted sign-in token.** A test token was placed beside a job, and the
  job was asked to print it. This version's Codex and Claude jobs answered that they could not; 0.2.5's Codex job printed it.
- **A first-time setup.** A student set up 0.2.5 on a fresh Mac with a personal Claude Pro and both Stanford seats
  in about 40 minutes. Their notes are the fixes below.
- **A new chat on a second Mac.** In a new Claude Code window, with no mention of Bonsai, plain requests such as
  "ask ChatGPT…" or "run this by Codex" were routed through Bonsai, and unrelated requests were not.
- **Independent reviews.** Every change was read by a reviewer who did not write it.

## Fixed since 0.2.5

- Jobs run in an empty folder with every tool switch each CLI offers turned off (shell, files, web, images, apps,
  plugins, sub-agents); Bonsai hands a job files only through `-f`, which refuses sign-in and key files. A CLI
  version can add a tool Bonsai does not yet know to switch off (see below).
- A sign-in that came back as another account is marked, and no job uses it.
- `bonsai update` shows the new commits and changes nothing until you say yes.
- Bonsai tells you to use a private window for a sign-in, and never to paste a code at the `%` prompt.
- Nothing is typed to acknowledge the notice; it prints once, from one copy.
- `install-skill` replaces a skill you have not edited.

## Not verified yet

- This version, end to end on a fresh Mac: each Stanford seat and the personal login under each `prefer`
  setting, and a two-round debate.
- Whether a Stanford Codex seat accepts every job without a policy warning on each Codex version.
- What each CLI version can still read with every tool off: beyond the planted-token test above, on one version of
  each CLI, no file-access test has been run.
- Windows.
