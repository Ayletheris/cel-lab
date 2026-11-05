import copy
import json
from pathlib import Path

import pytest

from cellab.core.model import Automaton
from cellab.io import load_automaton, load_automaton_from_text, validate


EXAMPLES = Path(__file__).resolve().parents[2] / "automata" / "examples"


def automaton(**changes):
    return Automaton(**{
        "grid_size": [5, 5],
        "boundary": "fixed",
        "states": [0, 1],
        "neighborhood": {"type": "moore", "radius": 1},
        "rules": [
            {"state": 0, "next_state": 1},
            {"state": 1, "next_state": 0},
        ],
        **changes,
    })


def errors(description):
    return [problem for problem in validate(description) if problem.startswith("Eroare:")]


def test_good_automaton_has_no_problems():
    assert validate(automaton()) == []


@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("*.json")), ids=lambda p: p.stem)
def test_complete_examples_have_no_problems(path):
    assert validate(json.loads(path.read_text(encoding="utf-8"))) == []
    assert validate(load_automaton(path)) == []


@pytest.mark.parametrize("field", ["state", "next_state", "neighbor_state"])
def test_undeclared_state_in_internal_rule(field):
    rule = {"state": 0, "next_state": 1, "neighbor_state": 1, "counts": [2]}
    rule[field] = 7
    assert any(f".{field}: stare nedeclarata" in p for p in errors(automaton(rules=[rule])))


@pytest.mark.parametrize("field", ["from", "to", "count", "otherwise"])
def test_undeclared_state_in_json_rule(field):
    rule = {"type": "count", "from": 0, "count": 1, "in": [2], "to": 1, "otherwise": 0}
    rule[field] = 7
    assert any(f".{field}: stare nedeclarata" in p for p in errors(automaton(rules=[rule])))


def test_nested_conditions_check_all_state_references():
    rule = {"condition": {"all": [
        {"neighbor_state": 8, "exact": 2},
        {"any": [{"more_than": [9, 10]}]},
    ]}, "next_state": 1}
    assert len(errors(automaton(rules=[rule]))) == 3


def test_conflicting_rules_with_reordered_counts():
    rules = [
        {"state": 1, "neighbor_state": 1, "counts": [2, 3], "next_state": 1},
        {"state": 1, "neighbor_state": 1, "counts": [3, 2], "next_state": 0},
    ]
    assert any("rules[1] contrazice rules[0]" in p for p in errors(automaton(rules=rules)))


def test_conflicting_nested_conditions_ignore_key_and_conjunction_order():
    first = {"state": 0, "condition": {"all": [
        {"neighbor_state": 0, "exact": 1}, {"neighbor_state": 1, "at_least": 2},
    ]}, "next_state": 1}
    second = copy.deepcopy(first)
    second["condition"]["all"].reverse()
    second["next_state"] = 0
    assert any("contrazice" in p for p in errors(automaton(rules=[first, second])))


def test_conflicting_otherwise_results():
    first = {"type": "count", "from": 0, "count": 1, "in": [2], "to": 1, "otherwise": 0}
    second = {**first, "otherwise": 1}
    assert any("contrazice" in p for p in errors(automaton(rules=[first, second])))


def test_loader_does_not_silently_discard_contradictions():
    data = json.loads((EXAMPLES / "life.json").read_text(encoding="utf-8"))
    data["rules"].append({**data["rules"][0], "to": 0})
    with pytest.raises(ValueError, match="contrazice"):
        load_automaton_from_text(json.dumps(data))


def test_identical_rules_and_different_conditions_do_not_conflict():
    rules = [
        {"state": 0, "neighbor_state": 1, "counts": [2], "next_state": 1},
        {"state": 0, "neighbor_state": 1, "counts": [2], "next_state": 1},
        {"state": 0, "neighbor_state": 1, "counts": [3], "next_state": 0},
        {"state": 1, "next_state": 0},
    ]
    assert validate(automaton(rules=rules)) == []


