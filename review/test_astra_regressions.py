"""Adversarial acceptance tests; failures are intentional against the reviewed source.

Run: /usr/bin/python3 -m unittest discover -s review -p test_astra_regressions.py -v
Set BONSAI_REVIEW_SOURCE to another bonsai file to run these tests against it.
Only synthetic credentials, temporary files, mocked provider/CLI calls. No paid jobs.
"""
import contextlib
import copy
import io
import json
import math
import os
from pathlib import Path
import runpy
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch


SOURCE = Path(os.environ.get("BONSAI_REVIEW_SOURCE", str(Path(__file__).resolve().parents[1] / "bonsai")))


def row(pool="default", **kw):
    r = dict(pool=pool, name=pool, provider="codex", state="OK",
             institution=False, wk=10, wk_at=2000000000)
    r.update(kw)
    return r


class Review(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bonsai-astra-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Adjusted 2026-11-09: an agent's sandbox marks in the caller's environment are dropped, as the main suite does.
        marks = patch.dict(os.environ)
        marks.start()
        self.addCleanup(marks.stop)
        for mark in [k for k in os.environ if k in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "BONSAI_CHAT_DRIVEN")
                     or (k.startswith("CODEX_") and k != "CODEX_HOME")]:
            del os.environ[mark]
        env = patch.dict(os.environ, {
            "BONSAI_POOLS_HOME": str(self.root),
            "BONSAI_STATE": str(self.root / "state"),
            "BONSAI_CONFIG": str(self.root / "config.json"),
        })
        env.start()
        self.addCleanup(env.stop)
        self.b = runpy.run_path(str(SOURCE))
        self.g = self.b["main"].__globals__
        self.cfg = copy.deepcopy(self.b["DEFAULT_CONFIG"])
        for name in ("_get", "claude_blob", "claude_status"):
            p = patch.dict(self.g, {name: Mock(side_effect=AssertionError("unexpected credential/network access"))})
            p.start()
            self.addCleanup(p.stop)
        # Asking Claude Code for usage starts the real CLI: never from a test (no reading: the login stays unknown).
        p = patch.dict(self.g, {"read_usage_now": lambda pool, timeout=None: None})
        p.start()
        self.addCleanup(p.stop)
        self.out = io.StringIO()
        self.err = io.StringIO()
        for cm in (contextlib.redirect_stdout(self.out), contextlib.redirect_stderr(self.err)):
            cm.__enter__()
            self.addCleanup(cm.__exit__, None, None, None)

    def args(self, **kw):
        d = dict(target="codex", model=None, pool=None, effort=None,
                 prompt="review", file=None, out=None, dry_run=False, brief=None)
        d.update(kw)
        return Namespace(**d)

    def main_capture(self, argv):
        captured = []
        def command(a, cfg):
            captured.append(a)
            return 0
        with patch.dict(self.g, cmd_job=command, cmd_pass=command,
                        load_config=lambda: self.cfg):
            self.b["main"](argv)
        return captured[0]

    # Finding 1: auth, endpoint, nested-session, telemetry and startup state.
    def test_01_child_drops_auth_and_endpoint_overrides(self):
        names = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
                 "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_SESSION_ACCESS_TOKEN",
                 "CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR", "CLAUDE_CODE_USE_BEDROCK",
                 "CODEX_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_THREAD_ID",
                 "OTEL_EXPORTER_OTLP_ENDPOINT", "BASH_ENV")
        with patch.dict(os.environ, dict.fromkeys(names, "SYNTHETIC")):
            for provider in ("claude", "codex"):
                with self.subTest(provider=provider):
                    env = self.b["child_env"](provider, "school")
                    self.assertEqual(set(names) & set(env), set())

    # Finding 2. Adjusted 2026-11-08: `run` is gone (it started a command with none of a job's isolation); the guard
    # sits in run_job, the one path that spawns a job.
    def test_02_there_is_no_run_and_run_job_refuses_what_is_not_a_job(self):
        with self.assertRaises(SystemExit):
            self.b["main"](["run", "--pool", "default", "--", "codex"])
        launched = Mock()
        with patch.object(self.g["subprocess"], "run", launched):
            with self.assertRaises(self.b["LaunchRefused"]):
                self.b["run_job"](["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "x"], "codex", "default", "t")
        launched.assert_not_called()

    # Finding 3. Failing login must not relabel existing credentials.
    def test_03_failed_login_does_not_change_classification(self):
        a = Namespace(claude=False, email="school", institution=True, name=None, sso=False)
        original = copy.deepcopy(self.cfg)
        with patch.object(self.g["shutil"], "which", return_value="codex"), \
             patch.object(self.g["subprocess"], "call", return_value=1):
            self.assertEqual(self.b["cmd_login"](a, self.cfg), 1)
        # Adjusted 2026-11-08: the notice is printed (and recorded as shown) before the browser opens, whatever the
        # sign-in's outcome; nothing else in the config moves when the sign-in fails.
        saved = self.b["load_config"]()
        self.assertEqual(saved.get("logins"), original.get("logins"))
        self.assertEqual({k: v for k, v in self.cfg.items() if k != "notice_shown"},
                         {k: v for k, v in original.items() if k != "notice_shown"})

    def test_03_classification_is_per_provider(self):
        a = Namespace(claude=False, email="school", institution=True, name=None, sso=False)
        with patch.object(self.g["shutil"], "which", return_value="codex"), \
             patch.object(self.g["subprocess"], "call", return_value=0):
            self.b["cmd_login"](a, self.cfg)
        state = self.b["annotate"]({"rows": [row("school", provider="claude"), row("school")]}, self.cfg)
        self.assertFalse(state["rows"][0]["institution"])
        self.assertTrue(state["rows"][1]["institution"])

    # Finding 4.
    def test_04_a_named_login_must_be_signed_in_for_that_provider(self):
        # Adjusted 2026-11-08: the general/sensitive kind is gone (one preference decides auto); a named login is
        # still taken only where it is signed in for the provider asked for.
        with self.assertRaises(SystemExit):
            self.b["pick"]({"rows": [row()]}, "claude", "default", self.cfg)

    # Finding 5: test the precise truthful replacement documentation, not flag membership.
    def test_05_readme_does_not_promise_file_allowlisting(self):
        text = (SOURCE.parent / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("nothing else\ncan happen on your machine without you", text)

    # Finding 6. A transport fake invokes the actual redirect policy without sockets.
    def test_06_bonsai_reads_no_stored_token(self):
        # Adjusted 2026-11-08: Bonsai reads no stored Claude token at all (ruled: "Yes, remove it"), so there is no
        # bearer to forward; the probe asks `claude auth status` and never touches the Keychain or a credential file.
        for name in ("_get", "claude_blob", "keychain_service", "_claude_headers", "parse_claude_usage", "retry_deadline"):
            self.assertNotIn(name, self.b, name)
        (self.root / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"accessToken": "SYNTHETIC"}}))
        ran = []
        with patch.dict(self.g, claude_status=lambda pool: {"loggedIn": True, "email": "a@b.example"}), \
             patch.object(self.g["subprocess"], "run", side_effect=lambda *a, **k: ran.append(a) or Namespace(returncode=1)):
            r = self.b["probe_claude"]("default", str(self.root), self.cfg)
        self.assertEqual(r["state"], "signed-in")
        self.assertNotIn("SYNTHETIC", json.dumps(r))
        self.assertFalse(any("security" in str(a) for a in ran))

    # Finding 7.
    @unittest.skipIf(os.name == "nt", "POSIX permission bits; Windows guards these files with its own ACLs")
    def test_07_private_modes_despite_umask(self):
        old = os.umask(0o022)
        try:
            self.b["_write_json"](str(self.root / "state" / "x.json"), {"x": 1})
            self.b["record_job"]({"id": "x"})
        finally:
            os.umask(old)
        for p in (self.root / "state", self.root / "state" / "x.json", self.root / "state" / "jobs.jsonl"):
            with self.subTest(path=p.name):
                self.assertEqual(p.stat().st_mode & 0o077, 0)

    def test_07_atomic_writer_does_not_follow_predictable_symlink(self):
        victim = self.root / "victim"
        victim.write_text("KEEP")
        target = self.root / "config.json"
        Path(str(target) + ".tmp").symlink_to(victim)
        self.b["_write_json"](str(target), {"x": 1})
        self.assertEqual(victim.read_text(), "KEEP")

    def test_07_concurrent_atomic_writers(self):
        # Both writers hold a finished temporary file at the same moment, then both replace the target.
        # (Adjusted 2026-11-08 after a review: the barrier was on json.dump, which the writer never calls.)
        barrier = threading.Barrier(2)
        reached = []
        real_replace = os.replace
        def replace(src, dst, *a, **kw):
            name = os.path.basename(str(src))
            if name not in reached:                           # a retry (Windows refuses a rename onto a file
                reached.append(name)                          # being replaced) does not wait a second time
                barrier.wait(timeout=3)
            return real_replace(src, dst, *a, **kw)
        with patch.object(os, "replace", side_effect=replace), ThreadPoolExecutor(2) as ex:
            futures = [ex.submit(self.b["_write_json"], str(self.root / "same.json"), {"i": i}) for i in range(2)]
            for f in futures:
                f.result(timeout=4)
        self.assertEqual(len(set(reached)), 2)               # two temporary files, both waited at the barrier
        self.assertIn(json.loads((self.root / "same.json").read_text()), [{"i": 0}, {"i": 1}])
        self.assertEqual([p.name for p in self.root.iterdir() if p.name.startswith(".pool-")], [])

    # Finding 8.
    # Finding 9.
    def test_09_limited_cannot_win_auto(self):
        state = {"rows": [row("limited", state="LIMITED", wk_at=1), row("ready", wk_at=2)]}
        self.assertEqual(self.b["pick"](state, "codex", None, self.cfg)["pool"], "ready")

    def test_09_all_held_fails_closed(self):
        with self.assertRaises(SystemExit):
            # Adjusted 2026-11-08: the floor shrinks toward the reset, so the resets are days away, as a live one is.
            soon = time.time() + 6 * 86400
            self.b["pick"]({"rows": [row("empty", wk=100, wk_at=soon), row("almost", wk=91, wk_at=soon + 1)]},
                           "codex", None, self.cfg)

    # Finding 10.
    def test_10_missing_codex_duration_cannot_overwrite_known_window(self):
        # Adjusted 2026-11-08: the app-server's shape (the reference-only wham/usage parser is gone).
        r = self.b["parse_codex_rate_limits"]({"rateLimits": {
            "primary": {"windowDurationMins": 300, "usedPercent": 95},
            "secondary": {"usedPercent": 1}}})
        self.assertEqual(r["5h"], 95)
        self.assertNotIn("wk", r)

    def test_10_nonfinite_utilization_is_unknown(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                self.assertIsNone(self.b["_pct"](value))

    def test_10_malformed_auth_is_bad_credfile(self):
        for auth in ({"tokens": None}, {"tokens": []}):
            with self.subTest(auth=auth):
                (self.root / "auth.json").write_text(json.dumps(auth))
                r = self.b["probe_codex"]("x", str(self.root))
                self.assertEqual(r["state"], "bad-credfile")

    def test_10_jwt_claims_are_always_a_mapping(self):
        self.assertEqual(self.b["_jwt_claims"]("x.W10.x"), {})  # W10 is base64url([]).

    def test_10_unknown_present_window_cannot_route_from_other_window(self):
        parsed = self.b["parse_codex_rate_limits"]({"rateLimits": {
            "primary": {"windowDurationMins": 300, "usedPercent": "99"},
            "secondary": {"windowDurationMins": 10080, "usedPercent": 1}}})
        r = row(**parsed)
        with self.assertRaises(SystemExit):
            self.b["pick"]({"rows": [r]}, "codex", None, self.cfg)

    # Finding 11.
    def test_11_extra_prompt_words_are_rejected(self):
        with self.assertRaises(SystemExit):
            self.main_capture(["job", "codex", "review", "kind", "sensitive"])

    def test_11_option_abbreviations_are_rejected(self):
        with self.assertRaises(SystemExit):
            self.main_capture(["job", "codex", "--poo", "school", "review"])

    def test_11_double_dash_after_options_preserves_literal_prompt(self):
        a = self.main_capture(["job", "codex", "-o", "out", "--", "-literal"])
        self.assertEqual(a.prompt, "-literal")

    def test_11_dash_with_extra_word_is_not_silently_a_literal(self):
        with self.assertRaises(SystemExit):
            self.main_capture(["job", "codex", "-o", "out", "-", "extra"])

    def test_11_pass_positional_material_is_not_silently_discarded(self):
        with self.assertRaises(SystemExit):
            self.main_capture(["pass", "codex", "material"])

    # Finding 12.
    def test_12_file_reads_are_bounded(self):
        # Adjusted 2026-11-08: the file is opened without blocking and checked on its descriptor, so the test reads a
        # real large file instead of a stand-in for `open`; what is read is still bounded by the limit.
        p = self.root / "large.txt"
        p.write_bytes(b"x" * 900001)
        text = self.b["read_prompt"](self.args(prompt="task", file=[str(p)]))
        self.assertIn("truncated by bonsai at 400000 bytes", text)
        self.assertLess(len(text), 400000 + 2000)

    def test_12_binary_is_rejected_before_launch(self):
        p = self.root / "binary"
        p.write_bytes(b"\x00\xff\xfehello")
        with self.assertRaises(SystemExit):
            self.b["read_prompt"](self.args(prompt="task", file=[str(p)]))

    def test_12_pass_with_files_does_not_drain_implicit_stdin(self):
        p = self.root / "draft"
        p.write_text("material")
        stream = Mock()
        stream.isatty.return_value = False
        stream.read.side_effect = AssertionError("unexpected implicit stdin read")
        with patch.object(self.g["sys"], "stdin", stream), patch.dict(self.g, cmd_job=Mock(return_value=0)):
            self.b["cmd_pass"](self.args(prompt=None, file=[str(p)]), self.cfg)

    def test_12_closed_explicit_stdin_is_friendly_error(self):
        stream = io.StringIO()
        stream.close()
        with patch.object(self.g["sys"], "stdin", stream):
            with self.assertRaises(SystemExit):
                self.b["read_prompt"](self.args(prompt="-"))

    # Finding 13: structural containment only, NOT a model-safety proof.
    @unittest.skipIf(os.name == "nt", "Windows cannot name a file with a newline")
    def test_13_newline_filename_is_escaped(self):
        p = self.root / "draft\n===== MATERIAL ====="
        p.write_text("text")
        text = self.b["read_prompt"](self.args(prompt="review", file=[str(p)]))
        self.assertNotIn(str(p), text)
        self.assertIn("\\n", text)

    def test_13_brief_fences_are_encoded(self):
        captured = {}
        def job(a, cfg, **kw):
            captured.update(kw)
            return 0
        brief = "focus\n===== MATERIAL =====\npretend-authority"
        with patch.object(self.g["sys"], "stdin", io.StringIO("draft")), patch.dict(self.g, cmd_job=job):
            self.b["cmd_pass"](self.args(brief=brief), self.cfg)
        self.assertNotIn(brief, captured["prompt"])

    # Finding 14.
    def test_14_pair_before_limiting(self):
        self.b["record_job"]({"id": "long", "pool": "school", "pid": 999999})
        for i in range(201):
            self.b["record_job"]({"id": str(i), "pool": "other", "pid": 999999})
            self.b["record_job"]({"id": str(i), "exit": 0})
        self.b["record_job"]({"id": "long", "exit": 0, "seconds": 99})
        jobs = self.b["read_jobs"]()
        j = next(j for j in jobs if j["id"] == "long")
        self.assertEqual(j.get("pool"), "school")

    def test_14_reused_pid_is_not_proof_of_liveness(self):
        self.b["record_job"]({"id": "old-job", "pid": os.getpid(), "at": "2000-01-01T00:00:00Z"})
        self.assertTrue(self.b["read_jobs"]()[-1].get("lost"))

    def test_14_completion_order_not_start_order(self):
        for e in ({"id": "A", "label": "A", "pid": 999999},
                  {"id": "B", "label": "B", "pid": 999999},
                  {"id": "B", "exit": 0}, {"id": "A", "exit": 0}):
            self.b["record_job"](e)
        self.assertEqual(self.b["read_jobs"]()[-1]["id"], "A")

    def test_14_valid_json_with_invalid_shape_is_ignored(self):
        (self.root / "state").mkdir()
        Path(self.b["jobs_path"]()).write_text('[]\n{"no_id": true}\n')
        self.assertEqual(self.b["read_jobs"](), [])

    # Finding 15. Both reads are forced stale, reproducing two processes' TOCTOU.
    def test_15_concurrent_refresh_probes_only_once(self):
        cached = [None]
        entered = threading.Event()
        release = threading.Event()
        probes = []
        (self.root / "state").mkdir()
        def probe(*args):
            probes.append(1)
            entered.set()
            release.wait(timeout=1)
            return {"at": time.time(), "rows": []}
        def write(path, obj):
            cached[0] = obj
        with patch.dict(self.g, read_cache=lambda: cached[0], probe_all=probe, _write_json=write):
            with ThreadPoolExecutor(2) as ex:
                one = ex.submit(self.b["refresh"], self.cfg)
                self.assertTrue(entered.wait(timeout=1))
                two = ex.submit(self.b["refresh"], self.cfg)
                time.sleep(0.05)
                release.set()
                one.result(timeout=2)
                two.result(timeout=2)
        self.assertEqual(len(probes), 1)

    def test_15_gauge_interval_reaches_refresh(self):
        seen = []
        def refresh(cfg, **kw):
            seen.append(cfg["interval"])
            return {"rows": []}
        with patch.dict(self.g, refresh=refresh, render=lambda *a: ""):
            self.b["cmd_gauge"](Namespace(no_color=True, interval=900, once=True, fresh=False), self.cfg)
        self.assertEqual(seen, [900])

    # Finding 16.
    def test_16_probe_all_honors_passed_config_without_main(self):
        # Adjusted 2026-11-08: there is no usage-read switch any more; the passed config still decides the labels.
        self.cfg["logins"] = {"default": {"name": "mine"}}
        (self.root / "auth.json").write_text(json.dumps({"tokens": {"access_token": "SYNTHETIC"}}))
        with patch.dict(self.g, codex_app_server=lambda *a, **k: {"rateLimits": {}},
                        discover_pools=lambda: [("codex", "default", str(self.root))]):
            st = self.b["probe_all"](self.cfg)
        self.assertEqual(st["rows"][0]["name"], "mine")

    # Finding 17.
    def test_17_config_never_prints_unknown_secret_field(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["access_token"] = "SYNTHETIC_SECRET"
        try:
            self.b["cmd_config"](Namespace(set=None), cfg)
        except SystemExit:
            pass  # Rejecting unknown keys is also acceptable.
        self.assertNotIn("SYNTHETIC_SECRET", self.out.getvalue())

    def test_17_render_escapes_terminal_control_in_label(self):
        with patch.dict(self.g, machine_stats=lambda: {"host": "test"}, read_jobs=lambda: []):
            text = self.b["render"]({"at": time.time(), "rows": [row(name="\x1b[2JFAKE")]},
                                    self.cfg, self.b["Paint"](False), 110, 300)
        self.assertNotIn("\x1b[2J", text)

    # Finding 18.
    def test_18_claude_output_failure_preserves_existing_answer(self):
        dest = self.root / "answer.md"
        dest.write_text("KEEP")
        a = self.args(target="claude", out=str(dest))
        # Adjusted 2026-11-08: the job's real command (the text-only launch shape) is built; a stand-in is refused. Jobs
        # start with subprocess.Popen in their own process group (a time limit and `bonsai cancel` need the child's pid
        # while it runs), so the failing child is a fake Popen.
        class FailingChild:
            pid, returncode = 999999, 1

            def __init__(self, argv, stdout=None, stderr=None, **kw):
                if stderr is not None and hasattr(stderr, "write"):
                    stderr.write("failed")

            def communicate(self, input=None, timeout=None):
                return None, None

            def wait(self, timeout=None):      # adjusted 2026-11-09: the job waits on the child; its prompt comes from a file
                return self.returncode

            def poll(self):
                return self.returncode
        with patch.dict(self.g, refresh=lambda c: {"rows": [row(provider="claude")]},
                        cli_command=lambda n: ["/stand-in/" + n]), \
             patch.object(self.g["subprocess"], "Popen", FailingChild):   # a resolved CLI path: a job never starts from a bare name
            self.assertEqual(self.b["cmd_job"](a, self.cfg), 1)
        self.assertEqual(dest.read_text(), "KEEP")

    def test_18_launch_failure_has_completion_record(self):
        # Adjusted 2026-11-08: a real job command in a folder of its own (the guard refuses a stand-in).
        with self.b["private_cwd"]() as cwd, patch.object(self.g["subprocess"], "Popen", side_effect=PermissionError("denied")):
            try:
                self.b["run_job"](self.b["headless_argv"]("codex", "gpt-x", "low", None, cwd), "codex", "default", "test", cwd=cwd)
            except OSError:
                pass
        self.assertIn("exit", self.b["read_jobs"]()[-1])

    # Finding 19.
    def test_19_nonfinite_timestamp_is_unknown(self):
        for value in (float("nan"), float("inf")):
            self.assertIsNone(self.b["_when_ts"](value))

    # Finding 20.
    def test_20_load_average_is_not_labelled_cpu_utilization(self):
        with patch.dict(self.g, IS_MAC=False, IS_WIN=False), \
             patch.object(os, "getloadavg", return_value=(4.0, 4.0, 4.0), create=True), \
             patch.object(os, "cpu_count", return_value=4):
            self.assertNotIn("cpu", self.b["machine_stats"]())

    def test_20_windows_unknown_power_and_commit_are_not_fake_measurements(self):
        import ctypes
        def memory(ptr):
            m = ptr._obj
            m.dwMemoryLoad = 50
            m.ullTotalPhys, m.ullAvailPhys = 8 * 2**30, 4 * 2**30
            m.ullTotalPageFile, m.ullAvailPageFile = 16 * 2**30, 8 * 2**30
            return 1
        for flag, percent in ((128, 50), (0, 50)):
            def power(ptr):
                p = ptr._obj
                p.BatteryFlag, p.BatteryLifePercent, p.ACLineStatus = flag, percent, 255
                return 1
            kernel = Namespace(GlobalMemoryStatusEx=Mock(side_effect=memory),
                               GetSystemPowerStatus=Mock(side_effect=power),
                               GetTickCount64=Mock(return_value=2**40))
            with patch.object(ctypes, "windll", Namespace(kernel32=kernel), create=True):
                st = self.b["_machine_stats_windows"]({})
            with self.subTest(flag=flag):
                self.assertNotIn("swap_gb", st)
                self.assertNotIn("ac", st)
                if flag == 128:
                    self.assertNotIn("batt", st)
                self.assertEqual(st["uptime"], 2**40 / 1000)

    # Finding 21.
    def test_21_pool_path_cannot_escape_root(self):
        for pool in ("../.codex", "/tmp/elsewhere", "bad\nname"):
            with self.subTest(pool=pool), self.assertRaises(SystemExit):
                self.b["pool_dir"]("codex", pool)

    # WHAT HOLDS: precise edge cases that should remain passing.
    def test_holds_routing_ambiguity_and_dead_rows(self):
        for rows in ([row("a@one"), row("a@two")],
                     [row("default", name="personal"), row("personal")]):
            with self.assertRaises(SystemExit):
                self.b["pick"]({"rows": rows}, "codex", "a" if rows[0]["pool"].startswith("a") else "personal", self.cfg)
        self.assertEqual(self.b["route"]({"rows": [row(state="re-login", last_good={"wk": 0})]}, "codex"), [])
        # Adjusted 2026-11-08: auto spends institution seats too (prefer decides the order, not whether).
        self.assertEqual([e["pool"] for e in self.b["route"]({"rows": [row(provider="claude", institution=True)]}, "claude")], ["default"])

    def test_holds_none_reset_and_provider_alias_conflict(self):
        r = self.b["route"]({"rows": [row("unknown", wk_at=None), row("known", wk_at=1)]}, "codex")
        self.assertEqual(r[0]["pool"], "known")
        p, _, m = self.b["resolve_target"]("astra", self.cfg, "opus")
        with self.assertRaises(SystemExit):
            self.b["resolve_model"](self.cfg, p, m)

    def test_holds_claude_scale_missing_fields_iso_and_negative_age(self):
        self.assertIsNone(self.b["_pct"]("98"))
        self.assertEqual(self.b["_when_ts"]("2026-01-01T00:00:00Z"), 1767225600)
        self.assertEqual(self.b["_age"](-100), "<1m")

    def test_holds_mac_battery_and_apple_silicon_page_size(self):
        cases = [("Now drawing from 'AC Power'\n", None, None),
                 ("Now drawing from 'AC Power'\n -InternalBattery-0 84%; charging; 1:00 remaining\n", 84, True),
                 ("Now drawing from 'Battery Power'\n -InternalBattery-0 3%; discharging; 0:05 remaining\nLow battery warning\n", 3, False)]
        for battery, pct, ac in cases:
            def run(argv, **kw):
                return Namespace(stdout=battery if argv[0] == "pmset" else
                                 "Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 10.\nPages inactive: 20.\nPages speculative: 30.\n")
            def sysctl(name):
                return {"hw.memsize": str(16384 * 100), "vm.swapusage": "used = 0.00M", "kern.boottime": "sec = 1"}[name]
            with patch.dict(self.g, IS_MAC=True, IS_WIN=False, _sysctl=sysctl), \
                 patch.object(self.g["subprocess"], "run", side_effect=run):
                s = self.b["machine_stats"]()
            self.assertEqual(s.get("batt"), pct)
            self.assertEqual(s.get("ac"), ac)
            self.assertAlmostEqual(s["mem"], 40)

    def test_holds_concurrent_small_ledger_appends(self):
        def writer(worker):
            for i in range(100):
                jid = "%s-%s" % (worker, i)
                self.b["record_job"]({"id": jid, "pool": "synthetic", "pid": 999999})
                self.b["record_job"]({"id": jid, "exit": 0})
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(writer, range(4)))
        jobs = self.b["read_jobs"](500)
        self.assertEqual(len(jobs), 400)
        self.assertTrue(all(j["pool"] == "synthetic" and j["exit"] == 0 for j in jobs))


if __name__ == "__main__":
    unittest.main()
