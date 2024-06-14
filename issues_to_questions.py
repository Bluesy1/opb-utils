import bisect
import json
import random
from github import Github
import shutil
from solutions import find_solutions
import os
from table import latex_table_to_md, find_all_figures
import pandoc
from utils import remove_unmatched_closing, uniq_by, remove_tags, find_2nd_string, unwrap_unsupported_tags, get_between_strings, get_between_tag, string_is_numeric, numbers_to_latex_equations, extract_first_number, split_question_by_if, split_question_by_question_mark, split_question_by_and, split_question_by_sentence, re_rstrip
import tempfile
from constants import textbook_chapter_to_name, github_profiles
import re
from dotenv import load_dotenv
from write_md import write_md
load_dotenv()
import time

# region settings
TEXTBOOK_PATH = os.environ.get("TEXTBOOK_PATH")
# WRITE_PATH = os.environ.get("WRITE_PATH")
GITHUB_ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")

WRITE_PATH = './questions'


# endregion

# region general helpers
def str_to_filename(string: str, delimiter='_'):
    return ''.join(e for e in string.lower().replace(' ', delimiter).replace(".", delimiter) if e.isalnum() or e == delimiter)

def get_file_url(chapter: str, filename: str):
    if not filename.endswith('.tex'):
        filename += '.tex'
    return f"{TEXTBOOK_PATH}/{textbook_chapter_to_name[chapter]}/TeX/{filename}"

def read_file(path):
    with open(path, 'r') as f:
        return f.readlines()

def read_chapter_info(chapter: str):
    path = get_file_url(chapter, textbook_chapter_to_name[chapter])
    lines = read_file(path)
    title = lines[0].split('{')[-1].split('}')[0]
    inputs = []
    for i in lines:
        i = i.strip()
        if i.startswith("{\input{"):
            inputs.append(i.split('/')[-1][:-6])
    inputs.append('review_exercises')
    return {"inputs": inputs, "title": title}

def count_exercises(chapter: str, section: str):
    count = 0
    path = get_file_url(chapter, section)
    lines = read_file(path)
    for i in lines:
        i = i.strip()
        if i.startswith("\eoce{"):
            count += 1
    return count

def closing_bracket_index(str_list, opening_bracket_index = 0):
    stack = []
    for i, string in enumerate(str_list):
        for j, c in enumerate(string):
            if i == 0 and j < opening_bracket_index:
                continue
            if c == '{':
                stack.append(i)
            elif c == '}':
                stack.pop()
            if len(stack) == 0:
                return (i, j)
    return (-1, -1)


# endregion


def latex_to_markdown(latex_lines: list):
    # write_file('latex.tex', latex_lines)
    doc = pandoc.read(file='latex.tex')
    md = pandoc.write(doc, format='markdown')
    pandoc.write(doc, file='md.md')
    return md
    # pandoc.write('markdown', format='markdown')
    # write_file('latex.tex', latex)
    # doc = pandoc.Document()
    # doc.latex = latex
    # webConverted = doc.markdown

# region latex helpers

# use unwrap_unsupported_tags instead
# def handle_latex_tags_in_text(paragraph: str, key: str):
#     paragraph = paragraph.replace('\\\\', '\n')
#     supported_tags = ['\\textit']
#     tags = []

#     chunks = paragraph.split('\\')
#     res = ''
#     for i, chunk in enumerate(chunks):
#         is_supported = False
#         for supported_tag in supported_tags:
#             # ex. /textit{hello}, Bob
#             if chunk.startswith(supported_tag):
#                 chunks[i] = chunk[len(supported_tag):]
#                 tags.append(supported_tag)
#                 is_supported = True
#                 break
#         if not is_supported:
#             remove_tags


# i = re.sub(r"\d+", r"[\g<0>]", i)
# endregion

