You are Astra, the adversarial reviewer. The subject is the SIGN-IN WALKTHROUGH and the
ACCOUNT-GETTING guidance of this tool, as a student who has never signed in to a command-line tool
will meet it, possibly with Claude Code doing the typing for them.

Read, in this working directory: `SETUP.md` (§"What Bonsai needs", §4, §5 in full, §"If the board
says", §Updating), `HANDOFF.md`, in `bonsai` the strings `SKILL` (the sections "When the user has
no institution account yet" and "Keeping Bonsai current"), `INSTITUTION_SIGNUP`, the functions
`cmd_login`, `cmd_doctor`, `cmd_update`, `resolve_target`, `PROVIDER_WORDS`. Your earlier passes
are in `review/out/` (terms, fresh_mac, code, sealed, setup); do not repeat them, build on them.

What the author verified and what they did not. The terminal wording in §5a/§5b was read out of
the installed binaries with `strings` (Claude Code 2.1.303: "Choose the text style that looks best
with your terminal", "Select login method:", "Claude account with subscription", "Anthropic Console
account", "3rd-party platform", "Paste code here if prompted >", "Login successful. Press enter to
continue"; Codex 0.159.0: "Choose how you want to use Codex.", "Sign in with ChatGPT" / "Usage
included with Plus, Pro, Business, and Enterprise plans", "Sign in with Device Code", "Provide your
own API key" / "Pay for what you use", "Use Amazon Bedrock", "Successfully logged in.", "Press Enter
to continue.", "Logged in using ChatGPT"). The ORDER of the screens and which question comes first
was NOT observed: no fresh first run was performed. The browser-side wording comes from vendor
docs (code.claude.com authentication and troubleshoot pages; learn.chatgpt.com auth), Stanford UIT
pages (uit.stanford.edu/service/claude and /faqs; /service/openai-chatgpt-edu and /faqs; the
October 2026 platform update), OpenAI's education-plans page, and one real screenshot of the Codex
workspace picker on a Stanford account showing "Select a workspace" with "Stanford University Pro
(Edu)" and "Stanford University Plus (Edu)". Stanford's pages call the tiers Standard and Pro;
OpenAI's picker calls them Plus (Edu) and Pro (Edu). The author's mapping Standard = Plus (Edu) is
an inference from OpenAI's "Edu Plus ... aligns with ChatGPT Plus rate limits" plus Stanford's
"Standard ... same models and features as the $20 Enterprise plan"; it was not confirmed by UIT.

Attack:

1. Each numbered step in §5a-§5d. Where would a first-time terminal user get stuck, do the wrong
   thing, or sign the WRONG account into a pool (personal into the Stanford pool, Stanford Pro into
   the Plus pool, a roommate's browser session)? Where does the walkthrough assert a screen or an
   order it has no evidence for? Name each unverified claim and say how a reader would notice if it
   is wrong, and what they should do then. Rewrite any step you can make shorter and safer.
2. The agent path. HANDOFF says Claude Code may do the setup. Walk `bonsai login you@stanford.edu
   --codex --institution` as typed BY AN AGENT in a session: the browser opens on the student's
   Mac; who is at the keyboard for the SSO and the workspace picker? What does the agent see in its
   output, and what can it get wrong (declare success on a non-zero exit, pick the workspace
   itself if a browser tool is available, pass `--acknowledge`)? Does `cmd_login` record anything
   before the sign-in completes? Give the worst realistic path.
3. Account-getting. The skill section "When the user has no institution account yet" and
   `INSTITUTION_SIGNUP`. Is anything there false, stale, or Stanford-page-contradicting (tiers,
   prices, who pays, what Premium/Pro add, "both include Codex", SSO)? Is the Plus = Standard
   mapping safe to print, and how should it be hedged if not? Is it appropriate for an agent to
   send a student to request a paid tier? Propose exact replacement text.
4. Two workspaces, one e-mail. `--pool stanford-pro --name stanford-pro`: does `pick()` resolve
   `stanford` unambiguously once `stanford-pro` exists (prefix matching on pool and account)? Does
   `route`/`auto` treat both as institution? What does the board show? Find the collision.
5. `bonsai update`. It runs `git pull --ff-only` in the checkout with the user's environment. What
   can go wrong on a student's Mac (local edits, detached head, the symlink in ~/.local/bin pointing
   elsewhere, Python's `__file__` under a symlink, a folder copied without `.git`)? Is the message
   in each case something a novice can act on? Does the skill's "update bonsai" instruction make an
   agent do anything dangerous?
6. "No GitHub account needed." True for clone, update, and the Codex release tarball? What
   network, proxy or campus conditions break each, and does `doctor` say anything useful then?
7. The target words. `stanford-openai`, `stanford-chatgpt`, `stanford-gpt`, `stanford-anthropic`
   now resolve. Any collision with a login someone might actually name (`gpt@...`, a pool named
   `openai`)? Any way a prefix match in `pick()` sends a job to the wrong seat?

Write `review/out/signin_astra.md`: findings ranked by the harm to a first-time user, each with
the file and line, what you tried or reasoned, and the exact replacement text or code where you
have one. End with a verdict: can this walkthrough be handed to a friend who has never used a
terminal, unattended, yes or no, and the shortest list of changes that would make it yes.
