"""End-to-end smoke test of the pipeline on a tiny synthetic corpus."""

import json
import subprocess
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]


def run(args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "kabuverdianu_corpus", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
        env={"PYTHONPATH": str(PKG_ROOT / "src"), "PATH": "/usr/bin:/bin"},
    )


def test_pipeline_end_to_end(tmp_path):
    (tmp_path / "data").mkdir()

    mono = tmp_path / "mono.txt"
    mono.write_text(
        "N ta papia kriolu tudu dia. N ta papia kriolu tudu dia.\n"
        "Kel mininu sta na kaza!\n"
        "12345\n",  # mostly-numeric line must be dropped
        encoding="utf-8",
    )
    run(["ingest", str(mono), "--source", "test/mono"], cwd=tmp_path)

    pairs = tmp_path / "pairs.tsv"
    pairs.write_text(
        "N ta papia kriolu\tEu falo crioulo\n"
        "Bon dia\tBom dia\n"
        "x\ty\n",  # too short, must be dropped
        encoding="utf-8",
    )
    run(["pairs", str(pairs), "--source", "test/pairs"], cwd=tmp_path)

    out = run(["clean"], cwd=tmp_path).stdout
    assert "kept" in out

    sents = [
        json.loads(l)
        for l in (tmp_path / "data/clean/sentences.jsonl").read_text().splitlines()
    ]
    texts = [s["text"] for s in sents]
    assert "Kel mininu sta na kaza!" in texts
    assert texts.count("N ta papia kriolu tudu dia.") == 1  # deduped
    assert all("12345" not in t for t in texts)

    prs = [
        json.loads(l)
        for l in (tmp_path / "data/parallel/pairs.jsonl").read_text().splitlines()
    ]
    assert len(prs) == 2
    assert all(p["src_lang"] == "kea" and p["tgt_lang"] == "por" for p in prs)

    counts = json.loads(run(["export"], cwd=tmp_path).stdout)
    assert sum(v for k, v in counts.items() if k.startswith("parallel.")) == 2
    assert sum(v for k, v in counts.items() if k.startswith("mono.")) == len(sents)