def generate_random_choices(num_choices: int):
    choices = [{"value": f"'{i}'", "correct": False, "feedback": '"This is a random number, you probably selected this choice by mistake! Try again please!"'} for i in range(num_choices)]
    # TODO: add actual choices
    correct = random.randint(0, num_choices-1)
    choices[correct]["correct"] = True
    choices[correct]["feedback"] = '"Correct!"'
    return choices

def generate_given_choices(options: list, answer: str = None):
    if answer:
        answer = answer.strip().lower()
    choices = [
        {
            "value": f'"{option}"',
            "correct": False,
            "feedback": '"Try again please!"'
        }
    for option in options]
    # TODO: add actual choices
    correct = random.randint(0, len(choices)-1)
    if answer:
        for (i, option) in enumerate(options):
            first_letter = option.strip()[0].lower()
            if answer.startswith(first_letter):
                correct = i
                break
            elif option in answer:
                correct = i
    choices[correct]["correct"] = True
    choices[correct]["feedback"] = '"Correct!"'
    return choices

def generate_yes_no_choices(answer: str = None):
    return generate_given_choices(['Yes', 'No'], answer)
    # if answer:
    #     answer = answer.strip().lower()
    # # Do I have access to solutions here?
    # choices = [
    #     {
    #         "value": '"Yes"',
    #         "correct": False,
    #         "feedback": '"Try again please!"'
    #     },{
    #         "value": '"No"',
    #         "correct": False,
    #         "feedback": '"Try again please!"'
    #     }
    # ]
    # # TODO: add actual choices
    # correct = random.randint(0, len(choices)-1)
    # if answer:
    #     if answer.startswith('y'):
    #         correct = 0
    #     elif answer.startswith('n'):
    #         correct = 1
    #     elif 'yes' in answer:
    #         correct = 0
    #     elif 'no' in answer:
    #         correct = 1
    # choices[correct]["correct"] = True
    # choices[correct]["feedback"] = '"Correct!"'
    # return choices


def generate_true_false_choices(answer: str = None):
    wrong_feedback = '"Try again please!"' #  if not answer else answer
    if answer:
        answer = answer.strip().lower()
    # Do I have access to solutions here?
    choices = [
        {
            "value": '"True"',
            "correct": False,
            "feedback": wrong_feedback
        },{
            "value": '"False"',
            "correct": False,
            "feedback": wrong_feedback
        }
    ]
    correct = random.randint(0, len(choices)-1)
    if answer:
        if answer.strip().lower().startswith('t'):
            correct = 0
        elif answer.strip().lower().startswith('f'):
            correct = 1
        elif 'true' in answer:
            correct = 0
        elif 'false' in answer:
            correct = 1
    choices[correct]["correct"] = True
    choices[correct]["feedback"] = '"Correct!"'
    return choices


