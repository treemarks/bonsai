"""Synthetic tests: no network, no real logins. Run with the stock macOS python:
    /usr/bin/python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = tempfile.mkdtemp(prefix="bonsai-fakehome-")
# The suite may be started from inside an agent's session, whose marks would make every job here chat-driven.
for _mark in [k for k in os.environ if k in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "BONSAI_CHAT_DRIVEN")
              or (k.startswith("CODEX_") and k != "CODEX_HOME")]:
    del os.environ[_mark]
os.environ["BONSAI_POOLS_HOME"] = FAKE
os.environ["BONSAI_STATE"] = os.path.join(FAKE, "state")
os.environ["BONSAI_CONFIG"] = os.path.join(FAKE, "config.json")

spec = importlib.util.spec_from_loader("bonsai", loader=None, origin=os.path.join(HERE, "..", "bonsai"))
bonsai = importlib.util.module_from_spec(spec)
with open(os.path.join(HERE, "..", "bonsai"), encoding="utf-8") as f:
    exec(compile(f.read(), "bonsai", "exec"), bonsai.__dict__)
# Asking Claude Code for usage starts the real CLI: never from a test (a test that needs a reading supplies one).
bonsai.read_usage_now = lambda pool, timeout=None: None

NOW = time.time()


def iso(ts):
    return bonsai._iso(ts)


class Parsing(unittest.TestCase):
    def test_codex_rate_limits_from_app_server(self):
        res = {"rateLimits": {"planType": "edu", "rateLimitReachedType": None, "spendControlReached": False,
                              "primary": {"usedPercent": 0, "windowDurationMins": 10080, "resetsAt": int(NOW + 5 * 86400)},
                              "secondary": {"usedPercent": 37.5, "windowDurationMins": 300, "resetsAt": int(NOW + 3000)}}}
        r = bonsai.parse_codex_rate_limits(res)
        self.assertEqual(r["plan"], "edu")
        self.assertEqual(r["wk"], 0)
        self.assertEqual(r["5h"], 37.5)
        self.assertAlmostEqual(r["5h_at"], NOW + 3000, delta=2)
        self.assertNotIn("limited", r)
        res["rateLimits"]["rateLimitReachedType"] = "primary"
        self.assertTrue(bonsai.parse_codex_rate_limits(res)["limited"])
        self.assertEqual(bonsai.parse_codex_rate_limits({})["plan"], None)

    def test_when(self):
        self.assertAlmostEqual(bonsai._when_ts(1700000000), 1700000000)
        self.assertAlmostEqual(bonsai._when_ts(1700000000000), 1700000000)   # milliseconds
        self.assertAlmostEqual(bonsai._when_ts("2026-01-01T00:00:00Z"), 1767225600)
        self.assertIsNone(bonsai._when_ts("soon"))
        self.assertIsNone(bonsai._when_ts(None))

    def test_age_is_whole_minutes(self):
        self.assertEqual(bonsai._age(12), "<1m")
        self.assertEqual(bonsai._age(600), "10m")
        self.assertEqual(bonsai._age(3 * 3600 + 120), "3h02m")
        self.assertEqual(bonsai._age(2 * 86400 + 13 * 3600), "2d13h")

def rows():
    return {"at": NOW, "rows": [
        {"pool": "default", "provider": "codex", "state": "OK", "name": "personal", "institution": False,
         "wk": 60, "wk_at": NOW + 6 * 86400, "5h": 0, "5h_at": NOW + 3600},
        {"pool": "other@example.com", "provider": "codex", "state": "OK", "name": "example", "institution": False,
         "wk": 20, "wk_at": NOW + 2 * 86400, "5h": 0, "5h_at": NOW + 3600},
        {"pool": "spent@example.com", "provider": "codex", "state": "OK", "name": "spent", "institution": False,
         "wk": 95, "wk_at": NOW + 1 * 86400, "5h": 0, "5h_at": NOW + 3600},
        {"pool": "me@stanford.edu", "provider": "codex", "state": "OK", "name": "stanford", "institution": True,
         "wk": 10, "wk_at": NOW + 3 * 86400, "5h": 0, "5h_at": NOW + 3600},
        {"pool": "dead@example.com", "provider": "codex", "state": "re-login", "name": "dead", "institution": False},
        {"pool": "me@stanford.edu", "provider": "claude", "state": "OK", "name": "stanford", "institution": True,
         "wk": 30, "wk_at": NOW + 3 * 86400, "5h": 50, "5h_at": NOW + 3600},
    ]}


class Routing(unittest.TestCase):
    def test_auto_spends_whichever_login_resets_first(self):
        # prefer=soonest (the default): personal and institution alike, the room that resets first goes first.
        order = bonsai.route(rows(), "codex")
        self.assertEqual([e["pool"] for e in order], ["spent@example.com", "other@example.com", "me@stanford.edu", "default"])
        self.assertNotIn("dead@example.com", [e["pool"] for e in order])    # a dead login is not routed to
        self.assertEqual([e["pool"] for e in bonsai.route(rows(), "codex", "institution")][0], "me@stanford.edu")
        self.assertEqual([e["pool"] for e in bonsai.route(rows(), "codex", "personal")][-1], "me@stanford.edu")
        cfg = bonsai.load_config()
        self.assertEqual(cfg["prefer"], "soonest")
        self.assertEqual(bonsai.pick(rows(), "codex", None, dict(cfg, prefer="institution"))["pool"], "me@stanford.edu")
        self.assertEqual(bonsai.pick(rows(), "codex", None, dict(cfg, prefer="personal"))["pool"], "spent@example.com")
        self.assertEqual(bonsai.pick(rows(), "codex", None, cfg)["pool"], "spent@example.com")

    def test_the_floor_shrinks_as_the_reset_nears(self):
        # The same 5% left waits early in the week and is spent just before the reset: room left then is lost.
        early = {"rows": [{"pool": "a", "provider": "codex", "state": "OK", "wk": 95, "wk_at": NOW + 6 * 86400, "5h": 0}]}
        late = {"rows": [{"pool": "a", "provider": "codex", "state": "OK", "wk": 95, "wk_at": NOW + 6 * 3600, "5h": 0}]}
        self.assertTrue(bonsai.route(early, "codex", now=NOW)[0]["held"])
        self.assertFalse(bonsai.route(late, "codex", now=NOW)[0]["held"])
        empty = {"rows": [{"pool": "a", "provider": "codex", "state": "OK", "wk": 100, "wk_at": NOW + 60, "5h": 0}]}
        self.assertTrue(bonsai.route(empty, "codex", now=NOW)[0]["held"])        # nothing left waits, even at the reset
        self.assertAlmostEqual(bonsai.floor_now(7 * 86400), bonsai.MIN_USABLE_PCT)
        self.assertEqual(bonsai.floor_now(0), 0.0)

    def test_room_is_the_tighter_window(self):
        left, win = bonsai.room({"wk": 30, "5h": 50})
        self.assertEqual((left, win), (50.0, "5h"))

    def test_pick_named_login(self):
        cfg = bonsai.load_config()
        r = bonsai.pick(rows(), "codex", "stanford", cfg)
        self.assertEqual(r["pool"], "me@stanford.edu")
        r = bonsai.pick(rows(), "codex", "ME@stanford.edu", cfg)   # the full pool name, any case
        self.assertEqual(r["pool"], "me@stanford.edu")
        with self.assertRaises(SystemExit):
            bonsai.pick(rows(), "codex", "me@stan", cfg)   # prefixes are not matched
        with self.assertRaises(SystemExit):
            bonsai.pick(rows(), "codex", "nobody", cfg)
        claude_only_seat = {"rows": [r for r in rows()["rows"] if r["provider"] == "claude"]}
        self.assertEqual(bonsai.pick(claude_only_seat, "claude", None, cfg)["pool"], "me@stanford.edu")   # auto spends seats

    def test_second_workspace_does_not_capture_the_first_target(self):
        # Astra, sign-in pass: with `stanford` and `stanford-pro` both present (one e-mail, two
        # workspaces), `stanford` must still mean the first pool, and the e-mail must not be ambiguous.
        cfg = bonsai.load_config()
        st = rows()
        st["rows"].append({"pool": "stanford-pro", "provider": "codex", "state": "OK", "name": "stanford-pro",
                           "institution": True, "account": "me@stanford.edu",
                           "wk": 10, "wk_at": NOW + 86400, "5h": 0, "5h_at": NOW + 3600})
        for r in st["rows"]:
            if r["pool"] == "me@stanford.edu" and r["provider"] == "codex":
                r["account"] = "me@stanford.edu"
        self.assertEqual(bonsai.pick(st, "codex", "stanford", cfg)["pool"], "me@stanford.edu")
        self.assertEqual(bonsai.pick(st, "codex", "stanford-pro", cfg)["pool"], "stanford-pro")
        self.assertEqual(bonsai.pick(st, "codex", "me@stanford.edu", cfg)["pool"], "me@stanford.edu")
        with self.assertRaises(SystemExit):
            bonsai.pick(st, "codex", "stanf", cfg)

    def test_reserved_names_are_not_pools(self):
        for word in ("auto", "codex", "openai", "chatgpt", "anthropic", "astra", "Claude"):
            with self.assertRaises(SystemExit):
                bonsai.check_pool_name(word)
        self.assertEqual(bonsai.check_pool_name("stanford-pro"), "stanford-pro")

    def test_targets(self):
        cfg = bonsai.load_config()
        self.assertEqual(bonsai.resolve_target("stanford-codex", cfg, None), ("codex", "stanford", None))
        self.assertEqual(bonsai.resolve_target("personal-claude", cfg, None), ("claude", "personal", None))
        self.assertEqual(bonsai.resolve_target("astra", cfg, None), ("codex", None, "gpt-6-astra"))
        self.assertEqual(bonsai.resolve_target("astra@stanford", cfg, None), ("codex", "stanford", "gpt-6-astra"))
        self.assertEqual(bonsai.resolve_target("opus", cfg, None), ("claude", None, "claude-opus-5-5"))
        self.assertEqual(bonsai.resolve_target("codex", cfg, "gpt-5-mini"), ("codex", None, "gpt-5-mini"))
        # The company, the product and the CLI are one seat: Stanford OpenAI = Stanford ChatGPT = Stanford Codex.
        for word in ("stanford-openai", "stanford-chatgpt", "stanford-gpt", "Stanford-OpenAI"):
            self.assertEqual(bonsai.resolve_target(word, cfg, None), ("codex", "stanford", None), word)
        self.assertEqual(bonsai.resolve_target("stanford-anthropic", cfg, None), ("claude", "stanford", None))
        self.assertEqual(bonsai.resolve_target("stanford-pro-codex", cfg, None), ("codex", "stanford-pro", None))
        self.assertEqual(bonsai.resolve_target("openai", cfg, None), ("codex", None, None))
        self.assertEqual(bonsai.resolve_target("anthropic", cfg, None), ("claude", None, None))
        with self.assertRaises(SystemExit):
            bonsai.resolve_target("-codex", cfg, None)  # a suffix with no login before it is not a target
        with self.assertRaises(SystemExit):
            bonsai.resolve_target("mystery", cfg, None)
        with self.assertRaises(SystemExit):
            bonsai.resolve_model(cfg, "claude", "astra")   # a codex alias on a claude target

    def test_headless_argv(self):
        a = bonsai.headless_argv("codex", "gpt-6-astra", "low", "/tmp/o.md", "/tmp")
        self.assertIn("read-only", a)
        self.assertEqual(a[-1], "-")
        self.assertIn('model_reasoning_effort="low"', a)
        a = bonsai.headless_argv("claude", "claude-haiku-5-5", "low", None, "/tmp")
        self.assertIn("dontAsk", a)
        self.assertIn("-p", a)

    def test_pick_signed_in_only_login(self):
        # Usage reads off for Claude: one personal login reads `signed-in`; auto picks it.
        st = {"at": NOW, "rows": [{"pool": "default", "provider": "claude", "state": "signed-in",
                                   "name": "personal", "institution": False}]}
        self.assertEqual(bonsai.pick(st, "claude", None, bonsai.load_config())["pool"], "default")
        self.assertIn("not ranked", bonsai.route(st, "claude")[0]["why"])     # what --dry-run says of it

    def test_child_env_drops_parent_marks(self):
        os.environ["CLAUDECODE"] = "1"
        os.environ["CLAUDE_CONFIG_DIR"] = "/elsewhere"
        os.environ["ANTHROPIC_API_KEY"] = "sk-test"
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "tok"
        os.environ["OPENAI_API_KEY"] = "sk-test"
        os.environ["SSL_CERT_FILE"] = "/etc/ssl/campus.pem"
        env = bonsai.child_env("codex", "me@stanford.edu")
        for k in ("CLAUDECODE", "CLAUDE_CONFIG_DIR", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY"):
            self.assertNotIn(k, env)
        self.assertEqual(env.get("SSL_CERT_FILE"), "/etc/ssl/campus.pem")  # an IT CA bundle is not a credential
        self.assertEqual(env["CODEX_HOME"], os.path.join(FAKE, ".codex-pools", "me@stanford.edu"))
        # The default pool is the CLI's own home, reached by leaving the variable unset.
        env = bonsai.child_env("claude", "default")
        self.assertNotIn("CLAUDE_CONFIG_DIR", env)
        env = bonsai.child_env("codex", "default")
        self.assertNotIn("CODEX_HOME", env)
        for k in ("CLAUDECODE", "CLAUDE_CONFIG_DIR", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY"):
            os.environ.pop(k, None)

    def test_chat_driven_detection(self):
        for k in [k for k in os.environ if k in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT") or (k.startswith("CODEX_") and k != "CODEX_HOME")]:
            os.environ.pop(k, None)
        self.assertFalse(bonsai.chat_driven())
        os.environ["CLAUDECODE"] = "1"
        self.assertTrue(bonsai.chat_driven())
        os.environ.pop("CLAUDECODE")
        os.environ["CODEX_SANDBOX"] = "seatbelt"
        self.assertTrue(bonsai.chat_driven())
        os.environ.pop("CODEX_SANDBOX")

    def test_a_stop_and_a_mismatched_sign_in_are_refused(self):
        cfg = bonsai.load_config()
        st = rows()
        st["rows"][0]["state"] = "LIMITED"       # personal codex at its limit
        self.assertNotIn("default", [e["pool"] for e in bonsai.route(st, "codex")])
        with self.assertRaises(SystemExit):      # a named login is not a way around a stop
            bonsai.pick(st, "codex", "personal", cfg)
        st = rows()
        st["rows"][1]["mismatch"] = "roommate@example.test"      # signed in as another account
        self.assertNotIn("other@example.com", [e["pool"] for e in bonsai.route(st, "codex")])
        with self.assertRaises(SystemExit):
            bonsai.pick(st, "codex", "example", cfg)
        self.assertEqual(bonsai.pick(rows(), "codex", "example", cfg)["pool"], "other@example.com")   # the same name, healthy
        for dead in ("re-login", "no-login", "locked", "cli-missing", "bad-credfile", "unauthorized", "offline"):
            st = rows()
            st["rows"][1]["state"] = dead               # a named login that cannot answer is refused, not tried
            with self.assertRaises(SystemExit):
                bonsai.pick(st, "codex", "example", cfg)
        st = rows()
        st["rows"][1]["wk"] = 100                       # nothing left this week: naming it is not a way past the limit
        with self.assertRaises(SystemExit):
            bonsai.pick(st, "codex", "example", cfg)
        for half_read in ({"incomplete_usage": True}, {"wk": None, "5h": None}):
            st = rows()
            st["rows"][1].update(half_read)             # a reading that cannot say what is left
            with self.assertRaises(SystemExit):
                bonsai.pick(st, "codex", "example", cfg)

    def test_claude_jobs_run_without_tools(self):
        a = bonsai.headless_argv("claude", "claude-haiku-5-5", "low", None, "/tmp")
        self.assertIn("--tools", a)
        self.assertEqual(a[a.index("--tools") + 1], "")
        self.assertIn("--strict-mcp-config", a)
        self.assertIn("--safe-mode", a)                 # the login's own CLAUDE.md, skills and hooks stay out

    def test_there_is_no_run(self):
        # Ruled 2026-11-08, "Keep job only": `run` started a command with none of a job's isolation, and a terminal is
        # no proof that a person is typing; a job is the one way Bonsai starts a model.
        import io, contextlib
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                bonsai.main(["run", "--pool", "personal", "--", "codex"])

    def test_tool_name(self):
        self.assertEqual(bonsai._tool_name(r"C:\Users\x\codex.exe"), "codex" if os.sep == "\\" else r"c:\users\x\codex")
        self.assertEqual(bonsai._tool_name("/opt/homebrew/bin/codex"), "codex")
        self.assertEqual(bonsai._tool_name("codex.cmd"), "codex")


class Discovery(unittest.TestCase):
    def test_discovers_pools_and_renders_board(self):
        os.makedirs(os.path.join(FAKE, ".codex-pools", "me@stanford.edu"), exist_ok=True)
        os.makedirs(os.path.join(FAKE, ".claude"), exist_ok=True)
        pools = bonsai.discover_pools()
        self.assertIn(("codex", "me@stanford.edu", os.path.join(FAKE, ".codex-pools", "me@stanford.edu")), pools)
        self.assertIn(("claude", "default", os.path.join(FAKE, ".claude")), pools)
        # A codex pool with no auth.json is no-login; nothing is probed over the network.
        row = bonsai.probe_codex("me@stanford.edu", os.path.join(FAKE, ".codex-pools", "me@stanford.edu"))
        self.assertEqual(row["state"], "no-login")
        text = bonsai.render(rows(), bonsai.load_config(), bonsai.Paint(False), 110, 300)
        self.assertIn("ACCOUNTS", text)
        self.assertIn("MACHINE", text)
        self.assertIn("stanford", text)
        self.assertNotIn("⌂", text)                               # no marks or legend: the fleet gauge's plain rows
        self.assertIn("re-login", text)
        for line in text.splitlines():
            self.assertNotIn("\n", line)   # one line per row
        self.assertNotIn("Bearer", text)

    def test_jobs_ledger(self):
        bonsai.record_job({"id": "abc", "at": iso(NOW), "provider": "codex", "pool": "default", "label": "t", "pid": 999999})
        jobs = bonsai.read_jobs()
        self.assertTrue(jobs[-1].get("lost"))
        bonsai.record_job({"id": "abc", "exit": 0, "seconds": 1.0})
        self.assertEqual(bonsai.read_jobs()[-1]["exit"], 0)

    def test_config_set_keeps_dots_in_emails(self):
        import argparse
        cfg = bonsai.load_config()
        a = argparse.Namespace(set=['logins.me@stanford.edu={"name":"stanford","institutions":{"codex":true}}',
                                    'models.astra=["codex","gpt-6-astra"]', "interval=600"])
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            bonsai.cmd_config(a, cfg)
        saved = bonsai.load_config()
        self.assertTrue(saved["logins"]["me@stanford.edu"]["institutions"]["codex"])
        self.assertEqual(saved["models"]["astra"], ["codex", "gpt-6-astra"])
        self.assertEqual(saved["interval"], 600)
        self.assertTrue(bonsai.is_institution(saved, "me@stanford.edu", "codex"))
        self.assertFalse(bonsai.is_institution(saved, "me@stanford.edu", "claude"))   # per provider
        with self.assertRaises(SystemExit):                                           # unknown keys are refused
            bonsai.cmd_config(argparse.Namespace(set=['access_token="x"']), bonsai.load_config())

    def test_annotate_reads_config_not_cache(self):
        cfg = bonsai.load_config()
        cfg.setdefault("logins", {})["me@stanford.edu"] = {"name": "farm", "institutions": {"codex": True}}
        state = bonsai.annotate({"rows": [{"pool": "me@stanford.edu", "provider": "codex", "institution": False, "name": "x"},
                                          {"pool": "me@stanford.edu", "provider": "claude", "institution": True, "name": "x"}]}, cfg)
        self.assertEqual(state["rows"][0]["name"], "farm")
        self.assertTrue(state["rows"][0]["institution"])
        self.assertFalse(state["rows"][1]["institution"])

    def test_declared_protected_data_is_refused_everywhere(self):
        for chat in (True, False):          # a Terminal is not a sign of approval either
            with self.assertRaises(SystemExit) as cm:
                bonsai._data_gate("high", "codex")
            self.assertIn("stopped (--data high); nothing was sent", str(cm.exception))
        with self.assertRaises(SystemExit) as cm:
            bonsai._data_gate("phi", "claude")
        self.assertIn("AI API Gateway", str(cm.exception))
        self.assertIsNone(bonsai._data_gate("low", "codex"))       # never blocks low
        self.assertIsNone(bonsai._data_gate(None, "codex"))        # undeclared flows
        with self.assertRaises(SystemExit):
            bonsai._data_gate("restricted", "codex")                # never, anywhere

    def test_pass_gates_before_reading_material(self):
        import argparse
        p = os.path.join(FAKE, "secret.md")
        with open(p, "w") as f:
            f.write("material")
        reads = []
        real = bonsai._read_file_bounded
        bonsai._read_file_bounded = lambda path: reads.append(path) or real(path)
        try:
            a = argparse.Namespace(target="codex", model=None, pool=None, effort=None, round=1,
                                   data="high", file=[p], out=None, dry_run=True, brief=None, prompt=None)
            with self.assertRaises(SystemExit):
                bonsai.cmd_pass(a, bonsai.load_config())
        finally:
            bonsai._read_file_bounded = real
        self.assertEqual(reads, [])

    def test_notice_is_shown_once_per_version(self):
        import io, contextlib
        cfg = bonsai.load_config()
        cfg.pop("notice_shown", None)  # the tests share one fake home; start before any showing
        bonsai.save_config(cfg)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            bonsai.ensure_notice(cfg, "job")
            bonsai.ensure_notice(cfg, "job")
        self.assertEqual(err.getvalue().count("Before your first job"), 1)
        self.assertEqual(bonsai.load_config()["notice_shown"]["version"], bonsai.NOTICE_VERSION)

    def test_the_guides_example_address_is_refused_before_anything_starts(self):
        import argparse
        for email in ("you@stanford.edu", "YOU@stanford.edu", "YOUR_NAME@stanford.edu", "<you>@stanford.edu"):
            a = argparse.Namespace(email=email, name=None, pool=None, institution=True, sso=False, claude=True, codex=False)
            with self.assertRaises(SystemExit) as caught:
                bonsai.cmd_login(a, bonsai.load_config())
            self.assertIn("the guide's example; use your own Stanford address", str(caught.exception))

    def test_notice_is_printed_once_at_the_first_institution_sign_in(self):
        import io, contextlib, shutil, subprocess, builtins, argparse
        saved = (shutil.which, subprocess.call, builtins.input)
        shutil.which = lambda name: "/usr/local/bin/" + name
        subprocess.call = lambda argv, env=None: 0
        builtins.input = lambda prompt="": self.fail("nothing is typed to sign in (ruled: the typed acknowledgement goes)")
        cfg = bonsai.load_config()
        cfg.pop("notice_shown", None)
        cfg["logins"] = {}                 # the tests share one fake home: start this one from no logins
        bonsai.save_config(cfg)
        try:
            def login(email, provider, pool=None, name=None, institution=True):
                a = argparse.Namespace(email=email, name=name, pool=pool, institution=institution, sso=False,
                                       claude=provider == "claude", codex=provider == "codex")
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    rc = bonsai.cmd_login(a, bonsai.load_config())
                return rc, out.getvalue()
            rc, out = login("a@stanford.edu", "claude")
            self.assertEqual(rc, 0)
            self.assertIn("Before your first job", out)
            self.assertIn("private (incognito) window", out)            # before the browser opens
            self.assertIn("if the browser shows a code, close it", out)                    # the code the browser may still show
            cfg = bonsai.load_config()
            cfg.pop("notice_shown", None)
            bonsai.save_config(cfg)
            rc, out = login("p@example.test", "codex", institution=False)    # a personal sign-in shows it too
            self.assertIn("Before your first job", out)
            rc, out = login("a@stanford.edu", "codex")        # same e-mail, other provider
            rc2, out2 = login("b@othercollege.edu", "codex")  # a different institution login
            self.assertEqual((rc, rc2), (0, 0))
            self.assertNotIn("Before your first job", out + out2)
            # One e-mail, a second workspace: its own pool directory and its own name on the board.
            rc3, _ = login("a@stanford.edu", "codex", pool="stanford-pro", name="stanford-pro")
            self.assertEqual(rc3, 0)
            logins = bonsai.load_config()["logins"]
            self.assertEqual(logins["stanford-pro"]["name"], "stanford-pro")
            self.assertEqual(logins["a@stanford.edu"]["name"], "stanford")
            self.assertTrue(os.path.isdir(bonsai.pool_dir("codex", "stanford-pro")))
            # A label that already names another pool is refused before anything is created.
            with self.assertRaises(SystemExit):
                login("c@stanford.edu", "codex", pool="c-pool", name="stanford")
            # The sign-in that completed is checked against the e-mail asked for: a mismatch marks the pool, and
            # jobs never use it until it is signed in again as the right account.
            real_identity = bonsai.login_identity
            bonsai.login_identity = lambda provider, pool, d: {"email": "roommate@example.test", "plan": "plus"}
            try:
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    rc4, _ = login("d@stanford.edu", "codex")
                self.assertEqual(rc4, 1)
                self.assertIn("roommate@example.test", err.getvalue())
                self.assertIn("in a private window", err.getvalue())
                self.assertIn("codex logout", err.getvalue())
                self.assertEqual(bonsai.load_config()["logins"]["d@stanford.edu"]["mismatch"]["codex"], "roommate@example.test")
            finally:
                bonsai.login_identity = real_identity
            rc5, _ = login("d@stanford.edu", "codex")         # signed in again, as the right account: the mark goes
            self.assertEqual(rc5, 0)
            self.assertNotIn("codex", bonsai.load_config()["logins"]["d@stanford.edu"].get("mismatch") or {})
            # --device-auth reaches codex, and only codex.
            seen = []
            subprocess.call = lambda argv, env=None: seen.append(argv) or 0
            a = argparse.Namespace(email="e@stanford.edu", name=None, pool=None, institution=False,
                                   sso=False, device_auth=True, claude=False, codex=True)
            with contextlib.redirect_stdout(io.StringIO()):
                bonsai.cmd_login(a, bonsai.load_config())
            self.assertEqual(seen[-1][-2:], ["login", "--device-auth"])
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                bonsai.ensure_notice(bonsai.load_config(), "job")  # the first job: no second printing
            self.assertEqual(err.getvalue(), "")
            self.assertEqual(bonsai.load_config()["notice_shown"]["how"], "login")
        finally:
            shutil.which, subprocess.call, builtins.input = saved

    def test_request_pages_are_the_universitys(self):
        self.assertEqual(bonsai.request_url("claude"), "https://uit.stanford.edu/service/claude")
        self.assertEqual(bonsai.request_url("codex"), "https://uit.stanford.edu/service/openai-chatgpt-edu")

    def test_codex_identity_labels(self):
        import base64
        claims = {"email": "s@stanford.edu", "https://api.openai.com/auth": {"chatgpt_plan_type": "edu_pro",
                                                                            "chatgpt_account_id": "acct-0000d78a"}}
        body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
        ident = bonsai.codex_identity({"id_token": "h.%s.s" % body, "account_id": "acct-0000d78a", "access_token": "x"})
        self.assertEqual(ident, {"email": "s@stanford.edu", "plan": "edu_pro", "workspace": "…d78a"})
        self.assertEqual(bonsai.describe_identity(ident), "s@stanford.edu · plan edu_pro · workspace id …d78a")
        self.assertEqual(bonsai.codex_identity({"access_token": "x"}), {"email": None, "plan": None, "workspace": None})

    def test_update_outside_a_checkout_says_so(self):
        import argparse, io, contextlib
        real = bonsai.repo_dir
        bonsai.repo_dir = lambda: None
        try:
            with self.assertRaises(SystemExit) as cm:
                bonsai.cmd_update(argparse.Namespace(dry_run=False), bonsai.load_config())
            self.assertIn("not a git checkout", str(cm.exception))
        finally:
            bonsai.repo_dir = real
        # A shell that points git elsewhere stops the update before any git command runs: checked the same way in a
        # clone or not, with no git call and no network (the suite is offline wherever a student runs it).
        bonsai.repo_dir = lambda: "/nonexistent/bonsai"
        os.environ["GIT_DIR"] = "/elsewhere/.git"
        try:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(bonsai.cmd_update(argparse.Namespace(dry_run=False, yes=False), bonsai.load_config()), 2)
            self.assertIn("GIT_DIR", err.getvalue())
        finally:
            del os.environ["GIT_DIR"]
            bonsai.repo_dir = real

    def test_display_text_escapes_controls(self):
        self.assertEqual(bonsai.display_text("a\x1b[2Jb\n"), "a\\u001b[2Jb\\u000a")
        self.assertEqual(bonsai.display_text("plain", 3), "pla")

    def test_names(self):
        cfg = bonsai.load_config()
        self.assertEqual(bonsai.login_name(cfg, "default"), "personal")
        self.assertEqual(bonsai.login_name(cfg, "x@stanford.edu"), "stanford")
        self.assertEqual(bonsai.login_name(cfg, "x@example.com"), "example")



class ConfigWrites(unittest.TestCase):
    def test_config_set_keeps_a_sign_in_made_meanwhile(self):
        stale = bonsai.load_config()                 # what `bonsai config` loaded when it started
        bonsai.update_config(lambda fresh: fresh.setdefault("logins", {}).__setitem__(
            "seat@x.example", {"name": "seat", "institutions": {"codex": True}}))       # a sign-in finishes
        args = type("A", (), {"set": ["interval=600"]})()
        with contextlib.redirect_stdout(io.StringIO()):
            bonsai.cmd_config(args, stale)
        saved = bonsai.load_config()
        self.assertEqual(saved["interval"], 600)
        self.assertTrue(saved["logins"]["seat@x.example"]["institutions"]["codex"])

    def test_two_sign_ins_at_once_both_stay_recorded(self):
        # Two processes loaded the config before either signed in; each records its own login afterwards.
        a_cfg, b_cfg = bonsai.load_config(), bonsai.load_config()
        def mark(provider):
            return lambda fresh: fresh.setdefault("logins", {}).setdefault("me@x.example", {}).setdefault(
                "institutions", {}).__setitem__(provider, True)
        bonsai.update_config(mark("claude"))
        bonsai.update_config(mark("codex"))
        saved = bonsai.load_config()["logins"]["me@x.example"]["institutions"]
        self.assertEqual(saved, {"claude": True, "codex": True})
        self.assertNotIn("me@x.example", a_cfg.get("logins", {}))


class AgentSides(unittest.TestCase):
    """Bonsai driven by Claude Code or by Codex: the skill installs for both, `other` means the other family,
    and inside Codex's sandbox a job stops with one clear line (a live run on 2026-11-08 failed with a bare
    `exit 1`: the sandbox hides the network and the Keychain)."""

    MARKS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED",
             "CODEX_THREAD_ID", "CODEX_MANAGED_BY_NPM")

    def setUp(self):
        self.saved = {k: os.environ.pop(k) for k in self.MARKS if k in os.environ}

    def tearDown(self):
        for k in self.MARKS:
            os.environ.pop(k, None)
        os.environ.update(self.saved)

    def test_other_is_the_other_family(self):
        cfg = bonsai.load_config()
        models = cfg.get("models") or {}
        os.environ["CLAUDECODE"] = "1"
        self.assertEqual(bonsai.caller_family(), "claude")
        self.assertEqual(bonsai.resolve_target("other", cfg, None), ("codex", None, models["sol"][1]))
        del os.environ["CLAUDECODE"]
        os.environ["CODEX_THREAD_ID"] = "t"
        self.assertEqual(bonsai.caller_family(), "codex")
        self.assertEqual(bonsai.resolve_target("other", cfg, None), ("claude", None, models["opus"][1]))
        self.assertEqual(bonsai.resolve_target("other@stanford", cfg, None), ("claude", "stanford", models["opus"][1]))
        self.assertEqual(bonsai.resolve_target("other", cfg, "claude-haiku-5-5"), ("claude", None, "claude-haiku-5-5"))

    def test_other_needs_a_known_side(self):
        cfg = bonsai.load_config()
        self.assertIsNone(bonsai.caller_family())               # neither mark: a person in Terminal
        with self.assertRaises(SystemExit):
            bonsai.resolve_target("other", cfg, None)
        os.environ["CLAUDECODE"] = "1"
        os.environ["CODEX_SANDBOX"] = "seatbelt"                 # both: refuse rather than guess
        self.assertIsNone(bonsai.caller_family())

    def test_codex_sandbox_stops_a_job_before_any_probe(self):
        import argparse
        os.environ["CODEX_SANDBOX"] = "seatbelt"
        os.environ["CODEX_SANDBOX_NETWORK_DISABLED"] = "1"
        self.assertTrue(bonsai.in_codex_sandbox())
        probed = []
        real = bonsai.refresh
        bonsai.refresh = lambda *a, **k: probed.append(1) or {"rows": []}
        try:
            a = argparse.Namespace(target="codex", model=None, pool=None, effort=None, data=None,
                                   file=None, out=None, dry_run=False, brief=None, prompt="hi")
            with self.assertRaises(SystemExit) as cm:
                bonsai.cmd_job(a, bonsai.load_config(), prompt="hi")
            self.assertIn("Codex's sandbox", str(cm.exception))
            self.assertEqual(probed, [])
        finally:
            bonsai.refresh = real

    def test_skill_frontmatter_is_strict_yaml(self):
        head = bonsai.SKILL.split("---")[1]
        desc = [l for l in head.splitlines() if l.startswith("description:")][0][len("description:"):].strip()
        # A YAML double-quoted scalar: Codex's loader rejected the unquoted one (": " inside it).
        self.assertTrue(desc.startswith('"') and desc.endswith('"'), desc[:60])
        self.assertNotIn('"', desc[1:-1])
        self.assertNotIn("\\", desc)
        self.assertIn("Which side you are on", bonsai.SKILL)
        self.assertIn("bonsai pass other", bonsai.SKILL)

    def test_install_skill_writes_each_agent(self):
        import argparse, contextlib, io, shutil
        home = os.path.join(FAKE, "skillhome")
        os.makedirs(os.path.join(home, ".claude"), exist_ok=True)
        os.makedirs(os.path.join(home, ".codex"), exist_ok=True)
        saved_home, saved_which = bonsai.HOME, shutil.which
        bonsai.HOME = home
        shutil.which = lambda name, *a, **k: None
        try:
            targets = bonsai.skill_targets()
            self.assertEqual([t[0] for t in targets], ["Claude Code", "Codex"])
            self.assertEqual(targets[1][1], os.path.join(home, ".agents", "skills", "bonsai-route", "SKILL.md"))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(bonsai.cmd_install_skill(argparse.Namespace(), bonsai.load_config()), 0)
            for _, path in targets:
                with open(path, encoding="utf-8") as f:
                    self.assertEqual(f.read(), bonsai.SKILL)
                self.assertEqual(bonsai.skill_state(path), "matches")
            with open(targets[1][1], "a", encoding="utf-8") as f:   # an edited Codex skill is left alone
                f.write("\nmine\n")
            with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(bonsai.cmd_install_skill(argparse.Namespace(), bonsai.load_config()), 2)
            self.assertIn("NOT UPDATED", out.getvalue())
            self.assertTrue(os.path.isfile(targets[1][1] + ".new"))
        finally:
            bonsai.HOME, shutil.which = saved_home, saved_which



class JobLifecycle(unittest.TestCase):
    """A job is bounded and stoppable (a Codex session's finding, 2026-11-08: a Claude reply ran six minutes with no
    way to tell slow from stuck, and the only way out was killing the process by hand)."""

    def _run(self, script, **kw):
        out = os.path.join(FAKE, "out-%d.md" % abs(hash(script)))
        with open(out, "w", encoding="utf-8") as f:
            f.write("previous\n")
        import contextlib, io
        err = io.StringIO()
        real_require = bonsai.require            # a plain Python child stands in for the CLI; the guard is for the CLIs
        bonsai.require = lambda *a, **k: None
        try:
            with contextlib.redirect_stderr(err):
                code = bonsai.run_job([sys.executable, "-c", script], "claude", "default", "test", stdin_text="x",
                                      capture_to=out, **kw)
        finally:
            bonsai.require = real_require
        with open(out, encoding="utf-8") as f:
            body = f.read()
        last = [j for j in bonsai.read_jobs(None) if "exit" in j][-1]
        return code, body, last, err.getvalue()

    def test_a_silent_job_times_out_and_publishes_nothing(self):
        code, body, last, err = self._run("import time; time.sleep(30)", timeout_minutes=0.02)
        self.assertEqual((code, last["outcome"]), (124, "timeout"))
        self.assertEqual(body, "previous\n")                 # the old answer is left alone
        self.assertIn("limit", err)
        self.assertNotIn("lost", [j.get("lost") for j in bonsai.read_jobs(None) if j.get("id") == last["id"]])

    def test_a_slow_job_that_finishes_publishes_with_a_newline(self):
        code, body, last, err = self._run("import sys, time; sys.stdin.read(); time.sleep(0.2); sys.stdout.write('ok')",
                                          timeout_minutes=1)
        self.assertEqual((code, last["outcome"], body), (0, "ok", "ok\n"))
        self.assertIn("started", err)

    def test_a_failed_job_keeps_its_messages_private(self):
        code, body, last, err = self._run("import sys; sys.stderr.write('secret prompt text'); sys.exit(3)", timeout_minutes=1)
        self.assertEqual((code, last["outcome"]), (3, "failed"))
        self.assertNotIn("secret prompt text", err)
        path = os.path.join(os.environ["BONSAI_STATE"], "job-%s.err" % last["id"])
        with open(path, encoding="utf-8") as f:
            self.assertIn("secret prompt text", f.read())
        if os.name != "nt":                                  # Windows keeps it private by ACL, not mode bits
            self.assertEqual(oct(os.stat(path).st_mode & 0o777), oct(0o600))

    def test_cancel_stops_the_job_and_its_children(self):
        import threading, time
        result = {}
        t = threading.Thread(target=lambda: result.update(zip(("code", "body", "last", "err"), self._run(
            "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
            "time.sleep(60)", timeout_minutes=2))))
        t.start()
        running = []
        for _ in range(100):
            running = [j for j in bonsai.read_jobs(None) if "exit" not in j and j.get("child")]
            if running:
                break
            time.sleep(0.05)
        self.assertTrue(running, "the job never recorded its process")
        child = running[-1]["child"]
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(bonsai.cancel_job(running[-1]["id"][:6]), 0)
        t.join(30)
        self.assertEqual((result["code"], result["last"]["outcome"]), (130, "cancelled"))
        self.assertEqual(result["body"], "previous\n")
        if os.name == "nt":                                  # taskkill /T took the tree; the job's own pid is gone
            import subprocess
            listed = subprocess.run(["tasklist", "/FI", "PID eq %d" % child, "/NH"], capture_output=True, text=True).stdout
            self.assertNotIn(" %d " % child, " %s " % listed)
        else:
            with self.assertRaises(ProcessLookupError):      # the whole group is gone, grandchild included
                os.killpg(child, 0)

    def test_a_cancel_recorded_in_the_ledger_stops_the_job(self):
        # Windows' path, taken on any platform: no signal is sent to a pid read back from the ledger; the process that
        # started the job sees the request within a second and stops its own child.
        import threading, time
        result = {}
        t = threading.Thread(target=lambda: result.update(zip(("code", "body", "last", "err"), self._run(
            "import time; time.sleep(60)", timeout_minutes=2))))
        t.start()
        running = []
        for _ in range(100):
            running = [j for j in bonsai.read_jobs(None) if "exit" not in j and j.get("child")]
            if running:
                break
            time.sleep(0.05)
        self.assertTrue(running, "the job never recorded its process")
        bonsai.record_job({"id": running[-1]["id"], "cancel": "now"})
        t.join(30)
        self.assertEqual((result["code"], result["last"]["outcome"]), (130, "cancelled"))
        self.assertEqual(result["body"], "previous\n")

    def test_a_prompt_over_a_megabyte_reaches_the_job_whole(self):
        # Astra, 2026-11-09: a pipe fed one second at a time stalled at 16,384 of 400,000 bytes on Python 3.9.
        out = os.path.join(FAKE, "big.md")
        real = bonsai.require
        bonsai.require = lambda *a, **k: None
        import contextlib, io
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                code = bonsai.run_job([sys.executable, "-c", "import sys; print(len(sys.stdin.read()))"], "claude",
                                      "default", "big", stdin_text="x" * 1_500_000, capture_to=out, timeout_minutes=1)
        finally:
            bonsai.require = real
        with open(out, encoding="utf-8") as f:
            self.assertEqual((code, f.read()), (0, "1500000\n"))

    def test_an_ok_job_without_a_file_prints_its_answer_and_no_failure(self):
        import contextlib, io
        real, err, std = bonsai.require, io.StringIO(), io.StringIO()
        bonsai.require = lambda *a, **k: None
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(std):
                code = bonsai.run_job([sys.executable, "-c", "print('ok')"], "codex", "default", "t", timeout_minutes=1)
        finally:
            bonsai.require = real
        self.assertEqual((code, std.getvalue()), (0, "ok\n"))
        self.assertNotIn("failed", err.getvalue())

    @unittest.skipIf(os.name == "nt", "POSIX process groups")
    def test_a_stop_reaches_what_the_job_started_even_when_the_job_itself_exits(self):
        # Astra, 2026-11-09: a grandchild that ignores TERM outlived a leader that exited at once.
        import threading, time
        pidfile = os.path.join(FAKE, "grandchild.pid")
        script = ("import os, signal, subprocess, sys, time; "
                  "g = subprocess.Popen([sys.executable, '-c', 'import signal, time; signal.signal(signal.SIGTERM, "
                  "signal.SIG_IGN); time.sleep(60)']); open(%r, 'w').write(str(g.pid)); time.sleep(60)" % pidfile)
        saved, bonsai.STOP_GRACE_SECONDS = bonsai.STOP_GRACE_SECONDS, 0.5
        result = {}
        t = threading.Thread(target=lambda: result.update(zip(("code", "body", "last", "err"), self._run(script, timeout_minutes=2))))
        try:
            t.start()
            for _ in range(200):
                if os.path.exists(pidfile) and os.path.getsize(pidfile):
                    break
                time.sleep(0.05)
            running = [j for j in bonsai.read_jobs(None) if "exit" not in j and j.get("child")]
            bonsai.record_job({"id": running[-1]["id"], "cancel": "now"})
            t.join(30)
        finally:
            bonsai.STOP_GRACE_SECONDS = saved
        self.assertEqual(result["last"]["outcome"], "cancelled")
        with open(pidfile) as f:
            pid = int(f.read())
        for _ in range(40):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            self.fail("the grandchild that ignores TERM is still running")

    def test_a_cancel_that_lands_as_the_job_exits_ok_publishes_nothing(self):
        # Astra, 2026-11-09: a cancel seen only on a wait timeout let a job that exited 0 meanwhile publish.
        calls = []
        saved = bonsai.cancel_requested
        bonsai.cancel_requested = lambda jid: calls.append(jid) or len(calls) > 1     # not before the spawn; then yes
        try:
            code, body, last, err = self._run("print('the answer')", timeout_minutes=1)
        finally:
            bonsai.cancel_requested = saved
        self.assertEqual((code, last["outcome"], body), (130, "cancelled", "previous\n"))

    def test_cancel_refuses_what_it_cannot_name(self):
        for bad in ("", "zz", "abc"):
            with self.assertRaises(SystemExit):
                bonsai.cancel_job(bad)
        with self.assertRaises(SystemExit):
            bonsai.cancel_job("ffff0000")


class JobPaths(unittest.TestCase):
    """`bonsai job` end to end with a stand-in CLI: the job is registered before any probe, Codex's -o is staged and
    published only on success, and a Claude job with no usage event says so."""

    def _job(self, provider, script, out=None, refresh=None, timeout=1, read=None):
        import argparse, contextlib, io
        now = bonsai._now()
        rows = [{"pool": "default", "name": "personal", "provider": provider, "state": "OK" if provider == "codex" else
                 "signed-in", "wk": 10.0, "wk_at": now + 86400, "5h": 1.0, "5h_at": now + 3600}]
        saved = (bonsai.refresh, bonsai.require, bonsai.headless_argv, bonsai.read_usage_now)
        bonsai.refresh = refresh or (lambda cfg, force=False: {"rows": [dict(r) for r in rows]})
        bonsai.read_usage_now = read or bonsai.read_usage_now
        bonsai.require = lambda *a, **k: None
        bonsai.headless_argv = lambda prov, model, effort, o, cwd, web=False: [sys.executable, "-c", script, o or ""]
        if read is None:
            bonsai.record_reading("default", {"status": "", "source": "usage"})     # a fresh reading: no /usage read here
        elif os.path.exists(os.path.join(os.environ["BONSAI_STATE"], "claude_usage.json")):
            os.remove(os.path.join(os.environ["BONSAI_STATE"], "claude_usage.json"))         # no reading: it is read
        a = argparse.Namespace(target=provider, model=None, pool=None, effort=None, data=None, file=None, out=out,
                               dry_run=False, brief=None, prompt="hi", timeout=timeout)
        err, std = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(std):
                try:
                    code = bonsai.cmd_job(a, bonsai.load_config(), prompt="hi")
                except SystemExit as e:
                    code = e
        finally:
            bonsai.refresh, bonsai.require, bonsai.headless_argv, bonsai.read_usage_now = saved
        return code, std.getvalue(), err.getvalue(), [j for j in bonsai.read_jobs(None) if "exit" in j][-1]

    def test_codex_writes_a_private_file_that_is_published_only_on_success(self):
        out = os.path.join(FAKE, "codex-out.md")
        script = "import sys; open(sys.argv[1], 'w').write('the answer'); print('the answer, again')"
        code, std, err, last = self._job("codex", script, out)
        with open(out, encoding="utf-8") as f:
            self.assertEqual((code, f.read(), last["outcome"]), (0, "the answer\n", "ok"))
        self.assertNotEqual(os.path.dirname(os.path.abspath(out)), "")
        self.assertNotIn("the answer", std)                        # the chat gets no second copy
        self.assertNotIn("failed", err)
        self.assertFalse(os.path.exists(os.path.join(os.environ["BONSAI_STATE"], "job-%s.answer" % last["id"])))

    def test_a_codex_job_stopped_after_writing_publishes_nothing(self):
        out = os.path.join(FAKE, "codex-kept.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write("previous\n")
        script = "import sys, time; open(sys.argv[1], 'w').write('half'); time.sleep(60)"
        code, std, err, last = self._job("codex", script, out, timeout=0.02)
        with open(out, encoding="utf-8") as f:
            self.assertEqual((code, f.read(), last["outcome"]), (124, "previous\n", "timeout"))

    def test_a_claude_job_with_no_usage_event_says_unavailable(self):
        script = "import json; print(json.dumps({'type': 'result', 'result': 'ok'}))"
        code, std, err, last = self._job("claude", script)
        self.assertEqual((code, std), (0, "ok\n"))
        self.assertIn("usage unavailable", err)

    def test_a_cancel_during_preparation_stops_the_job_before_it_is_sent(self):
        def refresh(cfg, force=False):
            mine = [j for j in bonsai.read_jobs(None) if "exit" not in j][-1]
            bonsai.record_job({"id": mine["id"], "cancel": "now"})   # the job exists before the probes
            return {"rows": []}
        code, std, err, last = self._job("codex", "raise SystemExit('never started')", refresh=refresh)
        self.assertIn("cancelled before it started", str(code))
        self.assertEqual(last["outcome"], "cancelled")
        self.assertNotIn("child", last)

    @unittest.skipIf(os.name == "nt", "POSIX process groups")
    def test_a_cancel_stops_what_preparation_started(self):
        # Astra, 2026-11-09: a hung probe's CLI outlived the cancelled job.
        import subprocess, time
        pidfile = os.path.join(FAKE, "probe.pid")
        if os.path.exists(pidfile):
            os.remove(pidfile)

        def refresh(cfg, force=False):
            mine = [j for j in bonsai.read_jobs(None) if "exit" not in j][-1]
            bonsai.record_job({"id": mine["id"], "cancel": "now"})
            subprocess.run([sys.executable, "-c", "import os, time; open(%r, 'w').write(str(os.getpid())); "
                            "time.sleep(60)" % pidfile])                # a probe that hangs
            return {"rows": []}
        code, std, err, last = self._job("codex", "raise SystemExit('never started')", refresh=refresh)
        self.assertIn("cancelled before it started", str(code))
        for _ in range(100):
            if os.path.exists(pidfile) and os.path.getsize(pidfile):
                break
            time.sleep(0.05)
        with open(pidfile) as f:
            pid = int(f.read())
        for _ in range(40):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            self.fail("the hung probe is still running after the job ended")

    def test_a_login_that_once_worked_keeps_its_last_good_row_through_failures(self):
        saved = (bonsai.discover_pools, bonsai.probe_claude)
        states = iter(["signed-in", "no-login", "no-login"])
        bonsai.discover_pools = lambda: [("claude", "default", FAKE)]
        bonsai.probe_claude = lambda pool, d, cfg: {"provider": "claude", "pool": pool, "state": next(states),
                                                     "plan": "max", "account": "a@x"}
        try:
            first = bonsai.probe_all(bonsai.load_config())
            second = bonsai.probe_all(bonsai.load_config(), first)
            third = bonsai.probe_all(bonsai.load_config(), second)
        finally:
            bonsai.discover_pools, bonsai.probe_claude = saved
        self.assertEqual(second["rows"][0]["last_good"]["plan"], "max")
        self.assertEqual(third["rows"][0]["last_good"]["plan"], "max")

    def test_preparation_that_hangs_stops_at_the_deadline(self):
        # Astra, 2026-11-09: the probes and the lock they wait on ran outside --timeout.
        import time
        t0 = time.time()
        code, std, err, last = self._job("codex", "raise SystemExit('never started')", timeout=0.02,
                                         refresh=lambda cfg, force=False: time.sleep(30) or {"rows": []})
        self.assertIn("ran past its limit before it started", str(code))
        self.assertEqual(last["outcome"], "timeout")
        self.assertLess(time.time() - t0, 10)

    def test_a_cancel_during_a_failed_usage_read_still_stops_the_job(self):
        def read(pool, timeout=None):
            mine = [j for j in bonsai.read_jobs(None) if "exit" not in j][-1]
            bonsai.record_job({"id": mine["id"], "cancel": "now"})
            return None                                              # the read failed
        code, std, err, last = self._job("claude", "raise SystemExit('never started')", read=read)
        self.assertIn("cancelled before it started", str(code))
        self.assertNotIn("child", last)


class Readings(unittest.TestCase):
    """Claude usage in Claude Code's own words (no stored token): a job's rate_limit_event and `/usage`; a login with
    no reading is unknown, never full; low and ran-out are said in one line; Codex's usage limit too."""

    def setUp(self):
        try:
            os.remove(os.path.join(os.environ["BONSAI_STATE"], "claude_usage.json"))
        except OSError:
            pass

    def test_the_usage_report_reads_the_account_rows_by_kind(self):
        # The shape `claude -p /usage --output-format stream-json --verbose` printed on 2026-11-08 (Claude Code 2.1.303).
        report = {"rate_limits": {"limits": [
            {"kind": "weekly_all", "group": "weekly", "percent": 52, "resets_at": "2026-11-09T15:00:00.199556+00:00",
             "scope": None, "severity": "normal", "is_active": False},
            {"kind": "weekly_scoped", "group": "weekly", "percent": 100, "resets_at": "2026-11-09T15:00:00.199694+00:00",
             "scope": {"model": {"display_name": "Fable"}}, "severity": "critical", "is_active": True}],
            "extra_usage": {"is_enabled": False}}}
        r = bonsai.from_report(report)
        self.assertEqual((r["wk"], r["wk_at"]), (52.0, 1794236400.199556))
        self.assertNotIn("limited_until", r)                     # one model's cap is not the login's room
        full = bonsai.from_report({"rate_limits": {"limits": [
            {"kind": "session", "percent": 100, "resets_at": "2026-11-09T15:00:00+00:00"}]}})
        self.assertEqual((full["5h"], full["limited_until"]), (100.0, 1794236400.0))
        for bad in (None, {}, {"rate_limits": {"limits": "x"}}, {"rate_limits": {"limits": [{"kind": "spend", "percent": 9}]}}):
            self.assertIsNone(bonsai.from_report(bad))

    def test_a_job_event_becomes_a_reading(self):
        info = {"status": "allowed_warning", "resetsAt": 1794236400, "rateLimitType": "seven_day",
                "unifiedWindows": {"seven_day": {"utilization": 0.93, "resetsAt": 1794236400}}}
        r = bonsai.from_event(info)
        self.assertEqual((r["wk"], r["wk_at"], r["status"]), (93.0, 1794236400.0, "allowed_warning"))
        out = bonsai.from_event(dict(info, status="rejected", rateLimitType="five_hour", resetsAt=1794200000))
        self.assertEqual(out["limited_until"], 1794200000.0)     # it waits until the reset that stopped it
        stream = "\n".join(json.dumps(d) for d in ({"type": "system"}, {"type": "rate_limit_event", "rate_limit_info": info},
                                                    {"type": "result", "result": "ok"}))
        self.assertEqual(bonsai.read_stream(stream), ("ok", info))

    def test_readings_are_shown_never_ranked_and_a_login_that_ran_out_waits(self):
        now = bonsai._now()
        bonsai.record_reading("a@x", {"wk": 90.0, "wk_at": now + 86400, "status": "allowed", "source": "job"})
        bonsai.record_reading("b@x", {"wk": 100.0, "wk_at": now + 86400, "status": "rejected", "source": "job",
                                      "limited_until": now + 3600})
        bonsai.record_reading("c@x", {"wk": 10.0, "wk_at": now - 60, "status": "allowed", "source": "usage"})
        bonsai.record_reading("e@x", {"wk": 5.0, "wk_at": now + 86400, "status": "allowed", "source": "usage"})
        pools = ("a@x", "b@x", "c@x", "d@x", "e@x")
        rows = {"rows": [{"pool": p, "provider": "claude", "state": "signed-in"} for p in pools]}
        before = [e["pool"] for e in bonsai.route(rows, "claude")]
        st = bonsai.apply_readings(rows)
        by = {r["pool"]: r for r in st["rows"]}
        self.assertEqual((by["a@x"]["state"], by["a@x"]["reading"]["wk"]), ("signed-in", 90.0))
        self.assertNotIn("wk", by["a@x"])                       # shown beside the row, not ranked on
        self.assertEqual(by["b@x"]["state"], "LIMITED")
        self.assertEqual(by["c@x"]["reading"].get("wk"), None)   # its reset has passed: that reading says nothing now
        self.assertNotIn("reading", by["d@x"])                  # no reading: unavailable, never full
        self.assertEqual([e["pool"] for e in bonsai.route(st, "claude")], [p for p in before if p != "b@x"])
        self.assertFalse(bonsai.stale("a@x") or not bonsai.stale("d@x"))
        board = bonsai.render(st, {}, bonsai.Paint(False), 100, 300)
        self.assertIn("unavailable", [l for l in board.splitlines() if "d@x" in l][0])
        bonsai.record_reading("b@x", {"wk": 20.0, "status": "allowed", "source": "usage"})
        self.assertEqual({r["pool"]: r for r in bonsai.apply_readings(st)["rows"]}["b@x"]["state"], "signed-in")

    def test_a_cached_reading_never_moves_a_job_to_another_login(self):
        # Astra, 2026-11-09: a board open that read "ran out" made the next auto job take another login, silently.
        import argparse, contextlib, io
        now = bonsai._now()
        bonsai.record_reading("default", {"wk": 100.0, "wk_at": now + 3600, "status": "rejected", "source": "job",
                                          "limited_until": now + 3600})
        rows = [{"pool": "default", "name": "personal", "provider": "claude", "state": "signed-in"},
                {"pool": "b@x", "name": "other", "provider": "claude", "state": "signed-in"}]
        saved = (bonsai.refresh, bonsai.read_usage_now)
        bonsai.refresh = lambda cfg, force=False: bonsai.apply_readings({"rows": [dict(r) for r in rows]})
        bonsai.read_usage_now = lambda pool, timeout=None: self.fail("the reading is fresh")
        try:
            a = argparse.Namespace(target="claude", model=None, pool=None, effort=None, data=None, file=None, out=None,
                                   dry_run=True, brief=None, prompt="hi")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    bonsai.cmd_job(a, bonsai.load_config(), prompt="hi")
        finally:
            bonsai.refresh, bonsai.read_usage_now = saved
        self.assertIn("personal has run out of Claude usage; it resets in", str(caught.exception))

    def test_low_and_ran_out_are_said(self):
        now = bonsai._now()
        self.assertIn("running low", bonsai.limit_line("me", {"wk": 80.0, "wk_at": now + 3600}))
        self.assertIn("running low", bonsai.limit_line("me", {"status": "allowed_warning"}))
        self.assertIn("run out", bonsai.limit_line("me", {"status": "rejected", "limited_until": now + 3600}))
        self.assertIsNone(bonsai.limit_line("me", {"wk": 40.0, "status": "allowed"}))
        self.assertIn("five hours", bonsai.limit_line("me", {"wk": 10.0, "5h": 85.0}))
        self.assertEqual(bonsai.limit_line("me", {"wk": 40.0, "status": "allowed"}, always=True),
                         "bonsai: me: 40% of the week used, as last reported by Claude Code.")
        msg = "ERROR: You've hit your usage limit. Upgrade to Pro or try again at Nov 10th, 2026 3:00 PM."
        self.assertIn("hit your usage limit", bonsai.ran_out_text(msg))
        self.assertIsNone(bonsai.ran_out_text("some other failure"))

    def test_a_claude_job_publishes_the_answer_and_keeps_the_reading(self):
        import contextlib, io
        info = {"status": "allowed", "unifiedWindows": {"seven_day": {"utilization": 0.25, "resetsAt": bonsai._now() + 86400}}}
        lines = [{"type": "rate_limit_event", "rate_limit_info": info}, {"type": "result", "result": "the answer"}]
        script = "import sys; sys.stdin.read(); print(%r)" % "\n".join(json.dumps(d) for d in lines)
        out = os.path.join(FAKE, "streamed.md")
        real = bonsai.require
        bonsai.require = lambda *a, **k: None
        try:
            def after(outcome, output, messages):
                answer, ev = bonsai.read_stream(output or "")
                bonsai.record_reading("s@x", bonsai.from_event(ev))
                return answer
            with contextlib.redirect_stderr(io.StringIO()):
                code = bonsai.run_job([sys.executable, "-c", script], "claude", "default", "t", stdin_text="x",
                                      capture_to=out, timeout_minutes=1, after=after)
        finally:
            bonsai.require = real
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as f:
            self.assertEqual(f.read(), "the answer\n")
        self.assertEqual(bonsai.readings()["s@x"]["wk"], 25.0)

    def test_a_job_reads_usage_first_when_its_login_has_no_recent_reading(self):
        import argparse, contextlib, io
        asked = []
        saved = (bonsai.refresh, bonsai.read_usage_now)
        rows = {"rows": [{"pool": "default", "name": "personal", "provider": "claude", "state": "signed-in"},
                         {"pool": "b@x", "name": "other", "provider": "claude", "state": "signed-in"}]}
        bonsai.refresh = lambda cfg, force=False: {"rows": [dict(r) for r in rows["rows"]]}
        bonsai.read_usage_now = lambda pool, timeout=None: asked.append(pool) or bonsai.record_reading(
            pool, {"wk": 100.0, "wk_at": bonsai._now() + 3600, "limited_until": bonsai._now() + 3600, "source": "usage"})
        try:
            a = argparse.Namespace(target="claude", model=None, pool=None, effort=None, data=None, file=None, out=None,
                                   dry_run=True, brief=None, prompt="hi")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:   # it has run out: the job stops, no other login
                    bonsai.cmd_job(a, bonsai.load_config(), prompt="hi")
            self.assertEqual(asked, ["default"])
            self.assertIn("personal has run out of Claude usage; it resets in", str(caught.exception))
            self.assertIn("--pool", str(caught.exception))
        finally:
            bonsai.refresh, bonsai.read_usage_now = saved


