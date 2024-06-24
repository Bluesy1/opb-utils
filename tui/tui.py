import json
import os
import pathlib
import random
import shlex
import shutil
import subprocess
import traceback

import questionary
from problem_bank_scripts import process_question_pl

from .generate_questions import generate_true_false_choices, generate_yes_no_choices
from .write_md import write_md


ch1_matching_type = {
    "type": "matching",
    "options": [
        '"Not a variable in the study"',
        '"Numerical and discrete variable"',
        '"Numerical and continuous variable"',
        '"Categorical"',
        # 'option4': 'Categorical and not ordinal variable',
    ],
    "statements": [
        {"value": '"Statement 1"', "matches": "Not a variable in the study"},
        {"value": '"Statement 2"', "matches": "Numerical and discrete variable"},
        {"value": '"Statement 3"', "matches": "Numerical and continuous variable"},
        {"value": '"Statement 4"', "matches": "Categorical"},
    ],
}


def write_json(data: dict, filename="saved.json"):
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def read_json(filename: str ="saved.json"):
    with open(filename) as f:
        return json.load(f)


def generate_given_choices(options: list[str], answer: str, question: str, use_gpt: bool):
    if answer:
        answer = answer.strip().lower()
    # Count how many empty string options
    num_empty = len([x for x in options if not x.strip()])
    options = [x.strip() for x in options if x.strip()]
    if num_empty > 0:
        if use_gpt:
            from .gpt import ask_mc_options

            options += ask_mc_options(options, answer, question, num_empty)
        else:
            options += ["Placeholder"] * num_empty

    choices = [{"value": f'"{option}"', "correct": False, "feedback": '"Try again please!"'} for option in options]

    correct = len(choices)
    if answer in options:
        correct = options.index(answer)
    else:
        choices.append({})
    choices[correct]["value"] = f'"{answer}"'
    choices[correct]["correct"] = True
    choices[correct]["feedback"] = '"Correct!"'
    # TODO: replace empty options with GPT generated text
    return choices


def is_int(s: str) -> bool:
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True


def validate_int(text: str):
    return True if is_int(text) else "Please enter an integer."


def ask_int(question: str, default: int | str = "") -> int:
    return int(questionary.text(question, validate=validate_int, default=str(default)).ask())


QUESTION_TYPES = {
    "multiple-choice": {},
    "number-input": {},
    "longtext": {},
    "dropdown": {},
    "checkbox": {},
    "matrix": {},
    "matching": {},
    "true-false": {"type": "multiple-choice"},
    "yes-no": {"type": "multiple-choice", "choices": generate_yes_no_choices()},
    "file-upload": {},
}


def split_comma(text: str) -> list[str]:
    return [x.strip() for x in text.split(",")]


def other_asks(part: dict, solution: str, use_gpt: bool):
    key = part["type"]
    question = part["question"]
    info = QUESTION_TYPES[key]
    if "type" not in info:
        info["type"] = key
    match key:
        case "multiple-choice" | "dropdown" | "checkbox":
            options: list[str] = []
            # answer = questionary.text("Solution").ask()
            num_options = ask_int("Number of options (excluding solution)", default=3)
            for i in range(num_options):
                options.append(questionary.text(f"Option {i+1}. Press enter to generate with GPT.").ask())
            info["choices"] = generate_given_choices(options, solution, question, use_gpt)
        case "yes-no":
            info["choices"] = generate_yes_no_choices(solution)
            info["fixed-order"] = "true"
        case "true-false":
            info["choices"] = generate_true_false_choices(solution)
            info["fixed-order"] = "true"
        case "number-input":
            digits = ask_int("Digits")
            info["digits"] = digits
            prefix = questionary.text("Prefix", default="$p=$").ask()
            if prefix:
                info["label"] = prefix
            suffix = questionary.text("Suffix").ask()
            if suffix:
                info["suffix"] = suffix
            if use_gpt:
                from .gpt import ask_number_code

                info["code"] = ask_number_code(question, solution)
            else:
                info["code"] = "..."
        case "matching":
            info = {**info, **ch1_matching_type}
    part["info"] = info


def extract_variables(text: str, variables: dict) -> str:
    res = ""
    open_i = None
    for i in range(len(text)):
        if text[i] == "{":
            open_i = i
        if open_i is None:  # has to be in the middle
            res += text[i]
        if text[i] == "}" and open_i is not None:
            var = text[open_i+1:i]  # fmt: skip
            name = ""
            value = None
            split = var.split(":")
            name = split[0].strip()
            if len(split) > 1:
                value = split[1].strip()
            if value:
                variables[name] = value
            res += f"{{{{ params.{name} }}}}"
            open_i = None
    if open_i is not None:
        raise ValueError("Unmatched {")
    return res.strip()


