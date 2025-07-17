import os
from string import Template

from halligan.utils.constants import Stage


def _get_template(prompt_name: str) -> Template:
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, prompt_name)
    prompt = open(path).read()
    return Template(prompt)


_TEMPLATES: dict[Stage, Template] = {
    Stage.OBJECTIVE_IDENTIFICATION: _get_template("objective_identification.prompt"),
    Stage.STRUCTURE_ABSTRACTION: _get_template("structure_abstraction.prompt"),
    Stage.SOLUTION_COMPOSITION: _get_template("solution_composition.prompt")
}


def get(stage: Stage, **kwargs) -> str:
    """
    Get the prompt template for a stage.
    Construct the final prompt by substituting placeholders.
    Throws KeyError for missing placeholders.
    """
    return _TEMPLATES[stage].substitute({**kwargs})