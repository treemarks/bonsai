"""Synthetic tests: no network, no real logins. Run with the stock macOS python:
    /usr/bin/python3 -m unittest discover -s tests
"""
import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = tempfile.mkdtemp(prefix="bonsai-fakehome-")
os.environ["BONSAI_POOLS_HOME"] = FAKE
os.environ["BONSAI_STATE"] = os.path.join(FAKE, "state")
os.environ["BONSAI_CONFIG"] = os.path.join(FAKE, "config.json")

spec = importlib.util.spec_from_loader("bonsai", loader=None, origin=os.path.join(HERE, "..", "bonsai"))
bonsai = importlib.util.module_from_spec(spec)
with open(os.path.join(HERE, "..", "bonsai")) as f:
    exec(compile(f.read(), "bonsai", "exec"), bonsai.__dict__)

NOW = time.time()


def iso(ts):
    return bonsai._iso(ts)


class Parsing(unittest.TestCase):
    def test_claude_usage(self):
        d = {"five_hour": {"utilization": 9.0, "resets_at": iso(NOW + 3600)},
             "seven_day": {"utilization": 66.5, "resets_at": iso(NOW + 2 * 86400)},
             "limits": [{"kind": "weekly_scoped", "utilization": 100,
                         "scope": {"model": {"display_name": "Fable"}}, "resets_at": iso(NOW + 86400)}]}
        r = bonsai.parse_claude_usage(d)
        self.assertEqual(r["5h"], 9.0)
        self.assertEqual(r["wk"], 66.5)
        self.assertAlmostEqual(r["wk_at"], NOW + 2 * 86400, delta=2)
        self.assertEqual(r["model_caps"]["fable"]["used"], 100)
        # A utilization of 1.0 is one percent, never "100%": the scale is 0-100.
        self.assertEqual(bonsai.parse_claude_usage({"five_hour": {"utilization": 1.0}})["5h"], 1.0)

    def test_codex_usage(self):
        d = {"plan_type": "edu", "rate_limit": {
            "primary_window": {"used_percent": 12.3, "reset_at": int(NOW + 7200), "limit_window_seconds": 18000},
            "secondary_window": {"used_percent": 40, "reset_at": int(NOW + 5 * 86400), "limit_window_seconds": 604800},
            "limit_reached": False}}
        r = bonsai.parse_codex_usage(d)
        self.assertEqual(r["plan"], "edu")
        self.assertEqual(r["5h"], 12.3)
        self.assertEqual(r["wk"], 40)
        self.assertAlmostEqual(r["wk_at"], NOW + 5 * 86400, delta=2)
        self.assertNotIn("limited", r)
        d["rate_limit"]["limit_reached"] = True
        self.assertTrue(bonsai.parse_codex_usage(d)["limited"])

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

    def test_keychain_service_name(self):
        self.assertEqual(bonsai.keychain_service("/x/.claude", True), "Claude Code-credentials")
        svc = bonsai.keychain_service("/Users/me/.claude-pools/me@stanford.edu", False)
        self.assertTrue(svc.startswith("Claude Code-credentials-") and len(svc) == len("Claude Code-credentials-") + 8)


def rows():
    return {"at": NOW, "rows": [
        {"pool": "default", "provider": "codex", "state": "OK", "name": "personal", "institution": False,
         "wk": 60, "wk_at": NOW + 6 * 86400, "5h": 0, "5h_at": NOW + 3600},
        {"pool": "other@gmail.com", "provider": "codex", "state": "OK", "name": "gmail", "institution": False,
         "wk": 20, "wk_at": NOW + 2 * 86400, "5h": 0, "5h_at": NOW + 3600},
        {"pool": "spent@gmail.com", "provider": "codex", "state": "OK", "name": "spent", "institution": False,
         "wk": 95, "wk_at": NOW + 1 * 86400, "5h": 0, "5h_at": NOW + 3600},
        {"pool": "me@stanford.edu", "provider": "codex", "state": "OK", "name": "stanford", "institution": True,
         "wk": 10, "wk_at": NOW + 3 * 86400, "5h": 0, "5h_at": NOW + 3600},
        {"pool": "dead@gmail.com", "provider": "codex", "state": "re-login", "name": "dead", "institution": False},
        {"pool": "me@stanford.edu", "provider": "claude", "state": "OK", "name": "stanford", "institution": True,
         "wk": 30, "wk_at": NOW + 3 * 86400, "5h": 50, "5h_at": NOW + 3600},
    ]}


