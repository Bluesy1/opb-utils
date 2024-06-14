import os
import shutil
from utils import replace_file_line, apply_indent, write_file, apply_params_to_str, string_is_numeric, insert_into_file, count_decimal_places
import tempfile
from constants import textbook_chapter_to_name, topics
from pdf2image import convert_from_path
import json
from table import find_all_figures
import pandas as pd
from similarity import text_similarity
from dotenv import load_dotenv
load_dotenv()
# question What is the variance of the mean of these $n$ values: $\frac{X_1 + X_2 + \dots + X_n}{n}$?
TEXTBOOK_PATH = os.environ.get("TEXTBOOK_PATH")
# WRITE_PATH = os.environ.get("WRITE_PATH")
GITHUB_ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
WRITE_PATH = './questions'
INFO_PATH = './info'
MY_NAME = os.environ.get("MY_NAME")
MY_INITIALS = os.environ.get("MY_INITIALS")

def md_part_lines(part, i, params=None, solution=None):
    q_type = part['info']['type']
    answer_section = ''
    if q_type == 'number-input':
        answer_section ='Please enter a numeric value in.\n'
    elif q_type == 'multiple-choice' or q_type == 'dropdown':
        choices = part['info']['choices']
        answer_section = '\n'.join([f'- {{{{ params.part{i+1}.ans{j+1}.value }}}}' for j in range(len(choices))])
    elif q_type == 'file-upload':
        answer_section ='File upload box will be shown here.\n'
    # answer_section2 = '### pl-answer-panel\n\nEverything here will get inserted directly into an pl-answer-panel element at the end of the `question.html`.\nPlease remove this section if it is not application for this question.'
    # if part['type'] == 'multiple-choice':

    result = [
        f'## Part {i+1}', '',
        part['question'], '',
    ]

    result += [
        '### Answer Section\n',
        answer_section, '',
        # answer_section2,
        ]

    if solution:
        if params:
            formated_soln = apply_params_to_str(solution, params)
            result += ['### pl-answer-panel', '', f'{formated_soln}', '']
        else:
            result += ['### pl-answer-panel', '', f'{solution}', '']

    return result + ['']


def get_pl_customizations(info: dict = {}, index: int = 0):
    type = info['type']
    pl_indent = '    '
    ans = []
    if type == 'multiple-choice':
        ans = ['weight: 1']
    elif type == 'number-input':
        # TODO: need to know if integer or not
        if 'sigfigs' in info and info['sigfigs'] == 'integer':
            ans = ['weight: 1', 'allow-blank: true'] #'label: $d= $',
        else:
            ans = ['comparison: decdig', 'digits: 2', 'weight: 1', 'allow-blank: true', 'label: $d= $']
        if 'suffix' in info:
            ans.append(f'suffix: {info["suffix"]}')
        # ans = ['weight: 1', 'allow-blank: true'] # for integer
    elif type == 'dropdown':
        ans = ['weight: 1', 'blank: true']
    elif type == 'checkbox':
        ans = ['weight: 1', 'partial-credit: true', 'partial-credit-method: EDC']
    elif type == 'symbolic-input':
        ans = ['label: $F_r = $', 'variables: "m, v, r"', 'weight: 1', 'allow-blank: false']
    elif type == 'longtext':
        ans = ['placeholder: "Type your answer here..."', f'file-name: "answer{index+1}.html"', 'quill-theme: "snow"', 'directory: clientFilesQuestion', 'source-file-name: sample.html']
    elif type == 'file-upload':
        ans = ['file-names: "file.png, file.jpg, file.pdf, filename space.png"']
    elif type == 'matching':
        ans = ['weight: 1', 'blank: true']
    return ['  pl-customizations:'] + apply_indent(lines=ans, indent=pl_indent)



