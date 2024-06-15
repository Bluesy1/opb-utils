import questionary
from issues_to_questions import generate_yes_no_choices, generate_true_false_choices
from write_md import write_md_new
from gpt import ask_mc_options
import os
from dotenv import load_dotenv
import re
import subprocess
import random
load_dotenv()
TESTING = True

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")

ch1_matching_type = {
    'type': 'matching',
    'options': [
        '"Not a variable in the study"',
        '"Numerical and discrete variable"',
        '"Numerical and continuous variable"',
        '"Categorical"',
        # 'option4': 'Categorical and not ordinal variable',
    ],
    'statements': [
        {'value': '"Statement 1"', 'matches': 'Not a variable in the study' },
        {'value': '"Statement 2"', 'matches': 'Numerical and discrete variable' },
        {'value': '"Statement 3"', 'matches': 'Numerical and continuous variable' },
        {'value': '"Statement 4"', 'matches': 'Categorical' },
    ],
}

def generate_given_choices(options: list, answer: str, question: str):
    if answer:
        answer = answer.strip().lower()
    # Count how many empty string options
    num_empty = len([x for x in options if not x.strip()])
    options = [x.strip() for x in options if x.strip()]
    if num_empty > 0:
        options += ask_mc_options(options, answer, question, num_empty)

    choices = [
        {
            "value": f'"{option}"',
            "correct": False,
            "feedback": '"Try again please!"'
        }
    for option in options]

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
validate_int = lambda text: True if is_int(text) else "Please enter an integer."

def ask_int(question: str, default="") -> int:
    return int(questionary.text(question, validate=validate_int, default=str(default)).ask())

question_types = {
    'multiple-choice': {
        "ask_choices": True,
    },
    'number-input': {
    },
    'longtext': {
    },
    'dropdown': {
        "ask_choices": True,
    },
    'checkbox': {
        "ask_choices": True,
    },
    'matrix': {
    },
    'matching': {
    },
    'true-false': {
        "type": "multiple-choice",
    },
    'yes-no': {
        "type": "multiple-choice",
        'choices': generate_yes_no_choices(),
    },
    'file-upload': {
    },
}

def split_comma(text: str) -> list:
    return [x.strip() for x in text.split(",")]

def other_asks(part: dict, solution: str):
    key = part["type"]
    question = part["question"]
    info = question_types[key]
    if "type" not in info:
        info["type"] = key
    match key:
        case "multiple-choice" | "dropdown" | "checkbox":
            options = []
            # answer = questionary.text("Solution").ask()
            num_options = ask_int("Number of options (excluding solution)", default=3)
            for i in range(num_options):
                options.append(questionary.text(f"Option {i+1}. Press enter to generate with GPT.").ask())
            info["choices"] = generate_given_choices(options, solution, question)
        case "yes-no":
            info["choices"] = generate_yes_no_choices(solution)
            info["fixed-order"] = "true"
        case "true-false":
            info["choices"] = generate_true_false_choices(solution)
            info["fixed-order"] = "true"
        case "number-input":
            digits = ask_int("Digits")
            info["digits"] = digits
            prefix = questionary.text(f"Prefix", default="$d=$").ask()
            if prefix:
                info["label"] = prefix
            suffix = questionary.text(f"Suffix").ask()
            if suffix:
                info["suffix"] = suffix
        case "matching":
            info = {**info, **ch1_matching_type}
    part["info"] = info

def extract_variables(text: str, variables: dict) -> list:
    res = ""
    open_i = None
    for i in range(len(text)):
        if text[i] == "{":
            open_i = i
        if open_i is None: # has to be in the middle
            res += text[i]
        if text[i] == "}" and open_i is not None:
            var = text[open_i+1:i]
            name = ""
            value = None
            split = var.split(":")
            name = split[0]
            if len(split) > 1:
                value = split[1]
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