# region read textbook
def guess_question_type(question: str):
    question = question.strip().lower()

    if question == '':
        return {'type': 'multiple-choice', 'choices': generate_yes_no_choices()}

    yes_no_starting_words = ['is ', 'are ', 'does ', 'do ', 'did ', 'was ', 'were ', 'has ', 'have ', 'can ', 'could ', 'would ', 'must ']
    multiple_choice_starting_words = ['which ']

    # numeric_phrases = ['what percent', 'calculate', 'how many', 'what is the probability']
    multiple_choice_phrases = [
        'what is', 'which group', 'each variable', 'what are', 'are being',
        'do you think', 'are the', 'must they be', 'are believing', 'how does',
        'which error', 'which of the following', 'which of these', 'which of the', 'which of these',
        'what population', 'what parameter', 'determine if', 'what features', 'what does', 'what do ',
        'check if ', 'would it be ', 'do these ', 'state whether', 'what shape'
    ]
    long_text_phrases = [
        'describe', 'explain', 'why', 'comment on', 'what is one other possible explanation', 'identify',
        'advantages and disadvantages', 'support your answer', 'write the', 'interpret ', 'what characteristics',
        'indicate any', 'write '
    ]
    matching_phrases = ['determine which of the following is']
    drop_down_phrases = ['determine which of']
    file_upload_phrases = ['upload', 'draw ', 'construct ']

    numeric_info_dict = {
        "what percent": {'suffix':'"%"'}, # Tried $/%$, $%$, %, /%
        'calculate': {},
        'how many': {'sigfigs': 'integer'},
        'what price': {},
        'find the expected': {},
        'compute': {},
        'estimate': {},
        'what proportion': {},
        'what fraction': {},
        'what ratio': {},
        'state the null and alternative hypothes': {},
        'how big': {},
        'how much': {},
        'how long': {},
        'how far': {},
        'how often': {},
        'how many times': {},
        'how many people': {},
        'how many students': {},
        'how small': {},
        'how large': {},
        'how tall': {},
        'how wide': {},
        'what would be the': {},
        'what is the variance': {},
        'what is the standard deviation': {},
        'what is the probability': {},
        'what is the mean': {},
        'what is the median': {},
        'what is the mode': {},
        'what is the range': {},
        'what is the interquartile range': {},
        'what is the standard error': {},
        'what is the margin of error': {},
        'what is the confidence interval': {},
        'what is the p-value': {},
        'what is the z-score': {},
        'what is the t-score': {},
        'what is the correlation': {},
        'what is the slope': {},
        'what is the intercept': {},
        'what is the coefficient': {},
        'what is the odds ratio': {},
        'what is the relative risk': {},
        'what is the expected': {},
        'what is the hazard ratio': {},
        "what's the variance": {},
        "what's the standard deviation": {},
        "what's the probability": {},
        "what's the mean": {},
        "what's the median": {},
        "what's the mode": {},
        "what's the range": {},
        "what's the interquartile range": {},
        "what's the standard error": {},
        "what's the margin of error": {},
        "what's the confidence interval": {},
        "what's the p-value": {},
        "what's the z-score": {},
        "what's the t-score": {},
        "what's the correlation": {},
        "what's the slope": {},
        "what's the intercept": {},
        "what's the coefficient": {},
        "what's the odds ratio": {},
        "what's the relative risk": {},
        "what's the hazard ratio": {},
        "what's the expected": {},
    }

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
    # ADD CUSTOM SPLITS HERE, MUST BE LOWER CASE
    multi_part_direct_match = {
        'who are the subjects in this study, and how many are included?': [
            {'type': 'longtext', 'question': 'Who are the subjects in this study?',
                'extract_solution': lambda x: ' '.join(x.strip().split(' ')[1:]),
            },
            {'type': 'number-input', 'sigfigs': 'integer', 'question': 'How many of the above subjects are included?',
                'extract_solution': extract_first_number,
            },
        ],
        'what are the variables in the study? identify each variable as numerical or categorical. if numerical, state whether the variable is discrete or continuous. if categorical, state whether the variable is ordinal.': ch1_matching_type,
        'how many numerical variables are included in the data? indicate what they are, and if they are continuous or discrete.': ch1_matching_type,
        'how many variables were recorded for each subject in the study in order to conclude these findings? state the variables and their types.': ch1_matching_type,
    }
    for (phrase, info) in multi_part_direct_match.items():
        if phrase in question:
            return info

    split_questions = split_question_by_if(question)
    if split_questions:
        question_type = guess_question_type(split_questions[0])
        return [{'question': q, 'extract_solution': lambda x: x, **question_type} for q in split_questions]
    if not split_questions:
        split_questions = split_question_by_question_mark(question)
    if not split_questions:
        split_questions = split_question_by_sentence(question)
    if not split_questions:
        split_questions = split_question_by_and(question)
    if split_questions:
        return [{'question': q, 'extract_solution': lambda x: x, **guess_question_type(q)} for q in split_questions]

    for ph in yes_no_starting_words:
        if question.strip().startswith(ph):
            return {'type': 'multiple-choice', 'choices': generate_yes_no_choices()}
    for ph in multiple_choice_starting_words:
        if question.strip().startswith(ph):
            return {'type': 'multiple-choice', 'choices': generate_random_choices(4)}
    for ph in numeric_info_dict.keys():
        if ph in question:
            return {'type': 'number-input', **numeric_info_dict[ph]}
    for ph in matching_phrases:
        if ph in question:
            return {'type': 'matching', **ch1_matching_type}
    for ph in file_upload_phrases:
        if ph in question:
            return {'type': 'file-upload'}
    for ph in drop_down_phrases:
        if ph in question:
            return {'type': 'dropdown', 'choices': generate_random_choices(4)}
    for ph in multiple_choice_phrases:
        if ph in question:
            return {'type': 'multiple-choice', 'choices': generate_random_choices(4)}
    for ph in long_text_phrases:
        if ph in question:
            return {'type': 'longtext'}
    return {'type': 'unknown'}

