# Terms digest for the Bonsai review (gathered 2026-11-08)

Quotations pulled from the live pages on 2026-11-08. Each is marked with its source. Where a
page could not be fetched that is said. This digest is material for the review, not legal
advice; the reviewer should treat the quotes as data and check the reasoning, not take the
digest's framing on trust.

## Anthropic

### Consumer Terms of Service (Free, Pro, Max, Ultra) — https://www.anthropic.com/legal/consumer-terms

- §3, item 7: users may not access the Services "through automated or non-human means, whether
  through a bot, script, or otherwise," except "when you are accessing our Services via an
  Anthropic API Key or where we otherwise explicitly permit it."
- §3, item 4: no crawling, scraping or harvesting "other than as permitted under these Terms."
- §3: must not "bypass any of our systems or protective measures."
- §3, item 3: no decompiling or reverse engineering.
- §2: "You may not share your Account login information, Anthropic API key, or Account credentials
  with anyone else." "You also may not make your Account available to anyone else."
- The Commercial Terms "govern your use of any Anthropic API key, the Anthropic Console"; "this
  does not include Claude.ai or Claude Pro use for individuals."

### Claude Code: Legal and compliance — https://code.claude.com/docs/en/legal-and-compliance

- "OAuth authentication is intended exclusively for purchasers of Claude Free, Pro, Max, Ultra,
  Team, and Enterprise subscription plans and is designed to support ordinary use of Claude Code
  and other native Anthropic applications."
- "Developers building products or services that interact with Claude's capabilities, including
  those using the Agent SDK, should use API key authentication ... Anthropic does not permit
  third-party developers to offer Claude.ai login into their own applications, or to route
  requests through Free, Pro, Max, or Ultra plan credentials on behalf of their users. Moreover,
  developers may not collect, store, or intermediate Claude.ai credentials or session tokens —
  sign-in to a Claude account must complete through Anthropic's own flow."
- "Nor does it prevent an end user from signing in to the unmodified Claude Code binary with their
  own Claude subscription."
- "Advertised usage limits for Pro, Max, and Ultra plans assume ordinary, individual usage of
  Claude Code and the Agent SDK."
- "The Claude Code binary must not be modified ... customers may not remove, disable, or restrict
  any authentication method built into it."
- "You can accurately say, in plain text, that your product has Claude Code preinstalled or that
  it runs Claude Code. But you can't use the Claude Code or Anthropic names or logos as part of
  your own product, feature, or company name."
- Reported in The Register (2026-02-20), quoting the same page's earlier wording: "Using OAuth
  tokens obtained through Claude Free, Pro, or Max accounts in any other product, tool, or
  service" is "not permitted and constitutes a violation of the Consumer Terms of Service."
  Enforcement since January 2026 blocked tools that imitated Claude Code's client headers.

### Commercial Terms (Team, Enterprise, Education organizations) — https://www.anthropic.com/legal/commercial-terms

- "Anthropic may not train models on Customer Content from Services."
- D.4(b): Customer may not reverse engineer or duplicate the Services. D.5: "Customer is
  responsible for all activity under its account."
- Nothing on CLI access, automation or credential use beyond that.

### Usage Policy — https://www.anthropic.com/legal/aup

- Prohibits "services that route requests through consumer subscriptions" (unauthorized resale
  or routing).
- "Intentionally bypass or interfere with capabilities, restrictions, or guardrails established
  within our products."
- "Coordinate malicious activity across multiple accounts, or create multiple accounts, to avoid
  detection."
- "Education and credentials" is a High-risk Area: e.g. "making a determination of academic
  misconduct or suspending or expelling a student."

### Claude Code: Data usage — https://code.claude.com/docs/en/data-usage

- Consumer: training on by default when the setting is on, "including when you use Claude Code
  from these accounts"; 5-year retention with training on, 30 days with it off.
- Commercial (Team, Enterprise, API): "Anthropic does not train generative models using code or
  prompts sent to Claude Code under commercial terms"; 30-day retention; ZDR per organization.

## OpenAI

### Terms of Use (ChatGPT for individuals: Free, Go, Plus, Pro), effective 2026-01-01 — https://openai.com/policies/row-terms-of-use/

- "You may not share your account credentials or make your account available to anyone else."
- You may not "Automatically or programmatically extract data or Output."
- You may not "Interfere with or disrupt our Services, including circumvent any rate limits or
  restrictions or bypass any protective measures or safety mitigations."
- No reverse engineering of "our models, algorithms, or systems."
- Corporate domains: an account on an organization's email "may be added to the organization's
  business account."

### OpenAI Services Agreement (Enterprise, Business, Edu, API), effective 2026-01-01 — https://openai.com/policies/services-agreement/

