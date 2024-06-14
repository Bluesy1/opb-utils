import questionary
from issues_to_questions import generate_yes_no_choices
from write_md import write_md_new
from dotenv import load_dotenv
load_dotenv()

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

def generate_given_choices(options: list, answer: str):
    if answer:
        answer = answer.strip().lower()
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
    info = question_types[key]
    if "type" not in info:
        info["type"] = key
    match key:
        case "multiple-choice" | "dropdown" | "checkbox":
            options = []
            # answer = questionary.text("Solution").ask()
            num_options = int(questionary.text("Number of options (excluding solution)", validate=validate_int, default="3").ask())
            for i in range(num_options):
                options.append(questionary.text(f"Option {i+1}. Press enter to generate with GPT.").ask())
            info["choices"] = generate_given_choices(options, solution)
        case "number-input":
            digits = int(questionary.text(f"Suffix", validate=validate_int).ask())
            info["digits"] = suffix
            prefix = questionary.text(f"Prefix").ask()
            if prefix:
                info["label"] = prefix
            suffix = questionary.text(f"Suffix").ask()
            if suffix:
                info["suffix"] = suffix
        case "matching":
            info = {**info, **ch1_matching_type}
    part["info"] = info

chapter = questionary.text("Chapter").ask()
question_numbers = [int(s) for s in split_comma(questionary.text("Question numbers (comma separated)").ask())]
title = questionary.text("Title").ask()
desc = questionary.text("Description").ask()
num_parts = int(questionary.text("Number of parts", validate=validate_int).ask())
num_variants = int(questionary.text("Number of variants with this description+#parts", validate=validate_int, default="1").ask())
issues = split_comma(questionary.text("What issues does this resolve (comma separated)").ask())
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
    # create_part
    for p in range(num_parts):
        part = {}
        part["question"] = questionary.text(f"Question text for v{i+1} - pt.{p+1}").ask()
        # part["info"] =
        part["type"] = questionary.select(
            f"pt.{p+1} question type?",
            choices=list(question_types.keys())).ask()  # returns value of selection
        part["solution"] = questionary.text(f"pt.{p+1} solution?").ask()
        other_asks(part, part["solution"])
        variant["parts"].append(part)

    solutions = [str(part["solution"]) for part in variant["parts"]]
    variants.append(variant)
    write_md_new({
        "title": title,
        "description": variant["desc"],
        "parts": variant["parts"],
        "chapter": chapter,
        "path": f"openstax_C{chapter}_Q{'_Q'.join([str(x) for x in question_numbers])}.md",
        "assets": [],
        "num_variables": {},
        "variables": {},
        "solutions": solutions,
    })

print(variants)
#                 exercises.append({
