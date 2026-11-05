import json

import numpy as np

from cellab.core.model import Automaton, State


def test_model_can_be_created_from_json_and_numpy_grid():
    description = json.loads(
        '{"grid_size":[3,4],"boundary":"fixed","states":[0,1],'
        '"neighborhood":"moore","rules":[]}'
    )
    automaton = Automaton(**description)
    state = State(np.zeros((3, 4), dtype=int))
    assert automaton.grid_size == [3, 4]
    assert state.grid.shape == (3, 4)
    assert state.generation == 0