@pytest.mark.parametrize("size", [[0, 5], [5, 0], [-1, 5], [5, -1], [False, 5], [1.5, 5]])
def test_invalid_grid_size(size):
    assert any("intreg pozitiv" in p for p in errors(automaton(grid_size=size)))


@pytest.mark.parametrize("neighborhood", ["unknown", {"type": "hex", "radius": 1}, 42])
def test_unknown_neighborhood(neighborhood):
    assert any("vecinatate necunoscuta" in p for p in errors(automaton(neighborhood=neighborhood)))


@pytest.mark.parametrize("probability", [-0.01, 1.01, float("nan"), float("inf"), "0.5", None, True])
def test_invalid_probability(probability):
    rules = [{"next_state": 1, "prob": probability}]
    assert any("probabilitatea" in p for p in errors(automaton(rules=rules)))


@pytest.mark.parametrize("probability", [0, .5, 1])
def test_valid_probability(probability):
    assert validate(automaton(rules=[{"next_state": 1, "prob": probability}])) == []


def test_state_without_rule_warns_that_it_stays_unchanged():
    assert validate(automaton(rules=[{"state": 0, "next_state": 1}])) == [
        "Avertisment: starea 1 nu are nicio regula; va ramane la fel.",
    ]


def test_missing_parameters_report_defaults_without_mutation():
    description = automaton(grid_size=None, boundary=None, neighborhood=None)
    before = copy.deepcopy(description)
    problems = validate(description)
    assert len(problems) == 5
    assert all(p.startswith("Avertisment:") for p in problems)
    assert any("grid.width; se foloseste 50" in p for p in problems)
    assert any("grid.height; se foloseste 50" in p for p in problems)
    assert any("grid.boundary; se foloseste wrap" in p for p in problems)
    assert any("neighborhood.type; se foloseste moore" in p for p in problems)
    assert description == before


def test_loaded_defaults_are_reported_once():
    description = load_automaton_from_text('{"rules": [{"type": "count", "from": 0, "to": 1}, {"type": "count", "from": 1, "to": 0}]}')
    problems = validate(description)
    assert len(problems) == len(description.defaults_used)
    assert len(problems) == len(set(problems))
    assert all(p.startswith("Avertisment:") for p in problems)
    assert description.grid_size == [50, 50]
    assert description.boundary == "toroidal"


def test_reports_all_problems_in_one_call():
    description = automaton(grid_size=[0, -2], neighborhood="unknown", rules=[
        {"state": 0, "next_state": 9, "prob": 2},
        {"state": 0, "next_state": 0},
    ])
    problems = validate(description)
    assert len(problems) == 7
    for text in ("grid.height", "grid.width", "vecinatate necunoscuta", "stare nedeclarata",
                 "probabilitatea", "contrazice", "va ramane la fel"):
        assert any(text in p for p in problems)


@pytest.mark.parametrize("changes", [
    {"grid_size": "bad"}, {"states": {"bad": 1}}, {"states": [[0], {}]},
    {"rules": None}, {"rules": [None, [], "bad"]},
    {"rules": [{"state": {}, "condition": {"all": None}, "next_state": []}]},
    {"rules": [{"condition": {"more_than": None}}]},
    {"rules": [{"condition": []}]},
    {"neighborhood": {"type": [], "radius": "bad"}},
])
def test_malformed_fields_return_a_list_without_crashing(changes):
    problems = validate(automaton(**changes))
    assert isinstance(problems, list) and problems
    assert all(isinstance(p, str) for p in problems)


@pytest.mark.parametrize("value", [None, [], "invalid", 42])
def test_invalid_root_returns_a_problem(value):
    assert validate(value) == ["Eroare: se asteapta un Automaton sau un obiect JSON."]


def test_next_mod_checks_declared_states():
    rule = {"next_state": {"next_mod": 3}}
    assert any("stari nedeclarate" in p for p in errors(automaton(rules=[rule])))
    assert validate(automaton(states=[0, 1, 2], rules=[rule])) == []
