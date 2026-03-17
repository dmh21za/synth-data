import ast
import re
from .classes import ConstraintProblem

def _parse_list(s: str) -> list[str] | None:
    """Try to extract a Python list from a string, returning None on failure.
    This means that the LLM won't be punished for text surrounding the list
    """
    s = s.strip()
    match = re.search(r'\[.*\]', s, re.DOTALL)
    if match:
        try:
            result = ast.literal_eval(match.group())
            if isinstance(result, list):
                return result
        except (ValueError, SyntaxError):
            pass
    return None

def verify_solution(problem: ConstraintProblem, output: str) -> bool:
    """
    Verify if a given output from the LLM matches the expected output (the golden label).
    For this implementation I've just checked whether LLM's output == the list of names we inputted to the problem
    However, we could also parse the text and logically deduce the expected output.
    I chose first option just because of time constraint
    """
    normalize = lambda s: s.strip().lower()

    parsed_output = _parse_list(output)
    parsed_label = _parse_list(problem.golden_label)

    if parsed_output is not None and parsed_label is not None:
        return [normalize(x) for x in parsed_output] == [normalize(x) for x in parsed_label]

    return normalize(output) == normalize(problem.golden_label)