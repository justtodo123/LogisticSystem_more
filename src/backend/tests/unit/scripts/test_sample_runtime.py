from pathlib import Path

from scripts.sample_runtime import collect_sample, parse_status, process_tree_rss_kb, read_pid


def _write_status(root: Path, pid: int, ppid: int, rss_kb: int) -> None:
    proc = root / str(pid)
    proc.mkdir(parents=True, exist_ok=True)
    (proc / "status").write_text(
        f"Name:\tpython\nPid:\t{pid}\nPPid:\t{ppid}\nVmRSS:\t{rss_kb} kB\n",
        encoding="utf-8",
    )


def test_parse_status_and_tree_rss(tmp_path):
    proc_root = tmp_path / "proc"
    _write_status(proc_root, 10, 1, 1000)
    _write_status(proc_root, 11, 10, 2500)
    _write_status(proc_root, 12, 10, 500)
    _write_status(proc_root, 99, 2, 9000)
    assert parse_status((proc_root / "10" / "status").read_text(encoding="utf-8")) == (10, 1, 1000)
    assert process_tree_rss_kb(10, proc_root) == 4000
    assert process_tree_rss_kb(99, proc_root) == 9000
    assert process_tree_rss_kb(7, proc_root) is None


def test_collect_sample_uses_probes_and_pid_file(tmp_path):
    proc_root = tmp_path / "proc"
    _write_status(proc_root, 21, 1, 1200)
    _write_status(proc_root, 22, 21, 800)
    _write_status(proc_root, 30, 1, 400)
    pid_file = tmp_path / "api.pid"
    extra_file = tmp_path / "worker.pid"
    pid_file.write_text("21\n", encoding="utf-8")
    extra_file.write_text("30\n", encoding="utf-8")

    def http_probe(url: str) -> dict:
        if url.endswith("/health"):
            return {"ok": True, "status": 200, "payload": {"code": 0}}
        return {
            "ok": True,
            "status": 200,
            "payload": {"gauges": {"outbox_backlog": 2, "outbox_processing": 0, "outbox_dead_letter": 1, "cache_degraded": 0}},
        }

    sample = collect_sample(
        pid=read_pid(pid_file),
        extra_pids=[read_pid(extra_file)],
        health_url="http://example/health",
        metrics_url="http://example/metrics",
        database_url="postgresql+psycopg://x",
        redis_url="redis://localhost/0",
        proc_root=proc_root,
        http_probe=http_probe,
        pg_probe=lambda _dsn: 8,
        redis_probe=lambda _url: 3,
    )
    assert sample["health_ok"] is True
    assert sample["rss_kb"] == 2400
    assert sample["pg_connections"] == 8
    assert sample["redis_clients"] == 3
    assert sample["outbox_backlog"] == 2
    assert sample["outbox_dead_letter"] == 1
    assert sample["errors"] == []