def create_part(question, info, title, parts, additional_assets, number_variables, solution: str):
    # TODO: PROBLEM HERE!!!
    if solution.strip().lower().startswith('true') or solution.strip().lower().startswith('false'):
        info = {'type': 'multiple-choice', 'choices': generate_true_false_choices(solution)}
    elif solution.strip().lower().startswith('yes') or solution.strip().lower().startswith('no'):
        info = {'type': 'multiple-choice', 'choices': generate_yes_no_choices(solution)}
    elif info['type'] == 'multiple-choice' or info['type'] == 'dropdown' or info['type'] == 'unknown':
        if solution.strip().lower().startswith('invalid') or solution.strip().lower().startswith('valid'):
            info = {'type': 'multiple-choice', 'choices': generate_given_choices(['Valid', 'Invalid'], solution)}
    # Added 'are being' to phrases, so problem may disappear. So remove to get problem again
    if info['type'] == 'unknown':
        info = guess_question_type(title)
        if isinstance(info, list):
            print('\nHERE')
            print(question)
            print(title)
            print(info)
            raise Exception('Problem with question type guessing')
        if info['type'] == 'unknown':
            info['type'] = 'longtext'
    # Because unknown, guessing title, which includes a latex table currently. Need to remove table from title
    num_key = f'part{len(parts)+1}'

    extracted_question, question_numbers = numbers_to_latex_equations(unwrap_unsupported_tags(question), num_key)

    parts.append({
        'question': extracted_question,
        'info': info,
    })

    if info['type'] == 'longtext':
        additional_assets.add('sample.html')
    number_variables[num_key] = question_numbers

