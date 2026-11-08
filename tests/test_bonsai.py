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

    def test_child_env_drops_parent_marks(self):
        os.environ["CLAUDECODE"] = "1"
        os.environ["CLAUDE_CONFIG_DIR"] = "/elsewhere"
        env = bonsai.child_env("codex", "me@stanford.edu")
        self.assertNotIn("CLAUDECODE", env)
        self.assertNotIn("CLAUDE_CONFIG_DIR", env)
        self.assertEqual(env["CODEX_HOME"], os.path.join(FAKE, ".codex-pools", "me@stanford.edu"))
        env = bonsai.child_env("claude", "default")
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], os.path.join(FAKE, ".claude"))


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
        a = argparse.Namespace(set=['logins.me@stanford.edu={"name":"stanford","institution":true}',
                                    'models.astra=["codex","gpt-6-astra"]', "interval=600"])
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            bonsai.cmd_config(a, cfg)
        saved = bonsai.load_config()
        self.assertTrue(saved["logins"]["me@stanford.edu"]["institution"])
        self.assertEqual(saved["models"]["astra"], ["codex", "gpt-6-astra"])
        self.assertEqual(saved["interval"], 600)
        self.assertTrue(bonsai.is_institution(saved, "me@stanford.edu"))

    def test_annotate_reads_config_not_cache(self):
        cfg = bonsai.load_config()
        cfg.setdefault("logins", {})["me@stanford.edu"] = {"name": "farm", "institution": True}
        state = bonsai.annotate({"rows": [{"pool": "me@stanford.edu", "provider": "codex", "institution": False, "name": "x"}]}, cfg)
        self.assertEqual(state["rows"][0]["name"], "farm")
        self.assertTrue(state["rows"][0]["institution"])

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
