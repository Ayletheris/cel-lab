import subprocess
import sys
from pathlib import Path

import numpy as np

from cellab.cli.commands import file_name, main
from cellab.io import load_automaton, load_state

EXAMPLES = Path(__file__).resolve().parents[2] / "automata" / "examples"


def test_file_name_is_simple():
    assert file_name("Brian's Brain") == "brians-brain"
    assert file_name("Game of Life") == "game-of-life"
    assert file_name("!!!") == "automat"


def test_run_saves_final_state(tmp_path, capsys):
    code = main(["run", str(EXAMPLES / "game_of_life.json"), "--generations", "5",
                 "--no-save-intermediate", "--output-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    assert "gata: 5 generatii (de la 0 la 5)" in out
    saved = tmp_path / "game-of-life-gen5.npz"
    assert saved.exists()
    state = load_state(saved, load_automaton(EXAMPLES / "game_of_life.json"))
    assert state.generation == 5


def test_run_with_intermediate_saves_checkpoints(tmp_path, capsys):
    main(["run", str(EXAMPLES / "game_of_life.json"), "--generations", "10",
          "--checkpoint-interval", "5", "--output-dir", str(tmp_path)])
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["game-of-life-gen0.npz", "game-of-life-gen10.npz", "game-of-life-gen5.npz"]


def test_resume_continues_like_one_long_run(tmp_path, capsys):
    example = str(EXAMPLES / "forest_fire_random.json")
    long_dir = tmp_path / "long"
    split_dir = tmp_path / "split"

    # o rulare de 10 generatii
    main(["run", example, "--generations", "10", "--no-save-intermediate", "--output-dir", str(long_dir)])
    # 5 generatii, apoi inca 5 de la starea salvata
    main(["run", example, "--generations", "5", "--no-save-intermediate", "--output-dir", str(split_dir)])
    main(["run", example, "--generations", "5", "--no-save-intermediate", "--output-dir", str(split_dir),
          "--resume", str(split_dir / "forest-fire-random-gen5.npz")])
    out = capsys.readouterr().out
    assert "continuam de la generatia 5" in out

    automaton = load_automaton(example)
    long_state = load_state(long_dir / "forest-fire-random-gen10.npz", automaton)
    split_state = load_state(split_dir / "forest-fire-random-gen10.npz", automaton)
    np.testing.assert_array_equal(long_state.grid, split_state.grid)


def test_show_prints_the_grid(tmp_path, capsys):
    main(["run", str(EXAMPLES / "life.json"), "--generations", "1", "--show",
          "--no-save-intermediate", "--output-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert "generatia 0" in out and "generatia 1" in out
    assert ".###." in out


def test_show_rule30_as_rows(tmp_path, capsys):
    main(["run", str(EXAMPLES / "rule30.json"), "--generations", "3", "--show",
          "--checkpoint-interval", "1", "--output-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert "###" in out and "generatia" not in out


def test_validate_good_file(capsys):
    assert main(["validate", str(EXAMPLES / "life.json")]) == 0
    assert "ok:" in capsys.readouterr().out


def test_bad_file_gives_short_error(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{ nu e json", encoding="utf-8")
    assert main(["validate", str(bad)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("eroare:") and "Traceback" not in err


def test_missing_file_gives_short_error(tmp_path, capsys):
    assert main(["run", str(tmp_path / "lipsa.json")]) == 2
    assert "eroare:" in capsys.readouterr().err


def test_help_lists_commands(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "run" in out and "validate" in out


def test_module_entrypoint_runs(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "cellab.cli", "run", str(EXAMPLES / "life.json"),
         "--generations", "2", "--no-save-intermediate", "--output-dir", str(tmp_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "gata: 2 generatii" in result.stdout