def handle_parts(lines, starting_index, title: str, solutions):
    additional_assets = set()
    start = end = -1
    index = starting_index
    number_variables = {}

    while index < len(lines):
        line = lines[index]
        if '\\begin{parts}' in line:
            start = index
        if line.startswith('}{}') or line.startswith('% '):
            # '\\end{parts}' in line
            if start == -1:
                break
            end = index
            break
        index += 1

    parts = []
    items = []
    if start == -1:
        # PROBLEM: params. should not count
        sentences = [sentence for sentence in title.split('. ') if sentence.strip() != '']
        split_index = -1
        # for i, sent in enumerate(sentences.reverse()):
        #     if '?' in sent:
        #         split_index = len(sentences) - i
        #         break
        # if split_index == -1:
        # info = guess_question_type(title)
        items = [sentences[-1] + '.']
        # else:
        #     return [{
        #         'question': numbers_to_latex_equations('.'.join(sentences[split_index-1:])),
        #     }]
    else:
        items = ' '.join(lines[start+1:end]).split('\\item')

    items = [item.strip().replace('\\end{parts}', '') for item in items if item.strip() != '']
    # def create_part(question, info):
    #     if info['type'] == 'unknown':
    #         info = guess_question_type(title)
    #     num_key = f'part{len(parts)+1}'

    #     extracted_question, question_numbers = numbers_to_latex_equations(unwrap_unsupported_tags(question), num_key)

    #     parts.append({
    #         'question': extracted_question,
    #         'info': info,
    #     })
    #     print('info', info)
    #     if info['type'] == 'longtext':
    #         additional_assets.add('sample.html')
    #     number_variables[num_key] = question_numbers
    j = 0
    while j < len(items):
        if 'begin{subparts}' in items[j]:
            old_value = items.pop(j)
            # items[j] valid even after pop because \\begin{subparts} must be matched with an end
            items[j] = old_value.replace('\\begin{subparts}', '').replace('\\end{subparts}', '') + ' ' + items[j]
        else:
            items[j].replace('\\end{subparts}', '')
            j += 1
    # print('items', json.dumps(items, indent=2))

    if len(items) <= 1 and len(solutions) > 1:
        items = [items[0]] if len(items) == 1 else []
        items += ['' for _ in range(len(solutions)-len(items))]

    for x in (items):
        question = x.replace('\\\\','\n').strip()
        info = guess_question_type(question)
        solution_index = len(parts)
        if type(info) is not list and info['type'] == 'unknown':
            info = guess_question_type(title)
            # if isinstance(info, list):
            #     print('\nHERE')
            #     print(question)
            #     print(title)
            #     print(info)
            #     raise Exception('Problem with question type guessing')
            # if info['type'] == 'unknown':
            #     info['type'] = 'longtext'
        if type(info) is list:
            solutions_to_insert = []
            for item in info:
                # create_part(item['question'], item)
                create_part(item['question'], info=item, title=title, parts=parts, additional_assets=additional_assets, number_variables=number_variables, solution=solutions[solution_index])
                solutions_to_insert.append(item['extract_solution'](solutions[solution_index]))
            solutions.pop(solution_index)
            solutions[solution_index:solution_index] = solutions_to_insert
            # TODO: handle solutions
        else:
            if info['type'] == 'unknown':
                info = guess_question_type(title)
                if isinstance(info, list):
                    print('\nHERE')
                    print(question)
                    print(title)
                    print(info)
                    raise Exception('Problem with question type guessing')
                if info['type'] == 'unknown':
                    info['type'] = 'longtext'
        # num_key = f'part{len(parts)+1}'
        # extracted_question, question_numbers = numbers_to_latex_equations(unwrap_unsupported_tags(question), num_key)
            # create_part(question, info)
            create_part(question, info=info, title=title, parts=parts, additional_assets=additional_assets, number_variables=number_variables, solution=solutions[solution_index])


        # parts.append({
        #     'question': extracted_question,
        #     'info': info,
        # })
        # if info['type'] == 'longtext':
        #     additional_assets.add('sample.html')
        # number_variables[num_key] = question_numbers
    return parts, number_variables, additional_assets


def format_description(description: str, non_text_lines: list):
    non_text = '\n\n' + '\n'.join(non_text_lines) if len(non_text_lines) > 0 else ''

    extracted_question, question_numbers = numbers_to_latex_equations(unwrap_unsupported_tags(description), 'description')
    text = extracted_question + non_text
    return text, question_numbers