def question_type_from_solution(solution: str) -> str | None:
    if solution.lower() in ["true", "false"]:
        return "true-false"
    if solution.lower() in ["yes", "no"]:
        return "yes-no"
    return None


def ask_if_not_exists(exercise: dict, key: str, question: str, variables: dict, default="", parser=lambda x: x):
    if key not in exercise:
        value = parser(questionary.text(question, default=default).ask())
        if isinstance(value, str):
            value = extract_variables(value, variables=variables)
        exercise[key] = value
        write_json(exercise)
    return exercise[key]


def set_default(exercise: dict, key: str, value: str | list):
    if key not in exercise:
        exercise[key] = value
        write_json(exercise)
    return exercise[key]


def run_tui(*, create_pr: bool = False, use_gpt: bool = False):
    exercise = {}
    variables = {}
    if os.path.isfile("saved.json") and questionary.confirm("Would you like to use saved data?").ask():
        exercise = read_json()
        if "variables" in exercise:
            variables = exercise["variables"]
    try:
        set_default(exercise, "assets", [])
        chapter = ask_if_not_exists(exercise, key="chapter", question="Chapter", variables=variables)

        question_numbers = ask_if_not_exists(
            exercise,
            key="question_numbers",
            question="Question numbers (comma separated)",
            variables=variables,
            parser=lambda x: [int(s) for s in split_comma(x)],
        )
        branch_name = f"openstax_C{chapter}_Q{'_Q'.join([str(x) for x in question_numbers])}"
        exercise["branch_name"] = branch_name
        exercise["path"] = f"{branch_name}.md"
        issues = ask_if_not_exists(
            exercise,
            key="issues",
            question="What issues does this resolve (comma separated, numbers only)",
            variables=variables,
            parser=split_comma,
        )
        title = ask_if_not_exists(exercise, key="title", question="Title", variables=variables)
        desc = ask_if_not_exists(exercise, key="description", question="Description", variables=variables)

        if "extras" not in exercise:
            exercise["extras"] = questionary.checkbox(
                "Select extra",
                choices=[
                    "table",
                    "image",
                    "graph",
                ],
            ).ask()

        if "image" in exercise["extras"]:
            exercise["assets"] += split_comma(questionary.text("Image paths (comma separated)").ask())
        if "table" in exercise["extras"]:
            num_tables = ask_int("How many tables", default=1)
            tables = []
            for i in range(num_tables):
                table = {"matrix": []}
                table_str: str = questionary.text("Paste in table").ask()
                table["first_row_is_header"] = questionary.confirm("Is the first row a header?").ask()
                table["first_col_is_header"] = questionary.confirm("Is the first column a header?").ask()
                rows = table_str.split("\n")
                for row_str in rows:
                    row_str = row_str.strip()
                    if not row_str:
                        continue
                    row = [x.strip() for x in row_str.split("\t")]
                    print("row", row)
                    table["matrix"].append(row)
                tables.append(table)
                # [["a", "b", "c"], ["x", "1"]]
            exercise["tables"] = tables
        if "graph" in exercise["extras"]:
            num_graphs = ask_int("How many graphs", default=1 if "graphs" not in exercise else len(exercise["graphs"]))
            exercise["graphs"] = exercise.get("graphs", [])
            graphs_done = len(exercise["graphs"])
            for i in range(graphs_done, num_graphs):
                graph: dict = {
                    "variables": {},
                }
                graph["type"] = questionary.select(
                    f"Graph {i+1} type",
                    choices=["bar", "line", "scatter", "box plot", "histogram", "other"],
                    default="box plot",
                ).ask()
                if graph["type"] == "box plot":
                    is_vertical = questionary.confirm("Is the box plot vertical?").ask()
                    graph["is_vertical"] = is_vertical
                    num_box = ask_int("Number of box plots", default=1)
                    if num_box > 1:
                        graph["data"] = [[None] for i in range(num_box)]
                    else:
                        graph["data"] = [None]
                default_graph_dict = {
                    "box plot": "q3",
                    "histogram": "num_bins",
                }
                known_info = questionary.checkbox(
                    "Select known/controlled params",
                    choices=[
                        "title",
                        "x_label",
                        "y_label",
                        "data",
                        "mean",
                        "median",
                        "std",
                        "num_bins",
                        "min_val",
                        "max_val",
                        "q1",
                        "q3",
                        "whislow",
                        "whishigh",
                        "sample_size",
                    ],
                    default=default_graph_dict.get(graph["type"], None),
                ).ask()
                if "median" in known_info and "mean" in known_info:
                    print("Cannot have both mean and median. Only median will be applied.")
                for op in known_info:
                    graph["variables"][op] = questionary.text(f"{i+1}) {graph['type']} {op} =").ask()
                if len(exercise["graphs"]) > i:
                    exercise["graphs"][i] = graph
                else:
                    exercise["graphs"].append(graph)
                write_json(exercise)

        num_parts = ask_int("Number of parts", default=len(exercise["parts"]) if "parts" in exercise else "")
        num_variants = 1  # ask_int("Number of variants with this description+#parts", default=1)
        variants = []
        print("num_parts", num_parts)
        #     {
        #         "question": f"A market researcher polls every {nth} person who walks into a store.",
        #         "options": options_sampling
        #     },
        #     {
        #         "question": f"A computer generates {rand_n} random numbers, and {rand_n} people whose names correspond with the numbers on the list are chosen.",
        #         "options": options_sampling_2
        #     }

        for i, variant in enumerate(range(num_variants)):
            print(f"{title} v{i+1}")
            variant = {"desc": desc, "parts": set_default(exercise, "parts", [])}
            solutions = [part["solution"] for part in variant["parts"]]
            # solutions = [] if "solutions" not in exercise else exercise["solutions"]
            print("solutions", solutions)
            parts_start_at = 0 if "parts" not in exercise else len(exercise["parts"])
            for p in range(parts_start_at, num_parts):
                if p >= len(solutions):
                    solutions.append(questionary.text(f"pt.{p+1} solution?").ask())
            # create_part
            for p in range(parts_start_at, num_parts):
                part = {}
                part["solution"] = extract_variables(solutions[p], variables=variables)
                part["question"] = extract_variables(
                    questionary.text(f"Question text for v{i+1} - pt.{p+1}").ask(), variables=variables
                )

                part["type"] = questionary.select(
                    f"pt.{p+1} question type?",
                    choices=list(QUESTION_TYPES.keys()),
                    default=question_type_from_solution(part["solution"]),
                ).ask()  # returns value of selection
                other_asks(part, part["solution"], use_gpt)
                variant["parts"].append(part)

            variants.append(variant)

        variant = random.choice(variants)
        exercise = {
            **exercise,
            "title": title,
            "description": variant["desc"],
            "parts": variant["parts"],
            "chapter": chapter,
            "path": f"{branch_name}.md",
            "num_variables": {},
            "variables": variables,
            "solutions": solutions,
            "imports": [],
            "finished": True,
        }
        write_json(exercise)
        print("Wrote to saved.json")
        full_path = pathlib.Path(write_md(exercise))
        if create_pr:
            GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
            WRITE_PATH = pathlib.Path(os.environ["WRITE_PATH"])
            print(f"Copying question to {WRITE_PATH / full_path.parent.name}")
            shutil.copytree(src=full_path.parent, dst=WRITE_PATH / full_path.parent.name, dirs_exist_ok=True)
            CWD = WRITE_PATH / full_path.parent.name
            pr_body = [f"Closes #{issue}" for issue in issues]
            pr_body.append(
                "OPB 000: https://ca.prairielearn.com/pl/course_instance/4024/instructor/course_admin/questions"
            )
            pr_body = "\n".join(pr_body)
            commands = [
                f"git checkout --no-track -b {branch_name!r} origin/main",
                "git add .",
                "git commit -m 'Autogenerated Template'",
                f"git push -u origin {branch_name!r}",
                f"gh pr create --draft -t {branch_name!r} -b '{pr_body}' --assignee {GITHUB_USERNAME!r}",
            ]
            for command in commands:
                print(f"Running: {command!r}")
                ret = subprocess.run(
                    shlex.split(command),
                    cwd=CWD,
                    capture_output=True,
                    check=True,
                    text=True,
                )
                print(ret.stdout)
        PL_QUESTION_PATH = pathlib.Path(os.environ["PL_QUESTION_PATH"])
        process_question_pl(full_path, output_path=PL_QUESTION_PATH / full_path.parent.name, dev=True)
        print(variants)
    except Exception as e:
        write_json(exercise)
        print("Wrote to saved.json")
        traceback.print_exc()
        if isinstance(e, subprocess.CalledProcessError):
            print(e.stdout)
            print(e.stderr)
        return 1
    return 0