class Routing(unittest.TestCase):
    def test_general_order_soonest_reset_first_held_last(self):
        order = bonsai.route(rows(), "codex", "general")
        self.assertEqual([e["pool"] for e in order], ["other@gmail.com", "default", "spent@gmail.com"])
        self.assertTrue(order[-1]["held"])
        self.assertNotIn("me@stanford.edu", [e["pool"] for e in order])   # a seat never carries general work
        self.assertNotIn("dead@gmail.com", [e["pool"] for e in order])    # a dead login is not routed to

    def test_sensitive_order_is_institution_only(self):
        order = bonsai.route(rows(), "codex", "sensitive")
        self.assertEqual([e["pool"] for e in order], ["me@stanford.edu"])
        self.assertEqual(bonsai.route(rows(), "claude", "general"), [])

    def test_room_is_the_tighter_window(self):
        left, win = bonsai.room({"wk": 30, "5h": 50})
        self.assertEqual((left, win), (50.0, "5h"))

    def test_pick_named_overrides_kind(self):
        cfg = bonsai.load_config()
        r = bonsai.pick(rows(), "codex", "general", "stanford", cfg)
        self.assertEqual(r["pool"], "me@stanford.edu")
        r = bonsai.pick(rows(), "codex", "general", "me@stan", cfg)
        self.assertEqual(r["pool"], "me@stanford.edu")
        with self.assertRaises(SystemExit):
            bonsai.pick(rows(), "codex", "general", "nobody", cfg)
        with self.assertRaises(SystemExit):
            bonsai.pick(rows(), "claude", "general", None, cfg)   # no personal claude login here

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
        self.assertEqual(bonsai.pick(st, "claude", "general", None, bonsai.load_config())["pool"], "default")

    def test_child_env_drops_parent_marks(self):
        os.environ["CLAUDECODE"] = "1"
        os.environ["CLAUDE_CONFIG_DIR"] = "/elsewhere"
        os.environ["ANTHROPIC_API_KEY"] = "sk-test"
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "tok"
        os.environ["OPENAI_API_KEY"] = "sk-test"
        env = bonsai.child_env("codex", "me@stanford.edu")
        for k in ("CLAUDECODE", "CLAUDE_CONFIG_DIR", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY"):
            self.assertNotIn(k, env)
        self.assertEqual(env["CODEX_HOME"], os.path.join(FAKE, ".codex-pools", "me@stanford.edu"))
        # The default pool is the CLI's own home, reached by leaving the variable unset.
        env = bonsai.child_env("claude", "default")
        self.assertNotIn("CLAUDE_CONFIG_DIR", env)
        env = bonsai.child_env("codex", "default")
        self.assertNotIn("CODEX_HOME", env)
        for k in ("CLAUDECODE", "CLAUDE_CONFIG_DIR", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY"):
            os.environ.pop(k, None)

    def test_chat_driven_detection(self):
        for k in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CODEX_SANDBOX"):
            os.environ.pop(k, None)
        self.assertFalse(bonsai.chat_driven())
        os.environ["CLAUDECODE"] = "1"
        self.assertTrue(bonsai.chat_driven())
        os.environ.pop("CLAUDECODE")
        os.environ["CODEX_SANDBOX"] = "seatbelt"
        self.assertTrue(bonsai.chat_driven())
        os.environ.pop("CODEX_SANDBOX")

    def test_limited_and_sensitive_rules(self):
        cfg = bonsai.load_config()
        st = rows()
        st["rows"][0]["state"] = "LIMITED"       # personal codex at its limit
        order = bonsai.route(st, "codex", "general")
        self.assertNotIn("default", [e["pool"] for e in order])
        with self.assertRaises(SystemExit):      # a named login is not a way around a stop
            bonsai.pick(st, "codex", "general", "personal", cfg)
        with self.assertRaises(SystemExit):      # sensitive never runs on a named personal login
            bonsai.pick(rows(), "codex", "sensitive", "gmail", cfg)
        self.assertEqual(bonsai.pick(rows(), "codex", "sensitive", "stanford", cfg)["pool"], "me@stanford.edu")

    def test_claude_jobs_run_without_tools(self):
        a = bonsai.headless_argv("claude", "claude-haiku-5-5", "low", None, "/tmp")
        self.assertIn("--tools", a)
        self.assertEqual(a[a.index("--tools") + 1], "")
        self.assertIn("--strict-mcp-config", a)

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
        self.assertIn("⌂stanford", text)
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

    def test_signed_out_stub_is_no_login(self):
        # Claude Code leaves a blob with empty tokens behind after sign-out; that is not a bad file.
        self.assertEqual(bonsai._blob_state({"claudeAiOauth": {"accessToken": "", "refreshToken": ""}})[1], "no-login")
        self.assertEqual(bonsai._blob_state({"claudeAiOauth": {"accessToken": "tok"}})[1], "ok")
        self.assertEqual(bonsai._blob_state({"other": 1})[1], "bad-credfile")
        self.assertEqual(bonsai._blob_state("junk")[1], "bad-credfile")

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
                bonsai._data_gate("high", "general", chat, "codex")
            self.assertIn("stopped before starting a model call", str(cm.exception))
        with self.assertRaises(SystemExit) as cm:
            bonsai._data_gate("phi", "general", False, "claude")
        self.assertIn("AI API Gateway", str(cm.exception))
        self.assertEqual(bonsai._data_gate("low", "general", True, "codex"), "general")       # never blocks low
        self.assertEqual(bonsai._data_gate(None, "sensitive", True, "codex"), "sensitive")    # undeclared flows
        with self.assertRaises(SystemExit):
            bonsai._data_gate("restricted", "general", False, "codex")                      # never, anywhere

    def test_pass_gates_before_reading_material(self):
        import argparse
        p = os.path.join(FAKE, "secret.md")
        with open(p, "w") as f:
            f.write("material")
        reads = []
        real = bonsai._read_file_bounded
        bonsai._read_file_bounded = lambda path: reads.append(path) or real(path)
        try:
            a = argparse.Namespace(target="codex", model=None, pool=None, effort=None, kind="general",
                                   data="high", file=[p], out=None, cd=None, dry_run=True, brief=None, prompt=None)
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
        self.assertEqual(err.getvalue().count("Before you use Bonsai"), 1)
        self.assertEqual(bonsai.load_config()["notice_shown"]["version"], bonsai.NOTICE_VERSION)

    def test_acknowledgement_is_asked_once_per_machine(self):
        import io, contextlib, shutil, subprocess, builtins, argparse
        saved = (shutil.which, subprocess.call, sys.stdin, builtins.input)
        asked = []
        shutil.which = lambda name: "/usr/local/bin/" + name
        subprocess.call = lambda argv, env=None: 0
        class Tty(io.StringIO):
            def isatty(self):
                return True
        sys.stdin = Tty()  # a terminal, so the prompt path runs; `input` below answers it
        cfg = bonsai.load_config()
        cfg.pop("notice_shown", None)
        cfg.pop("acknowledged", None)
        bonsai.save_config(cfg)
        try:
            builtins.input = lambda prompt="": asked.append(prompt) or "I understand"
            def login(email, provider, pool=None, name=None):
                a = argparse.Namespace(email=email, name=name, pool=pool, institution=True, acknowledge=False, sso=False,
                                       claude=provider == "claude", codex=provider == "codex")
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    rc = bonsai.cmd_login(a, bonsai.load_config())
                return rc, out.getvalue()
            rc, out = login("a@stanford.edu", "claude")
            self.assertEqual((rc, len(asked)), (0, 1))
            self.assertIn("Before you use Bonsai", out)
            rc, out = login("a@stanford.edu", "codex")        # same e-mail, other provider
            rc2, out2 = login("b@othercollege.edu", "codex")  # a different institution login
            self.assertEqual((rc, rc2, len(asked)), (0, 0, 1))
            self.assertNotIn("Before you use Bonsai", out + out2)
            # One e-mail, a second workspace: its own pool directory and its own name on the board.
            rc3, _ = login("a@stanford.edu", "codex", pool="stanford-pro", name="stanford-pro")
            self.assertEqual(rc3, 0)
            logins = bonsai.load_config()["logins"]
            self.assertEqual(logins["stanford-pro"]["name"], "stanford-pro")
            self.assertEqual(logins["a@stanford.edu"]["name"], "stanford")
            self.assertTrue(os.path.isdir(bonsai.pool_dir("codex", "stanford-pro")))
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                bonsai.ensure_notice(bonsai.load_config(), "job")  # the first job: no second printing
            self.assertEqual(err.getvalue(), "")
            cfg = bonsai.load_config()
            self.assertEqual(cfg["acknowledged"]["pool"], "a@stanford.edu")
            self.assertEqual(cfg["notice_shown"]["how"], "login")
        finally:
            shutil.which, subprocess.call, sys.stdin, builtins.input = saved

    def test_signup_hints_name_both_tiers(self):
        lines = bonsai.signup_hints("x@stanford.edu")
        self.assertEqual(len(lines), 2)
        text = "\n".join(lines)
        for needle in ("uit.stanford.edu/service/claude", "uit.stanford.edu/service/openai-chatgpt-edu",
                       "Stanford University Plus (Edu)", "Stanford University Pro (Edu)", "Continue with SSO"):
            self.assertIn(needle, text)
        self.assertEqual(bonsai.signup_hints("x@nowhere.edu"), [])
        self.assertEqual(bonsai.signup_hints(), lines)

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
        if real():  # running from the checkout: the dry run names the pull and spends nothing
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(bonsai.cmd_update(argparse.Namespace(dry_run=True), bonsai.load_config()), 0)
            self.assertIn("git -C", out.getvalue())
            self.assertIn("--ff-only", out.getvalue())

    def test_display_text_escapes_controls(self):
        self.assertEqual(bonsai.display_text("a\x1b[2Jb\n"), "a\\u001b[2Jb\\u000a")
        self.assertEqual(bonsai.display_text("plain", 3), "pla")

    def test_user_agent_is_bonsai(self):
        h = bonsai._claude_headers("tok")
        self.assertTrue(h["User-Agent"].startswith("bonsai/"))
        self.assertNotIn("claude-cli", h["User-Agent"])
        self.assertNotIn("x-app", h)

    def test_names(self):
        cfg = bonsai.load_config()
        self.assertEqual(bonsai.login_name(cfg, "default"), "personal")
        self.assertEqual(bonsai.login_name(cfg, "x@stanford.edu"), "stanford")
        self.assertEqual(bonsai.login_name(cfg, "x@gmail.com"), "gmail")


if __name__ == "__main__":
    unittest.main()