def format_type_info(info: dict):
    indent = '  '
    info_type = info['type']
    list = [f'type: {info["type"]}']
    if info_type == 'longtext':
        list.append('gradingMethod: Manual')
    if info_type == 'number-input' and 'sigfigs' in info and info['sigfigs'] == 'integer':
        list.append('label: $d=$')
    if info_type == 'matching':
        list.append('showCorrectAnswer: true')
    return apply_indent(list, indent)


def move_figure(chapter: str, a: str, exercise_path: str):
    dir_path = WRITE_PATH + '/' + ''.join(exercise_path.split('.')[:-1])

    fig_dir = '/'.join(a.split('/')[:-1])
    # print(fig_dir)
    # if not fig_dir.split:
    #     fig_dir = a
    figures_prefix = f'{textbook_chapter_to_name[chapter]}/figures/'
    if 'figures' in a:
        figures_prefix = ''
    figure_dir_path = f"{TEXTBOOK_PATH}/{figures_prefix}{fig_dir}"
    figure_name = ''
    # filebase
    tmp_name = a.split('/')[-1]
    for figure in os.listdir(figure_dir_path):
        if figure.lower().startswith(tmp_name.lower()):
            figure_name = figure
            break
    # figure_name = os.listdir(figure_dir_path)
    figure_no_extension_name, ext = figure_name.split('.')
    if ext == 'pdf':
        images = None
        with tempfile.TemporaryDirectory() as tmp_path:
            images = convert_from_path(f'{figure_dir_path}/{figure_name}', output_folder=tmp_path, use_cropbox=True)
            figure_name = f'{figure_no_extension_name}.jpg'
            if len(images) > 0:
                images[0].save(f'{dir_path}/{figure_name}', 'JPEG')
    else:
            shutil.copyfile(f'{figure_dir_path}/{figure_name}', f'{dir_path}/{figure_name}')
    return figure_name


def num_variable_to_line_value(num: float):
    randomized_str = ''
    if num.is_integer():
        if abs(num) > 15:
            range_value = abs(num)//10
            add = 0
        else:
            range_value = abs(num)
            add = 2 if num >=3 else 0
        randomized_str = f"random.randint({int(num - range_value + add)}, {int(num + range_value)})"
        num = int(num)
        if 1900 < num < 2090:
            randomized_str = num
    else:
        count_after_decimal = count_decimal_places(num)
        if abs(num) <= 0.5:
            range_value = round(abs(num)*2, count_after_decimal)
        else:
            range_value = round(abs(num)/10, count_after_decimal)
        randomized_str = f"round(random.uniform({round(num - range_value, count_after_decimal)}, {round(num + range_value, count_after_decimal)}), {count_after_decimal})"
    return f"{randomized_str}  # {num}"