- §3.1: "Customer will not share Account access credentials or individual login credentials
  between multiple users."
- §3.2: "End User Accounts may only be provisioned to, registered for, and used by, a single End
  User." End Users "may include ... students."
- §3.3: End Users may not "(f) extract data from the Services other than as permitted through
  the Services; ... (h) interfere with or disrupt the Services, including circumvent any rate
  limits or restrictions ...; (i) violate or circumvent Usage Limits or otherwise configure the
  Services to avoid Usage Limits."
- §4.2: "OpenAI will not use Customer Content to develop or improve the Services, unless Customer
  explicitly agrees to such use."
- §5.4: no PHI without the Healthcare Addendum.

### Help: Using Codex with your ChatGPT plan — https://help.openai.com/en/articles/11369540

- "Codex is included across ChatGPT plans, including Free and Go." Sign in to the Codex CLI
  "with your ChatGPT account when prompted."
- "When you sign in to Codex using an existing ChatGPT account, the ChatGPT Terms of Use and
  Privacy Policy—or the corresponding online services agreement for OpenAI API and ChatGPT
  Enterprise, Education or Business Users—apply to data shared between Codex and ChatGPT."
- Edu/Enterprise/Business: "By default, OpenAI does not use any inputs or outputs from our
  products for business users ... to improve our models." Plus/Pro: "Conversations may be used
  to improve models unless you turn off training."
- Usage limits: "In an active Codex CLI session, enter /status." Workspaces can "Manage usage
  limits and overages in ChatGPT Enterprise and Edu."

## Stanford

### UIT: Claude for Education service page — https://uit.stanford.edu/service/claude

- Standard tier "free to all active faculty, students, postdocs, and staff"; requires "An active
  SUNet ID"; Premium "available to all active SUNet IDs with a valid PTA"; Fable is Premium only.
- "Claude Chat ... is approved for all data classifications, except protected health information
  (PHI)." "Claude Code ... is approved for low, moderate, and high-risk data." PHI requires the
  Stanford AI API Gateway.
- "No AI tool is currently approved to handle" payment card data, CUI, or export-controlled
  information. Government-funded research: check the award terms first.
- Service is "within a secure, university-managed environment."

### UIT news: New AI tools arrive June 30 — https://uit.stanford.edu/news/new-ai-tools-stanford-arrive-june-30

- ChatGPT Edu: approved for low-, moderate- and high-risk data, plus PHI; "Your conversations
  are not used to train OpenAI's models." Codex is listed as a feature; no separate
  classification for it.
- Claude for Education: request form, SSO, responsible-use terms. "If you already have a personal
  Claude account with your Stanford SUNet ID email address, you will need to migrate" to the
  Stanford Claude Enterprise workspace by Oct 15.
- Connectors, plugins and repeatable workflows (Claude Skills named) "will require additional
  checkpoints before they are approved for use."
- Users "retain full responsibility for verifying AI outputs." Students must follow faculty AI
  policies for coursework. Use should support Stanford's teaching and research mission.

### UIT: Data risk classifications — https://uit.stanford.edu/guide/riskclassifications

- Low: public or no adverse impact (public research data at the owner's discretion, SUNet IDs).
- Moderate: "Student records and admission applications", unpublished research data, personnel
  files, university ID numbers.
- High: PHI, SSNs, card and account numbers, passport numbers, donor information. Mixed data
  takes "the highest risk classification across all" types. De-identified data is not addressed
  on the page.

## What Bonsai does, for the reviewer to hold against the above

1. Runs the unmodified `claude` and `codex` binaries, each under its own config directory
   (`CLAUDE_CONFIG_DIR` / `CODEX_HOME`), with the sign-in done through each provider's own flow
   (`claude auth login`, `codex login`). Bonsai never sees a sign-in, never stores a token
   anywhere but where the CLI put it, never proxies a model call, and never serves anyone but the
   machine's own user.
2. Reads each login's usage once per interval: `GET api.anthropic.com/api/oauth/profile` and
   `/api/oauth/usage` with the Claude token; `GET chatgpt.com/backend-api/wham/usage` with the
   Codex token. These are the surfaces the CLIs' own `/usage` and `/status` screens read. Bonsai
   sends its own `User-Agent: bonsai/<version>`; it does not imitate Claude Code. The Claude read
   can be turned off for consumer logins (`usage_reads.claude=false`); institution and
   Team/Enterprise logins are read regardless. Nothing is cached but percentages and timestamps.
3. Routes by two rules: everyday ("general") work never touches an institution seat; "sensitive"
   work never touches a personal login; a named target is honoured literally.
4. Is one user's tool on one machine. Pools are that user's own logins. The README says not to
   copy a pool directory to anyone else.