def get_exercises(chapter: str, section: str, questions, solutions_dict):
    path = get_file_url(chapter, section)
    lines = [x.strip() for x in read_file(path)]

    # print(path)
    # print(questions)
    exercises = []
    table_num = 0

    cur_question = 0
    for i, line in enumerate(lines):
        if cur_question >= len(questions):
            break
        question = questions[cur_question]['question_number']

        line = line.strip()
        if line.startswith("% ") and lines[i + 2].strip().startswith('\eoce{'):
            if int(line.split(' ')[-1]) != question:
                continue
            else:
                variables = {}
                solutions = [x.replace("\\\\", "").strip().lstrip('`').lstrip('\\`').rstrip("'").rstrip('"').rstrip('".').strip() for x in re.split('\([a-z]+\)~|\([a-z]+\)\\\\|\([a-z]+-i+\)~', solutions_dict[question]) if x.strip() != '']

                #region title
                title_end_index = i + 1
                closing_line = -1
                bracket_start_index = find_2nd_string(lines[i + 2], '{')
                while closing_line == -1:
                    title_end_index += 1
                    (closing_line, closing_line_index) = closing_bracket_index(lines[i+2:title_end_index+1], bracket_start_index)
                closing_line += i+2
                title_lines = lines[i+2:closing_line+1]
                if len(title_lines) == 1:
                    title_lines[0] = title_lines[0][bracket_start_index+1:closing_line_index]
                else:
                    title_lines[0] = title_lines[0][bracket_start_index+1:]
                    title_lines[-1] = title_lines[-1][:closing_line_index]
                title = ' '.join(title_lines)
                title = remove_tags(title)
                #endregion

                #region description
                target = '\\begin{parts'
                description_end_index = closing_line
                started = False
                while description_end_index < len(lines):
                    cur_line = lines[description_end_index]
                    if description_end_index == closing_line:
                        cur_line = cur_line[closing_line_index+1:]
                    if (target in cur_line and '\\begin{align' not in cur_line and '\\begin{center' not in cur_line) or '}{}' in cur_line:
                        print('chapter', chapter, 'section', section, 'question', question)
                        break
                    if cur_line.strip() == '':
                        if started:
                            break
                    else:
                        started = True
                    description_end_index += 1
                # Look for closing bracket without opening
                description_lines = [x.strip() for x in lines[closing_line:description_end_index+1]]
                description_lines[0] = description_lines[0][closing_line_index+1:]
                description_lines[-1] = description_lines[-1].split(target)[0]
                description = ' '.join(description_lines).strip()
                description = remove_unmatched_closing(description)

                # print("END CUR DESCRIPTION", lines[description_end_index], lines[description_end_index+1])
                non_text_description_lines = []
                # print(f'i: {i}, Question: {question}')
                table = latex_table_to_md(f'table{table_num}', lines, description_end_index+1, variables=variables, phrases_signalling_end=['\\begin{parts}', '}{}'])
                figures = []
                # try:
                figures = find_all_figures(' '.join(lines[description_end_index+1:]).strip(), phrases_signalling_end=['}{}'])
                # except Exception as e:
                #     print("\nERROR FINDING FIGURES", chapter, section, question)
                #     print(e)
                if table is not None:
                    non_text_description_lines.append(table)
                    table_num += 1

                description, question_numbers = format_description(description, non_text_description_lines)
                #endregion


                # after adding parameters, description_end_index may have to be changed
                #region parts
                parts, number_variables, additional_assets = handle_parts(lines, description_end_index, description, solutions)
                number_variables['description'] = question_numbers
                #endregion
                if len(parts) == 1:
                    description = '. '.join([sentence for sentence in description.split('. ') if sentence.strip() != ''][:-1]) + '.'


                filename = str_to_filename(questions[cur_question]['issue_title'], '_')
                exercises.append({
                    "title": title,
                    "description": description,
                    "parts": parts,
                    "chapter": chapter,
                    "path": f"{filename}.md",
                    "assets": figures + list(additional_assets),
                    "issue": questions[cur_question]['issue_title'],
                    "num_variables": number_variables,
                    "variables": variables,
                    "solutions": solutions,
                })
                cur_question += 1
    if cur_question < len(questions):
        print("Looping again: CUR QUESTION", cur_question, questions[cur_question])
        print("chapter", chapter, "section", section, "questions", [question['question_number'] for question in questions], len(questions))
        raise Exception("Looping again")

    # print("CHAPTER", chapter)
    # print(json.dumps(exercises, indent=4))
    # print(len(exercises))
    return exercises

