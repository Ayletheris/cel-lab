"""verifica ca demo-ul pt laborator merge (ca sa nu ne trezim ca pica la prezentare)."""

import subprocess
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1] / "scripts" / "demo_l6.py"


def test_demo_runs_and_restores_everything():
    result = subprocess.run([sys.executable, str(DEMO)], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    out = result.stdout
    # toate cele 3 automate apar si toate restaurarile sunt identice
    for name in ["life.json", "brians_brain.json", "forest_fire.json"]:
        assert name in out
    assert out.count("grila identica: da") == 3
    assert "grila identica: NU" not in out