def start_tui():
    exercise = {}
    assets = []
    variables = {}
    chapter = questionary.text("Chapter").ask()
    question_numbers = [int(s) for s in split_comma(questionary.text("Question numbers (comma separated)").ask())]
    issues = split_comma(questionary.text("What issues does this resolve (comma separated)").ask())
    title = questionary.text("Title").ask()
    desc = extract_variables(questionary.text("Description").ask(), variables=variables)

    extras = questionary.checkbox(
        'Select extra',
        choices=[
            "table",
            "image",
            "graph",
        ]).ask()

    if "image" in extras:
        assets += split_comma(questionary.text("Image paths (comma separated)").ask())
    if "table" in extras:
        num_tables = ask_int("How many tables", default=1)
        tables = []
        for i in range(num_tables):
            table = {
                "matrix": []
            }
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
    if "graph" in extras:
        num_graphs = ask_int("How many graphs", default=1)
        graphs = []
        for i in range(num_graphs):
            graph = {
                "variables": {},
            }
            graph["type"] = questionary.select(
                f"Graph {i+1} type",
                choices=["bar", "line", "scatter", "box plot", "histogram", "other"],
                default="box plot"
            ).ask()
            if graph["type"] == "box plot":
                num_box = ask_int("Number of box plots", default=1)
                if num_box > 1:
                    graph["data"] = [[None] for i in range(num_box)]
                else:
                    graph["data"] = [None]

            known_info = questionary.checkbox(
                'Select known/controlled params',
                choices=[
                    "title",
                    "x_label",
                    "y_label",
                    "data",
                    "mean",
                    "median",
                    "mean",
                    "std",
                    "num_bins",
                    "q1",
                    "q3",
                    "min",
                    "max",
                    "sample_size",
                ]).ask()
            if "median" in known_info and "mean" in known_info:
                print("Cannot have both mean and median. Only median will be applied.")
            for op in known_info:
                graph["variables"][op] = questionary.text(f"{i+1}) {graph['type']} {op} =").ask()
            graphs.append(graph)

        exercise["graphs"] = graphs

    num_parts = ask_int("Number of parts")
    num_variants = 1 # ask_int("Number of variants with this description+#parts", default=1)
    variants = []
    #     {
#         "question": f"A market researcher polls every {nth} person who walks into a store.",
#         "options": options_sampling
#     },
#     {
#         "question": f"A computer generates {rand_n} random numbers, and {rand_n} people whose names correspond with the numbers on the list are chosen.",
#         "options": options_sampling_2
#     }

    for (i, variant) in enumerate(range(num_variants)):
        print(f"{title} v{i+1}")
        variant = {
            "desc": desc,
            "parts": []
        }
        solutions = []
        for p in range(num_parts):
            solutions.append(questionary.text(f"pt.{p+1} solution?").ask())
        # create_part
        for p in range(num_parts):
            part = {}
            part["solution"] = extract_variables(solutions[p], variables=variables)
            part["question"] = extract_variables(questionary.text(f"Question text for v{i+1} - pt.{p+1}").ask(), variables=variables)

            part["type"] = questionary.select(
                f"pt.{p+1} question type?",
                choices=list(question_types.keys()),
                default=question_type_from_solution(part["solution"])
                ).ask()  # returns value of selection
            other_asks(part, part["solution"])
            variant["parts"].append(part)

        variants.append(variant)

    variant = random.choice(variants)
    path = f"openstax_C{chapter}_Q{'_Q'.join([str(x) for x in question_numbers])}"
    exercise = {
        **exercise,
        "title": title,
        "description": variant["desc"],
        "parts": variant["parts"],
        "chapter": chapter,
        "path": f"{path}.md",
        "assets": assets,
        "num_variables": {},
        "variables": variables,
        "solutions": solutions,
        "imports": [],
        "extras": extras,
    }
    # print(exercise)
    full_path = write_md_new(exercise)
    if not TESTING:
        # subprocess.check_call("./git-pr-first.sh %s %s %s" % (path, str(arg2), arg3), shell=True)
        subprocess.check_call(f'./git-pr-first.sh {path} "{title}" {GITHUB_USERNAME} {" ".join(issues)}', shell=True)
    subprocess.call(f'./pl-questions.sh', shell=True)

    print(variants)
#                 exercises.append({

if __name__ == "__main__":
    start_tui()