def write_code(exercise: dict):
    indent = '        '
    lines = ["data2 = pbh.create_data2()", "", f'data2["params"]["vars"]["title"] = "{exercise["title"]}"']

    num_variables = exercise['num_variables']
    variables = exercise['variables']
    # Randomize Variables
    # v = random.randint(2,7)
    # t = random.randint(5,10)

    # region Handle variables
    used_by = {}
    for (var_name, value) in variables.items():
        if type(value) == float:
            num = value
            used = used_by[num] if (num in used_by) else ''
            if not used:
                used_by[num] = var_name
            line = f"{var_name} = {num_variable_to_line_value(num)}" if not used else f"{var_name} = {used}"
            lines.append(line)
        else:
            lines.append(f"{var_name} = {value}")
            used_by[value] = var_name
    lines.append('')
    for (var_name, value) in variables.items():
        values = var_name.split('_')
        cur_var_line = f"data2['params']"
        for val in values:
            cur_var_line += f"['{val}']"
        cur_var_line += f" = {var_name}"
        lines.append(cur_var_line)
    lines.append('')

    lines.append('# Randomize Variables')
    for (key, values) in num_variables.items():
        for (i, num) in enumerate(values):
            cur_var_name = f"{key}_num{i+1}"
            used = used_by[num] if (num in used_by) else ''
            if not used:
                used_by[num] = cur_var_name

            line = f"{cur_var_name} = {num_variable_to_line_value(num)}" if not used else f"{key}_num{i+1} = {used}"
            lines.append(line)

    lines.append('')
    lines.append('# store the variables in the dictionary "params"')
    for (key, values) in num_variables.items():
        for (i, num) in enumerate(values):
            lines.append(f"data2['params']['{key}']['num{i+1}'] = {key}_num{i+1}")
    lines.append('')

    # endregion handle variables

    if len(exercise['parts']) != len(exercise['solutions']):
        print(f"MISMATCH: parts {len(exercise['parts'])}, solns {len(exercise['solutions'])}")
        print("parts:")

        print(json.dumps([x["question"] for x in exercise['parts']], indent=2))
        print("solns:")
        print(json.dumps(exercise['solutions'], indent=2))

    for solution in exercise['solutions']:

        figures = find_all_figures(solution)
        for a in figures:
            move_figure(exercise['chapter'], a, exercise['path'])

    for part_num, part in enumerate(exercise['parts']):
        if part['info']['type'] == 'multiple-choice' or part['info']['type'] == 'dropdown':
            lines.append(f"# Part {part_num+1} is a {part['info']['type']} question.")
            for choice_num, choice in enumerate(part['info']['choices']):
                for (key, val) in choice.items():
                    lines += [f"data2['params']['part{part_num+1}']['ans{choice_num+1}']['{key}'] = {val}"]
                lines.append('')
            lines.append('')
        if part['info']['type'] == 'matching':
            lines.append(f"# Part {part_num+1} is a {part['info']['type']} question.")
            for (key, val) in part['info']['options'].items():
                lines += [f'data2["params"]["part{part_num+1}"]["{key}"]["value"] = {val}']
            lines.append('')
            for s_num, statement_info in enumerate(part['info']['statements']):
                lines += [f'data2["params"]["part{part_num+1}"]["statement{s_num+1}"]["value"] = {statement_info["value"]}']
                lines += [f'data2["params"]["part{part_num+1}"]["statement{s_num+1}"]["matches"] = "{statement_info["matches"]}"']
            lines.append('')
        if part['info']['type'] == 'number-input':
            numeric_answer = None
            words = exercise['solutions'][part_num].strip().split(' ')
            if len(words) == 1 and string_is_numeric(exercise['solutions'][part_num].replace(',', '').strip()):
                numeric_answer = float(exercise['solutions'][part_num].replace(',', '').strip())
                exercise['solutions'][part_num] = f'{{{{ correct_answers.part{part_num+1}_ans }}}}'
            if len(list(filter(None, exercise['solutions'][part_num].split('\n')))) == 1 and '\\rightarrow' in exercise['solutions'][part_num]:
                numeric_answer = 1
                answer_section: str = exercise['solutions'][part_num].split('\\rightarrow')[-1].strip()
                while not answer_section[-1].isdigit():
                    answer_section = answer_section[:-1]
                while not answer_section[0].isdigit() and not answer_section[0] == '-':
                    answer_section = answer_section[1:]
                numeric_answer = (float(answer_section.strip()))
                split = exercise['solutions'][part_num].split('\\rightarrow')
                split[-1] = split[-1].replace(answer_section, f'{{{{ correct_answers.part{part_num+1}_ans }}}}')
                exercise['solutions'][part_num] = '\\rightarrow'.join(split)
            if len(words) > 0 and string_is_numeric(words[-1].replace(',', '').strip()):
                numeric_answer = float(words[-1].replace(',', '').strip())
                exercise['solutions'][part_num] = exercise['solutions'][part_num].replace(words[-1], f'{{{{ correct_answers.part{part_num+1}_ans }}}}')
            lines.append(f"# Part {part_num+1} is a {part['info']['type']} question.")
            end_note = '' if numeric_answer is not None else '# TODO: insert correct answer here'
            decimals = count_decimal_places(numeric_answer) if numeric_answer is not None else 2
            lines.append(f"correct_part{part_num+1}_ans = {numeric_answer or 0}  {end_note}")
            lines.append(f"data2['correct_answers']['part{part_num+1}_ans'] = pbh.roundp(correct_part{part_num+1}_ans, decimals={decimals})")
            lines.append('')

    lines += ["# Update the data object with a new dict", "data.update(data2)"]
    return apply_indent(lines, indent), used_by
        # data2["params"]["part1"]["ans1"]["value"] = pbh.roundp(42)
        # data2["params"]["part1"]["ans1"]["correct"] = False
        # data2["params"]["part1"]["ans1"]["feedback"] = "This is a random number, you probably selected this choice by mistake! Try again please!"