class WindowsPaths(unittest.TestCase):
    """What Windows does differently, shown on any machine; the Windows CI run exercises it for real."""

    def setUp(self):
        from unittest.mock import patch
        self.patch = patch
        self.d = tempfile.mkdtemp()
        self.script = os.path.join(self.d, "node_modules", "@openai", "codex", "bin", "codex.js")
        self.node = os.path.join(self.d, "node.exe")

    def test_npm_codex_starts_its_own_script_with_node_never_a_batch_file(self):
        os.makedirs(os.path.dirname(self.script))
        for f in (self.script, self.node):
            open(f, "w").close()
        shim = os.path.join(self.d, "codex.cmd")
        with open(shim, "w") as f:                               # what the batch file says is never read
            f.write('REM "%dp0%\\elsewhere\\other.js"\r\n')
        which = {"codex": shim, "claude": os.path.join(self.d, "claude.cmd"), "node": "C:\\x\\node.cmd"}.get
        with self.patch.dict(bonsai.__dict__, IS_WIN=True), self.patch.object(bonsai.shutil, "which", which):
            self.assertEqual(bonsai.cli_command("codex"), [self.node, self.script])
            self.assertIsNone(bonsai.cli_command("claude"))     # npm's Claude Code: its native installer instead
            os.unlink(self.node)
            self.assertIsNone(bonsai.cli_command("codex"))      # a node that is itself a batch file is not used

    def test_the_guard_takes_only_npm_codex_own_script_as_codex(self):
        with bonsai.private_cwd() as cwd, self.patch.dict(bonsai.__dict__, cli_command=lambda n: [self.node, self.script]):
            argv = bonsai._codex_job_argv("gpt-x", "low", None, cwd)
            self.assertEqual(argv[:3], [self.node, self.script, "exec"])
            self.assertEqual(bonsai.codex_problems(argv, cwd), [])
            elsewhere = os.path.join(self.d, "elsewhere", "codex.js")
            self.assertNotEqual(bonsai.codex_problems([self.node, elsewhere] + argv[2:], cwd), [])
            self.assertNotEqual(bonsai.codex_problems([self.node, os.path.join(self.d, "other.js")] + argv[2:], cwd), [])

    def test_windows_logout_lines_are_powershell_and_restore_the_variable(self):
        with self.patch.dict(bonsai.__dict__, IS_WIN=True):
            line = bonsai._codex_logout_line("s@example.org")
        self.assertTrue(line.startswith("$was=$env:CODEX_HOME; $env:CODEX_HOME='"), line)
        self.assertTrue(line.endswith("; codex logout; $env:CODEX_HOME=$was"), line)

    def test_windows_device_names_are_no_pool(self):
        with self.patch.dict(bonsai.__dict__, IS_WIN=True):
            for name in ("CON", "nul.x@example.com", "com1", "COM¹", "lpt².txt", "CONIN$", "a@example.com.", "a@example.com "):
                with self.subTest(name=name), self.assertRaises(SystemExit):
                    bonsai.check_pool_name(name)
            self.assertEqual(bonsai.check_pool_name("console@example.com"), "console@example.com")