def get_chapter_counts(chapter: str):
    chapter_info = read_chapter_info(chapter)
    all_sections = chapter_info['inputs']
    exercise_counts = [count_exercises(chapter, cur_section) for cur_section in all_sections]
    summed_counts = [sum(exercise_counts[:i]) for i in range(len(exercise_counts))]
    return all_sections, exercise_counts, summed_counts

def read_all_chapter(chapter: str, people: list[str]):
    github_profiles
    chapter_info = read_chapter_info(chapter)
    all_sections = chapter_info['inputs']
    exercise_counts = [count_exercises(chapter, cur_section) for cur_section in all_sections]
    total_exercises = sum(exercise_counts)
    questions = [{"question_number": i, 'issue_title': f'openstat_Q{chapter}.{i}'} for i in range(1, total_exercises+1,2)]
    summed_counts = [sum(exercise_counts[:i]) for i in range(len(exercise_counts))]

    for j, person in enumerate(people):
        for i in range(7):
            questions[j*7+i]['assignee'] = person

    # title = chapter_info['title']
    sections = {}
    for question in questions:
        section_index = bisect.bisect_left(summed_counts, question['question_number'])
        section = all_sections[section_index-1]
        if section not in sections:
            sections[section] = []
        sections[section].append(question)

    issues_list = [x for item in list(sections.values()) for x in item]
    print("SECTIONS", json.dumps(issues_list, indent=2))
    print("NUM SECTIONS", len(sections))
    print("NUM QUESTIONS", len(questions))
    return issues_list


def read_chapter(chapter: str, questions: list): # questions is int list
    questions.sort(key=lambda x: x['question_number'])
    chapter_info = read_chapter_info(chapter)
    all_sections = chapter_info['inputs']
    exercise_counts = [count_exercises(chapter, cur_section) for cur_section in all_sections]
    summed_counts = [sum(exercise_counts[:i]) for i in range(len(exercise_counts))]
    title = chapter_info['title']
    print("exercise_counts", exercise_counts)
    print("summed_counts", summed_counts)
    print("all_sections", all_sections)
    print("chapter_info", chapter_info)
    print("title", title)
    print("questions", questions)
    # return
    sections = {}
    for question in questions:
        section_index = bisect.bisect_left(summed_counts, question['question_number'])
        section = all_sections[section_index-1]
        if section not in sections:
            sections[section] = []
        sections[section].append(question)

        # print("SECTIONS", json.dumps(sections, indent=2))
    results = []
    # print(all_sections)
    # for (section, questions) in sections.items():
        # question_numbers = [x['questions'] for x in questions]
    # section_index = all_sections.index(section)
    # file_questions = [q - summed_counts[section_index] for q in questions]
    question_solutions_dict = find_solutions(title, questions)
    for (section, questions) in sections.items():
        print("SECTION", section, "count", len(questions))
        print([question['question_number'] for question in questions])
        results += get_exercises(chapter, section, questions, question_solutions_dict)

    with open('completed.txt', 'r') as reader:
        lines = reader.readlines()
        lines = [line.strip() for line in lines]
        results = [exercise for exercise in results if exercise['path'].strip() not in lines]
        # ex. exercise['path'] = '1_2_data_basics_q1_9.md'
        for line in lines:
            line.strip()
    for exercise in results:
        # if (exercise['path'] == ''):
        write_md(exercise)
        # try:
        #     write_md(exercise)
        # except Exception as e:
        #     print(f'Error writing {exercise["path"]}')
        #     print(e)
        #     continue
    # print(json.dumps(results, indent=4))
# endregion read textbook





if __name__ == "__main__":
    print('hi')

    # read_chapter("7")
    with open('issues.txt', 'w') as f:
        f.write('')
    # latex_to_markdown('')
    # Public Web Github
    g = Github(login_or_token=GITHUB_ACCESS_TOKEN)
    user = g.get_user()
    print(user) # will print 'AuthenticatedUser(login=None)'
    login = user.login
    print(login)