def write_md(exercise):
    solutions = exercise['solutions']
    chapter = exercise['chapter']

    dir_end ='/' + ''.join(exercise['path'].split('.')[:-1])
    dir_path = WRITE_PATH + dir_end
    path = dir_path + '/' + exercise['path']
    title_path = INFO_PATH + dir_end + '/title.txt'
    if not os.path.exists('questions'):
        os.mkdir('questions')
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    shutil.copyfile('q11_multi-part.md', path)

    replace_file_line(path, 1, f"title: {exercise['title']}")
    replace_file_line(path, 2, f"topic: {topics[chapter]}")
    replace_file_line(path, 3, f"author: {MY_NAME}")
    replace_file_line(path, 21, f"tags:")
    replace_file_line(path, 22, f"- {MY_INITIALS}")

    df = pd.read_csv('/Users/christinayang/Documents/GitHub/OPB/learning_outcomes/outputs_csv/LO_stats.csv')
    df = df.loc[df['Topic'] == topics[chapter]]

    question_text = '\n'.join([x['question'] for x in exercise['parts']]) + '\n' + exercise['description'] + '\n' + exercise['title'] + '\n' + '\n'.join(exercise['solutions'])
    df['Similarity'] = df.apply(lambda row: text_similarity(row['Learning Outcome'], question_text), axis = 1)


    # df.sort_values(by=['Brand'], inplace=True, ascending=False)

    min_value = 1
    while len(df.index)>5:
        df = df.loc[df['Similarity'] > min_value]
        min_value += 0.5
        # df = df[df.apply(lambda row: text_similarity(row['Learning Outcome'], question_text) >= min_value, axis=1)]
    # text_similarity()
    values_to_insert = ''.join([f"- {row['Code']}  # {row['Learning Outcome']}\n" for index, row in df.iterrows()])
    insert_into_file(path, 11, values_to_insert)
    for index, row in df.iterrows():
        print("SIM:", row['Similarity'])
    # df = df.loc[text_similarity(df['Learning Outcome'], question_text) > 0.2]
    # print("\nDF HERE:")
    # print(df.to_string())

    # TODO: write expression
    lines_to_write = []
    asset_lines = ["assets:"]
    asset_to_filename = {}
    # Do all the moving here
    for i, a in enumerate(exercise['assets']):
        if a.endswith('.html'):
            asset_lines.append(f"- {a}")
            continue
        figure_name = move_figure(chapter, a, exercise['path'])
        asset_to_filename[a] = figure_name
        asset_lines.append(f"- {figure_name}")
    lines_to_write += asset_lines
    lines_to_write.append("server:\n  imports: |\n        import random\n        import pandas as pd\n        import problem_bank_helpers as pbh")
    lines_to_write.append("  generate: |")
    code_lines, params_dict = write_code(exercise)
    lines_to_write += code_lines
    lines_to_write.append("  prepare: |\n        pass\n  parse: |\n        pass\n  grade: |\n        pass")
    # lines_to_write += [
    #     "        data2 = pbh.create_data2()\n        data.update(data2)",
    #     "  prepare: |\n        pass\n  parse: |\n        pass\n  grade: |\n        pass"
    # ]
    question_part_lines = []
    for (i, e) in enumerate(exercise['parts']):
        question_lines = [f'part{i+1}:'] + format_type_info(e['info']) + get_pl_customizations(e['info'], i)
        question_part_lines += question_lines
    lines_to_write += question_part_lines
    lines_to_write += ['---', '# {{ params.vars.title }}', '', exercise['description'], '']

    # TODO: ADD ASSETS HERE, how should assets be formatted?, since parts assets + main assets
    for a in exercise['assets']:
        filename = asset_to_filename[a] if a in asset_to_filename else a
        if not filename.endswith('.jpg') and not filename.endswith('.jpeg') and not filename.endswith('.png'):
            continue
        img = f'<img src="{filename}" width=400>'
        lines_to_write.append(img)
    if len(exercise['assets']) > 0:
        lines_to_write.append('')

    has_long_text = False
    if len(exercise['parts']) != len(solutions):
        print(f"ERROR: PARTS AND SOLUTIONS LENGTHS DON'T MATCH, parts {len(exercise['parts'])}, solutions {len(solutions)}")
        print("PARTS", len(exercise['parts']), json.dumps([x['question'] for x in exercise['parts']], indent=2))
        print("SOLUTIONS", len(solutions), json.dumps(solutions, indent=2))
        # print(json.dumps(exercise, indent=2))

        print("\nPATH", path)
        print()
        # raise Exception("PARTS AND SOLUTIONS LENGTHS DON'T MATCH")
        # join until length matches
        # if len(exercise['parts']) > len(solutions):
        #     while len(exercise['parts']) > len(solutions):
        #         first = exercise['parts'][0]
        #         exercise['parts'] = exercise['parts'][1:]
        #         exercise['parts'][0]['question'] = first['question'] + ' ' + exercise['parts'][0]['question']
        #         solutions.append('')

        if len(solutions) > len(exercise['parts']):
            while len(solutions) > len(exercise['parts']):
                solutions[1] = solutions[0] + '\n' + solutions[1]
                solutions = solutions[1:]
        else:
            raise Exception("PARTS AND SOLUTIONS LENGTHS DON'T MATCH")
    for i, part in enumerate(exercise['parts']):
        lines_to_write += md_part_lines(part, i=i, params=params_dict, solution=solutions[i])
        if part['info']['type'] == 'longtext':
            has_long_text = True

    lines_to_write += ['## Rubric', '', 'This should be hidden from students until after the deadline.', '']

    print("WRITING TO", path)
    write_file(path, lines_to_write)
    with open(title_path, 'w') as f:
        f.write(exercise['title'].strip())
    if has_long_text:
        shutil.copyfile('sample.html', f'{dir_path}/sample.html')

