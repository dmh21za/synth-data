import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from .classes import ConstraintProblem
from .verify import verify_solution

load_dotenv(dotenv_path=".env")

_client = OpenAI(
    api_key=os.environ["OPENSOURCE_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

MODEL = "openai/gpt-4.1-mini"


def test_problem_against_model(problem: ConstraintProblem, model: str = MODEL) -> dict:
    """Send the problem to the model and check if the answer matches the golden label."""
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": problem.input}],
    )
    model_output = response.choices[0].message.content.strip()
    passed = verify_solution(problem, model_output)
    return {
        "input": problem.input,
        "golden_label": problem.golden_label,
        "model_output": model_output,
        "passed": passed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate constraint ranking problems against a model")
    parser.add_argument(
        "--problems",
        type=str,
        required=True,
        help="Path to a JSON file containing problems (output of generate.py)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output .jsonl file path for results (default: print to stdout)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=MODEL,
        help=f"Model to evaluate (default: {MODEL})"
    )
    parser.add_argument(
        "--num-runs",
        type=int,
        default=1,
        help="Number of times to run each problem (default: 1)"
    )
    parser.add_argument(
        "--problem-index",
        type=int,
        default=None,
        help="Index (0-based) of a single problem to evaluate"
    )

    args = parser.parse_args()

    problems_path = Path(args.problems)
    if not problems_path.exists():
        parser.error(f"Problems file not found: {args.problems}")

    with open(problems_path) as f:
        raw_problems = [json.loads(line) for line in f if line.strip()]

    if not raw_problems:
        parser.error("Problems file is empty")

    if args.problem_index is not None:
        if args.problem_index < 0 or args.problem_index >= len(raw_problems):
            parser.error(f"--problem-index {args.problem_index} is out of range (file has {len(raw_problems)} problems, valid range: 0–{len(raw_problems) - 1})")
        raw_problems = [raw_problems[args.problem_index]]

    output_path = Path(args.output) if args.output else None
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_file = open(output_path, "w")
    else:
        output_file = None

    total_runs = 0
    total_passed = 0

    for i, raw in enumerate(raw_problems):
        problem = ConstraintProblem(input=raw["input"], golden_label=raw["golden_label"])
        extra = {k: v for k, v in raw.items() if k not in ("input", "golden_label")}

        runs = []
        for run in range(args.num_runs):
            result = test_problem_against_model(problem, model=args.model)
            runs.append(result)
            status = "PASS" if result["passed"] else "FAIL"
            print(f"[problem {i + 1}/{len(raw_problems)}, run {run + 1}/{args.num_runs}] {status}")

        num_success = sum(r["passed"] for r in runs)
        total_runs += args.num_runs
        total_passed += num_success

        record = {
            **extra,
            "input": problem.input,
            "golden_label": problem.golden_label,
            "num_runs": args.num_runs,
            "num_success": num_success,
            "runs": runs,
        }

        print(f"  -> problem {i + 1}: {num_success}/{args.num_runs} passed")

        if output_file:
            output_file.write(json.dumps(record) + "\n")
        else:
            print(json.dumps(record, indent=2))

    print(f"\nOverall: {total_passed}/{total_runs} passed ({100 * total_passed / total_runs:.1f}%)")

    if output_file:
        output_file.close()
        print(f"Results saved to {args.output}")
