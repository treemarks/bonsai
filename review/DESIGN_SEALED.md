# Design under attack: sealed jobs, data classes, and "just say so"

Draft 2026-11-08, written to be broken. Three claims, each with what it does and does not promise.

## The problem

A student works in a personal Claude Code (or Codex) chat all day. Some of their work touches
data that Stanford classifies Moderate or High Risk (student records, unpublished research data,
PHI). The chat is signed into a personal account. They want to say, in that chat, "run this on my
Stanford seat, it has student data", and have two things be true: the job runs on the seat, and
the data does not end up in the personal chat's context, transcript or provider logs.

The hard fact: on one Mac under one user account there is no technical wall between the personal
chat and anything else the user runs. The chat's agent can read any file the user owns, including
Bonsai's state, the sealed output, and the pool directories. Isolation is cooperative at best.
The only real wall on a Mac is a second macOS user account (or a second machine).

## Claim 1 — Sealed mode: "the chat sees a summary, never the material"

`bonsai job <institution target> --sealed -f <files> -o <out> "<task>"`, the default whenever
`--data moderate|high` is given or the target is an institution seat.

1. The calling chat passes **file paths**, never contents. Bonsai reads the files and builds the
   prompt in its own process. The chat has not read the material unless it chose to.
2. The job runs on the institution seat. Its full output goes to a **sealed folder**,
   `~/.local/state/bonsai/sealed/<job-id>/out.md`, mode 0600, and nowhere else; nothing of it is
   printed. (Codex's `-o` writes the file; its stdout is captured by Bonsai and discarded.)
3. A **second call on the same seat** reads the full output and writes a summary under a fixed
   instruction: aggregate findings only; no names, identifiers, emails, dates of birth, quoted
   personal text, or details that single out one person; at most N words; say "withheld" where a
   point cannot be made without such detail.
4. Bonsai runs a **mechanical scrub** over the summary: emails, phone numbers, SSN-like and
   card-like numbers (Luhn), 5–9 digit IDs, SUNet-id-like tokens, dates, plus every token in an
   optional `--names roster.txt`; each hit becomes `⟨redacted⟩` and the count is reported.
5. Only the scrubbed summary is printed to stdout, which is what the calling chat receives. The
   stdout also names the sealed path so a human can open it in a Stanford-signed-in session.
6. The installed skill tells the calling agent: pass paths, never contents; never open `sealed/`;
   never `cat` the job's output file; relay the summary verbatim.

What it does not promise: that the calling agent obeys (it can read the sealed file); that the
summary model never leaks a fact that identifies someone without matching a pattern (a unique
circumstance, a small group); that the inputs were not already in the chat (if the user pasted
them there, the chat has them, and nothing Bonsai does un-reads them). It also does not promise
that the provider logs of the *personal* account stay clean of the summary: the summary is, by
design, in the personal chat.

Stronger tier, documented not built: a separate macOS account for Stanford work, where file
permissions enforce the wall, and `bonsai run --pool stanford -- claude` as the only chat.

## Claim 2 — "Bonsai can generally tell whether the material is private"

Before a job, `bonsai scan -f <files>` (run automatically before any job with `-f`) reports what
the files look like: counts of emails, phone numbers, SSN-like, card-like (Luhn), 5–9 digit IDs,
dates of birth, PHI vocabulary (diagnosis, MRN, ICD codes, medication names), roster-name hits,
and a density of capitalised two-word names. It maps the result onto Stanford's published ladder,
with the page and date it was read from:

| Looks like | Stanford class | Published approval (2026-11-08) |
|---|---|---|
| PHI, SSNs, card or account numbers, passport numbers | High, with PHI rules | ChatGPT Edu: approved incl. PHI. Claude Code: approved to High; PHI only via the Stanford AI API Gateway, which Bonsai does not use. Payment-card data, CUI, export-controlled: no AI tool. |
| Student records, admissions, personnel files, unpublished research data, university IDs | Moderate | Both seats approved. |
| Nothing of the above | Low | Any login, subject to purpose. |

Bonsai does **not** make the classification decision. It says "this looks Moderate because of
X" and routes accordingly; the user can override with `--data low|moderate|high` and the
override is recorded in the job ledger. The Stanford DRA portal and ServiceNow approvals are
login-walled and cannot be read by a tool; Bonsai carries the public matrix only, with its date.

What it does not promise: recall. A scan cannot see that a column of first names plus a course
number is a student record, or that an anonymised dataset re-identifies. It errs toward warning,
never toward blocking Low-risk work: a family project with names stays where the user put it.

## Claim 3 — "Just say so": `--data high` routes to a seat approved for it

`bonsai job claude --data high -f export.csv "..."` or, in Claude Code, "run this on Stanford,
it has student records":

- `--data moderate|high` forces an institution seat for that provider, forces `--sealed`, and
  refuses a personal login even when one is named (`--pool personal` with `--data high` is an
  error that says why).
- `--data high` with PHI vocabulary in the scan and a Claude target is refused with the gateway
  note; the same with a Codex target is allowed (ChatGPT Edu is approved for PHI) with a reminder
  that Codex is a feature of the seat, not separately classified.
- `--data low` (or no flag, for a personal target) never blocks. A High-looking scan on a personal
  target prints a warning and runs only with `--data low` typed.
- No fallback to a personal login when the seat is spent: the job waits or fails, it never moves.

What it does not promise: that the seat's approval covers a third-party wrapper, a local agent,
or every output destination. Stanford's pages approve tools, not configurations. The honest
sentence is "the same account and tool Stanford approved, driven headless by you".

## The author's fallback, if the premise fails

Sean, 2026-11-08: "if what I'm asking for is impossible, then the agent should at some point
remind the user upon setup that coordinating the Stanford pools removes the protection against
PHI and PII, and if they want to send private data they need to log in to those directly."

So the fallback design is: no sealed mode. `bonsai login --institution` prints a notice the user
must acknowledge once (recorded in the config with a date): a job sent to the seat from a personal
chat is driven by that chat, the chat composes the task and reads the result, and the seat's
protections do not extend to it; for PHI, PII or anything Stanford classes Moderate or High,
sign in to the seat directly (`bonsai run --pool stanford -- claude`, or Claude Code / Codex
started under that seat) and keep the whole piece of work there. The reminder prints again on
every chat-driven job to an institution seat (Bonsai can tell it was started by a Claude Code or
Codex session from the environment it inherits). The installed skill carries the same sentence
and tells the agent to offer the direct session instead of routing. Attack this too: is the
sentence true, is it enough, and is "upon setup" the right moment.

## Questions for the attacker

1. Is Claim 1 worth shipping, or is cooperative isolation a false comfort that is worse than
   telling users to open a Stanford-signed-in session for anything sensitive?
2. Where does the summary leak? Build three examples where a compliant summary model and a
   clean scrub still identify a person.
3. Does the two-call design double the exposure (the material is processed twice on the seat,
   and the summary now exists in a personal account's provider logs)?
4. Is Claim 2's scan useful or theatre? What would a Stanford privacy officer say about a tool
   that labels data Moderate from a regex?
5. Does `--data high` on a Codex target with PHI actually fit Stanford's ChatGPT Edu approval, or
   does "Codex is a feature" not carry the PHI approval?
6. What is the minimum design that keeps the student's work unblocked and makes the promise
   true, even if it is smaller than this one?