def suggested_outcomes(exercise):
    chapter = exercise['chapter']
    df = pd.read_csv('/Users/christinayang/Documents/GitHub/OPB/learning_outcomes/outputs_csv/LO_stats.csv')
    df = df.loc[df['Topic'] == topics[chapter]]

    question_text = '\n'.join([x['question'] for x in exercise['parts']]) + '\n' + exercise['description'] + '\n' + exercise['title'] + '\n' + '\n'.join(exercise['solutions'])
    df['Similarity'] = df.apply(lambda row: text_similarity(row['Learning Outcome'], question_text), axis = 1)

    min_value = 1
    while len(df.index)>5:
        df = df.loc[df['Similarity'] > min_value]
        min_value += 0.5

    values_to_insert = ''.join([f"- {row['Code']}  # {row['Learning Outcome']}\n" for index, row in df.iterrows()])
    return values_to_insert

def write_md_new(exercise):
    solutions = exercise['solutions']
    chapter = exercise['chapter']

    dir_end ='/' + ''.join(exercise['path'].split('.')[:-1])
    dir_path = WRITE_PATH + dir_end
    path = dir_path + '/' + exercise['path']
    if not os.path.exists('questions'):
        os.mkdir('questions')
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    shutil.copyfile('q11_multi-part.md', path)

    replace_file_line(path, 1, f"title: {exercise['title']}")
    replace_file_line(path, 2, f"topic: {topics[chapter]}")
    replace_file_line(path, 3, f"author: {MY_NAME}")
    replace_file_line(path, 21, f"tags:")
    replace_file_line(path, 22, f"- {MY_INITIALS}")

    insert_into_file(path, 11, suggested_outcomes(exercise))

    # TODO: write expression
    lines_to_write = []
    asset_lines = ["assets:"]
    asset_to_filename = {}
    # Do all the moving here
    for i, a in enumerate(exercise['assets']):
        if a.endswith('.html'):
            asset_lines.append(f"- {a}")
            continue
        figure_name = move_figure(chapter, a, exercise['path'])
        asset_to_filename[a] = figure_name
        asset_lines.append(f"- {figure_name}")
    lines_to_write += asset_lines
    lines_to_write.append("server:\n  imports: |\n        import random\n        import pandas as pd\n        import problem_bank_helpers as pbh")
    lines_to_write.append("  generate: |")
    code_lines, params_dict = write_code(exercise)
    lines_to_write += code_lines
    lines_to_write.append("  prepare: |\n        pass\n  parse: |\n        pass\n  grade: |\n        pass")
    # lines_to_write += [
    #     "        data2 = pbh.create_data2()\n        data.update(data2)",
    #     "  prepare: |\n        pass\n  parse: |\n        pass\n  grade: |\n        pass"
    # ]
    question_part_lines = []
    for (i, e) in enumerate(exercise['parts']):
        question_lines = [f'part{i+1}:'] + format_type_info(e['info']) + get_pl_customizations(e['info'], i)
        question_part_lines += question_lines
    lines_to_write += question_part_lines
    lines_to_write += ['---', '# {{ params.vars.title }}', '', exercise['description'], '']

    # TODO: ADD ASSETS HERE, how should assets be formatted?, since parts assets + main assets
    for a in exercise['assets']:
        filename = asset_to_filename[a] if a in asset_to_filename else a
        if not filename.endswith('.jpg') and not filename.endswith('.jpeg') and not filename.endswith('.png'):
            continue
        img = f'<img src="{filename}" width=400>'
        lines_to_write.append(img)
    if len(exercise['assets']) > 0:
        lines_to_write.append('')

    has_long_text = False
    if len(exercise['parts']) != len(solutions):
        print(f"ERROR: PARTS AND SOLUTIONS LENGTHS DON'T MATCH, parts {len(exercise['parts'])}, solutions {len(solutions)}")
        print("PARTS", len(exercise['parts']), json.dumps([x['question'] for x in exercise['parts']], indent=2))
        print("SOLUTIONS", len(solutions), json.dumps(solutions, indent=2))
        # print(json.dumps(exercise, indent=2))

        print("\nPATH", path)
        print()

        if len(solutions) > len(exercise['parts']):
            while len(solutions) > len(exercise['parts']):
                solutions[1] = solutions[0] + '\n' + solutions[1]
                solutions = solutions[1:]
        else:
            raise Exception("PARTS AND SOLUTIONS LENGTHS DON'T MATCH")
    for i, part in enumerate(exercise['parts']):
        lines_to_write += md_part_lines(part, i=i, params=params_dict, solution=solutions[i])
        if part['info']['type'] == 'longtext':
            has_long_text = True

    lines_to_write += ['## Rubric', '', 'This should be hidden from students until after the deadline.', '']

    print("WRITING TO", path)
    write_file(path, lines_to_write)
    # old stuff
    # with open(title_path, 'w') as f:
    #     f.write(exercise['title'].strip())
    if has_long_text:
        shutil.copyfile('sample.html', f'{dir_path}/sample.html')
