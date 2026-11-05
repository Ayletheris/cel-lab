from dataclasses import dataclass, fields
from pathlib import Path


def experiment_problems(config) -> list[str]:
    if isinstance(config, Experiment):
        config = vars(config)
    if not isinstance(config, dict):
        return ["experiment trebuie sa fie un obiect."]
    defaults = {field.name: field.default for field in fields(Experiment)}
    problems = [f"experiment: parametru necunoscut {key}." for key in config.keys() - defaults.keys()]
    values = defaults | config
    for key, minimum in (("N", 1), ("seed", 0), ("checkpoint_interval", 1)):
        value = values[key]
        if type(value) is not int or value < minimum:
            problems.append(f"experiment.{key} trebuie sa fie un intreg >= {minimum}.")
    if type(values["save_intermediate"]) is not bool:
        problems.append("experiment.save_intermediate trebuie sa fie true sau false.")
    directory = values["output_dir"]
    if not isinstance(directory, (str, Path)) or not str(directory).strip() or "\0" in str(directory):
        problems.append("experiment.output_dir trebuie sa fie o cale nevida.")
    return problems


@dataclass(frozen=True)
class Experiment:
    N: int = 100
    seed: int = 0
    save_intermediate: bool = True
    checkpoint_interval: int = 10
    output_dir: str | Path = Path("saves")

    def __post_init__(self):
        problems = experiment_problems(self)
        if problems:
            raise ValueError(" ".join(problems))
        object.__setattr__(self, "output_dir", Path(self.output_dir))

    @classmethod
    def from_sources(cls, config=None, **overrides):
        if isinstance(config, cls):
            config = vars(config)
        if config is None:
            config = {}
        if not isinstance(config, dict):
            raise ValueError("experiment trebuie sa fie un obiect.")
        values = config | overrides
        problems = experiment_problems(values)
        if problems:
            raise ValueError(" ".join(problems))
        return cls(**values)