# g = Github(login_or_token='token_bla_bla', base_url='https://github.company.com/api/v3')


    # ch7issues = read_all_chapter("7", github_profiles[0:3])
    # ch8issues = read_all_chapter("8", github_profiles[3:])
    # all_issues = ch7issues + ch8issues
    # read_chapter("7", [{"question_number": i, 'issue_title': 'TODO'} for i in range(1,10,2)])

    # Github Enterprise with custom hostname
    # g = Github(base_url="https://{hostname}/api/v3", auth=auth)

    repo = g.get_repo("open-resources/instructor_stats_bank")
    # for i, issue in enumerate(all_issues[33:]):
    #     try:
    #         print('issue', issue)
    #         if "assignee" in issue:
    #             repo.create_issue(title=issue["issue_title"], body=body, assignee=issue["assignee"])
    #         else:
    #             repo.create_issue(title=issue["issue_title"], body=body)
    #     except Exception as e:
    #         print("Q", i)
    #         print('Error creating issue', issue)
    #         print(e)
    #         time.sleep(5)
    #         continue

    if GITHUB_USERNAME:
        issues = repo.get_issues(state="open", assignee=GITHUB_USERNAME)
    else:
        issues = repo.get_issues(state="open")
    print(issues.totalCount)

    questions_by_chapter = {}
    sections_by_chapter = {}
    for item in issues:
        if not item.title.startswith('openstat_Q'):
            continue
        if 'Q' not in item.title or '.' not in item.title:
            continue
        # print('title', item.title)
        # print('issue number', item.number)
        if item.pull_request:
            continue

        # print(item.comments)
        with open('issues.txt', 'a') as f:
            f.write(f'{item.title}={item.number}\n')


        tmp_filepath = str_to_filename(item.title, '_')
        dir_path = 'info/' + tmp_filepath
        if not os.path.exists('info'):
            os.mkdir('info')
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)


        if not GITHUB_USERNAME and len(item.assignees) > 0 and item.assignees[0].login.strip() == 'yangchristina':
            continue

        with open(f'{dir_path}/issue_number.txt', 'w') as f:
            f.write(str(item.number))
        with open(f'{dir_path}/assign.txt', 'w') as f:
            if len(item.assignees) > 0:
                f.write(','.join([a.login.strip() for a in item.assignees]))
            else:
                f.write('')

        question_info = item.title.split("Q")[-1]
        chapter, question = question_info.split('.')
        chapter = chapter.strip()
        question = int(re_rstrip(question.split(' ')[0].strip(), '\D'))
        # print('chapter', chapter, 'question', question)


        if chapter not in questions_by_chapter:
            questions_by_chapter[chapter] = []
        questions_by_chapter[chapter].append({"question_number": question, 'issue_title': item.title})


    for (chapter, questions) in questions_by_chapter.items():
        read_chapter(chapter, uniq_by(questions, lambda x: x['question_number']))





# ARCHIVE

        # if item.title.startswith('Chapter Exercises'):
        # index = item.title.find('q')
        # else:
        #     chapter = item.title.split(' ')[0].split('.')[0]
        #     split = item.title.split(' ')
        #     section_name = '_'.join(split[1:-1]).lower()
        #     section_name = str_to_filename(section_name)
        #     question = int(split[-1][1:].split('.')[-1])
        # if chapter not in sections_by_chapter:
        #     sections_by_chapter[chapter] = {}
        # if section_name not in sections_by_chapter[chapter]:
        #     sections_by_chapter[chapter][section_name] = []
        # sections_by_chapter[chapter][section_name].append({"question_number": question, 'issue_title': item.title})
    # print(sections_by_chapter)
    # print('\nquestions_by_chapter\n')
    # print(questions_by_chapter)
    # print('questions_by_chapter', len(questions_by_chapter['4']))
    # should_split_question("blue. fish? are cool, today; today is a good day.")
    # for (chapter, sections) in sections_by_chapter.items():
    #     read_chapter(chapter, sections)
    # NOT IN CORRECT ORDER from .items
