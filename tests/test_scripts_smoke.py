"""Subprocess smoke tests for the thin REMOUNT CLI scripts.

Each script must exit 0 and produce the expected stdout/artifact. Runs with
``sys.executable`` (the venv python) and ``cwd=project_root`` so scripts can
self-bootstrap ``src/`` onto ``sys.path``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / name), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_brief_script():
    proc = _run("brief.py")
    assert proc.returncode == 0, proc.stderr
    assert "REMOUNT" in proc.stdout
    assert proc.stderr == ""


def test_recon_script():
    proc = _run("recon.py", "survey the theater")
    assert proc.returncode == 0, proc.stderr
    assert "Recon findings" in proc.stdout


def test_plan_script():
    proc = _run("plan.py")
    assert proc.returncode == 0, proc.stderr
    assert "run_remount" in proc.stdout


def test_execute_script_writes_artifact(tmp_path: Path):
    out = tmp_path / "outcome.json"
    proc = _run("execute.py", "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["success"] is True
    assert payload["results"]["overall_verdict"] == "improved"


def test_debrief_script():
    proc = _run("debrief.py")
    assert proc.returncode == 0, proc.stderr
    assert "Lessons" in proc.stdout


def test_run_mission_script():
    proc = _run("run_mission.py")
    assert proc.returncode == 0, proc.stderr
    assert "Success: True" in proc.stdout


def test_preflight_script():
    proc = _run("00_preflight.py")
    assert proc.returncode == 0, proc.stderr
    assert "REMOUNT" in proc.stdout


def test_z_generate_manuscript_variables_script():
    proc = _run("z_generate_manuscript_variables.py")
    assert proc.returncode == 0, proc.stderr
    variables_path = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    assert variables_path.is_file()
    payload = json.loads(variables_path.read_text(encoding="utf-8"))
    assert payload["OVERALL_VERDICT"] == "improved"
    # Figures must render too.
    assert (PROJECT_ROOT / "output" / "figures" / "op_diff_scores.png").is_file()
    assert (PROJECT_ROOT / "output" / "figures" / "asset_distribution.png").is_file()
    assert (PROJECT_ROOT / "output" / "figures" / "learning_curve.png").is_file()
    assert (PROJECT_ROOT / "output" / "figures" / "asset_allocation.png").is_file()
