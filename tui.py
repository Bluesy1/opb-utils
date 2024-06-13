import questionary

def is_int(s: str) -> bool:
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True
validate_int = lambda text: True if is_int(text) else "Please enter an integer."

question_types = {
    'mcq': {},
    'dropdown': {},
    'checkbox': {},
    'number': {},
    'matrix': {},
    'matching': {},
}

title = questionary.text("Title").ask()
desc = questionary.text("Description").ask()
num_parts = int(questionary.text("Number of parts", validate=validate_int).ask())
num_variants = int(questionary.text("Number of variants with this description+#parts", validate=validate_int, default="1").ask())

for (i, variant) in enumerate(range(num_variants)):
    variant_desc = f"{title} v{i+1}"
    print(variant_desc)
    for part in range(num_parts):
        part_desc = f"v{i+1} - pt.{part+1}"
        question = questionary.text(f"Question text for {part_desc}").ask()
        option = questionary.select(
            f"pt.{part+1} question type?",
            choices=list(question_types.keys())).ask()  # returns value of selection