class SecurityGuards(unittest.TestCase):
    """What the security audit asked for (2026-11-09): sign-in files never ride -f, a job starts only from a resolved
    CLI, Codex's tool-giving features are off, and an answer printed to a terminal cannot drive it."""

    def test_f_refuses_sign_in_files_however_reached(self):
        import argparse
        d = tempfile.mkdtemp()
        link = os.path.join(d, "notes.md")
        os.symlink(os.path.join(bonsai.SECRET_DIRS[1], "x@example.com", "auth.json"), link)
        for path in (link, os.path.join(d, "auth.json"), os.path.join(d, "AUTH.JSON")):
            with self.subTest(path=path), self.assertRaises(SystemExit) as cm:
                bonsai.read_prompt(argparse.Namespace(prompt="review", file=[path]))
            self.assertIn("sign-in or key file", str(cm.exception))

    def test_f_opens_no_link_put_in_place_after_the_check(self):
        if not hasattr(os, "O_NOFOLLOW"):
            self.skipTest("no O_NOFOLLOW here")
        d = tempfile.mkdtemp()
        secret, link = os.path.join(d, "secret.txt"), os.path.join(d, "notes.md")
        with open(secret, "w") as f:
            f.write("token")
        os.symlink(secret, link)                      # what a swap after the realpath check would leave
        with self.assertRaises(SystemExit):
            bonsai._open_regular(link)

    def test_codex_jobs_turn_off_the_tool_features(self):
        argv = bonsai._codex_job_argv("gpt-x", "low", None, "/tmp/x")
        for feature in ("view_image", "computer_use", "browser_use", "apps", "plugins", "multi_agent", "multi_agent_v2", "hooks"):
            self.assertIn("features.%s=false" % feature, argv)
        self.assertIn("agents.enabled=false", argv)          # a model's metadata cannot turn sub-agents back on

    def test_a_job_never_starts_from_a_bare_name(self):
        import io
        real = bonsai.require
        bonsai.require = lambda *a, **k: None
        try:
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                code = bonsai.run_job(["codex", "exec", "-"], "codex", "default", "t", stdin_text="hi", cwd=tempfile.mkdtemp())
        finally:
            bonsai.require = real
        self.assertNotEqual(code, 0)

    def test_a_stopped_preparation_starts_nothing_afterwards(self):
        import threading
        real, go, seen = subprocess.Popen, threading.Event(), []

        def step():
            go.wait(5)
            try:
                seen.append(subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"]))
            except OSError:
                seen.append("refused")
        j = bonsai.Job("codex", "t", 0.001)          # past its limit at once
        try:
            with self.assertRaises(SystemExit):
                j.within(step)
            go.set()
            for _ in range(50):
                if seen:
                    break
                time.sleep(0.05)
        finally:
            for p in seen:
                if p != "refused":
                    p.kill()
            subprocess.Popen = real
        self.assertEqual(seen, ["refused"])

    def test_web_is_the_cached_search_and_only_on_request(self):
        cwd = tempfile.mkdtemp()
        plain = bonsai._codex_job_argv("gpt-x", "low", None, cwd)
        web = bonsai._codex_job_argv("gpt-x", "low", None, cwd, web=True)
        self.assertIn('web_search="disabled"', plain)
        self.assertIn('web_search="cached"', web)
        self.assertNotIn('web_search="disabled"', web)
        self.assertNotIn('web_search="live"', web)
        self.assertIn("features.code_mode_host=false", plain)                 # the JS host: on only for --web
        self.assertNotIn("features.code_mode_host=false", web)
        self.assertIn("features.shell_snapshot=false", web)
        self.assertIn('web_search="disabled" is not set', bonsai.codex_problems(web, cwd))   # not without --web
        self.assertFalse([p for p in bonsai.codex_problems(web, cwd, web=True) if "web_search" in p])
        self.assertTrue([p for p in bonsai.codex_problems(plain, cwd, web=True) if "web_search" in p])
        on = [x.replace("features.code_mode_host=false", "features.code_mode_host=true") for x in plain]
        self.assertTrue([p for p in bonsai.codex_problems(on, cwd) if "code-mode host" in p])
        with self.assertRaises(bonsai.LaunchRefused):
            bonsai.require("claude", ["claude"], cwd, web=True)

    def test_web_takes_no_files_and_no_claude(self):
        import argparse
        base = dict(model=None, pool=None, effort=None, data=None, dry_run=True, out=None, timeout=None, web=True)
        one = "--web takes the question as its one argument"
        for target, files, prompt, said in (("chatgpt", ["notes.md"], "hi", one), ("chatgpt", None, "-", one),
                                            ("chatgpt", None, None, one), ("claude", None, "hi", "is for ChatGPT")):
            with self.subTest(target=target, files=files, prompt=prompt), self.assertRaises(SystemExit) as cm:
                bonsai.cmd_job(argparse.Namespace(target=target, file=files, prompt=prompt, **base), {})
            self.assertIn(said, str(cm.exception))

    def test_update_merges_only_the_commit_that_was_reviewed(self):
        import argparse, io
        if not shutil.which("git"):
            self.skipTest("git not installed")
        root = tempfile.mkdtemp()
        origin, copy = os.path.join(root, "origin"), os.path.join(root, "copy")
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "init.defaultBranch=main"]
        run = lambda *a, cwd=root: subprocess.run(git + list(a), cwd=cwd, capture_output=True, check=True)
        run("init", "-q", origin)
        run("commit", "-q", "--allow-empty", "-m", "reviewed", cwd=origin)
        run("clone", "-q", origin, copy)
        run("commit", "-q", "--allow-empty", "-m", "arrived later", cwd=origin)
        before = subprocess.run(["git", "-C", copy, "rev-parse", "HEAD"], capture_output=True, text=True).stdout
        real = bonsai.repo_dir
        bonsai.repo_dir = lambda: copy
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = bonsai.cmd_update(argparse.Namespace(dry_run=False, yes=True, to="0000000"), {})
        finally:
            bonsai.repo_dir = real
        self.assertEqual(code, 2)
        self.assertIn("not 0000000 you reviewed", err.getvalue())
        self.assertIn("not github.com/treemarks/bonsai", err.getvalue())
        self.assertEqual(before, subprocess.run(["git", "-C", copy, "rev-parse", "HEAD"], capture_output=True, text=True).stdout)


if __name__ == "__main__":
    unittest.main()
