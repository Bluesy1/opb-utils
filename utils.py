import re
import nltk.data

def uniq_by(list1, fn=None):
    seen_keys = set()

    if fn is None:
        fn = lambda x: x
    # initialize a null list
    unique_list = []
    # traverse for all elements
    for x in list1:
        key = fn(x)
        if key in seen_keys:
            continue
        unique_list.append(x)
        seen_keys.add(key)
    return unique_list

def apply_indent(lines, indent='        '):
    return [indent + x for x in lines]


def write_file(path, lines, mode='a'):
    lines = '\n'.join(lines).split('\n')
    while lines[-1].strip() == '':
        lines.pop()
    with open(path, mode) as f:
        f.writelines([line.rstrip()+ '\n' for line in lines])


def replace_file_line(file_name, line_num, text):
    with open(file_name, 'r') as f:
        lines = f.readlines()
    lines[line_num] = text.rstrip() + '\n'
    with open(file_name, 'w') as f:
        f.writelines(lines)


def insert_into_file(path, index, content: str):
    with open(path, "r") as f:
        contents = f.readlines()

    contents.insert(index, content)

    with open(path, "w") as f:
        contents = "".join(contents)
        f.write(contents)


def remove_unmatched_closing(string: str):
    stack = []
    for i, c in enumerate(string):
        if c == '{':
            stack.append(i)
        elif c == '}':
            if len(stack) == 0:
                return string[:i]
            stack.pop()
    return string

def find_end_tag(string: str):
    stack = []
    is_started = False
    for i, c in enumerate(string):
        if c == '{':
            is_started = True
            stack.append(i)
        elif c == '}':
            stack.pop()
        if is_started and len(stack) == 0:
            return i
    raise Exception('Does not have ending tag')


def remove_tags(string: str):
    while '\\' in string:
        index = string.index('\\')
        end_bracket_index = find_end_tag(string[index:])
        string = string[:index] + string[index+end_bracket_index+1:]
    return string

def unwrap_tags(string: str):
    while '\\' in string:
        index = string.index('\\')
        end_bracket_index = find_end_tag(string[index:])
        tag_area = string[index:index+end_bracket_index+1]
        wrapped_text = tag_area.split('{')[1].split('}')[0]
        string = string[:index] + wrapped_text + string[index+end_bracket_index+1:]
    return string

# ISSUE: might add an extra \n
def unwrap_unsupported_tags(stringV: str):
    string = stringV.replace("\\\\", "\n").replace("``", '"').replace("''", '"')
    supported_tags = [
        '\\textit{',
        '\\$', '\\mu', '\\sigma',
        '\\frac{', '\\sum_{', '\\prod_{', '\\sqrt['
        '\\ne', '\\geq', '\\leq', '\\times', '\\cdot', '\\pm', '\\%',
    ]
    # if no variables, should automatically support
    unsupported_remove_entirely_tags = ['\\footfullcite', '\\noindent', '\\renewcommand\\arraystretch']
    # unsupported, \footfullcite + \noindent, \emph, '\\raisebox'
    result = ''
    while '\\' in string:
        index = string.index('\\')
        matching_tags = [tag for tag in supported_tags if string[index:].startswith(tag)]

        first_section = string[index:].strip().split(' ')[0].strip()
        do_not_wrap = False
        if len(matching_tags) > 0 or not '{' in first_section:
            if not '{' in first_section:
                end_tag_index = index + len(first_section)-1
                do_not_wrap = True
            else:
            # if '{' not in first_section:
            #     end_tag_index = len(first_section)-1
            # else:
                end_tag_index = find_end_tag(string[index:])+index if matching_tags[0].endswith("{") else index + (string[index:].index(' ') - 1 if ' ' in string[index:] else len(matching_tags[0])-1)
            # index + len(matching_tags[0])-1
            result += string[:index]

            cur_line = string[index:end_tag_index+1]
            if do_not_wrap or '$' in cur_line or (index > 0 and string[index-1] == '$'):
                result += f'{cur_line}'
            else:
                result += f'${cur_line}$'
            string = string[end_tag_index+1:]
            continue
        if '{' not in string[index+1:].split(' ')[0].split('}')[0]:
            end_bracket_index = index + len(string[index+1:].split(' ')[0])
            string = string[:index] + string[end_bracket_index+1:]
            continue
        end_bracket_index = find_end_tag(string[index:]) + index
        tag_area = string[index:end_bracket_index+1]
        if end_bracket_index+1 < len(string) and string[end_bracket_index+1] == '[':
            end_bracket_index = find_end_tag(string[end_bracket_index+1:]) + end_bracket_index
            tag_area = string[index:end_bracket_index+1]
        wrapped_text = ''
        if not any([tag_area.startswith(tag) for tag in unsupported_remove_entirely_tags]):
            wrapped_text = tag_area.split('{')[-1].split('}')[0]
        # print('tag_area:', tag_area)
        # print('wrapped_text:', wrapped_text)
        string = string[:index] + wrapped_text + string[end_bracket_index + 2:]
    return result + string


def get_between_tag(string: str, tag: str):
    index = string.index(tag)
    end_bracket_index = find_end_tag(string[index:]) + index
    also_add = 1 if string[index + len(tag)] == '{' else 0
    return string[index+len(tag)+also_add:end_bracket_index]


def get_between_strings(text: str, start_target: str, end_target: str | list[str]):
    start = text.index(start_target)
    text = text[start + len(start_target):]

    if isinstance(end_target, str):
        end_target = [end_target]
    end_target_index = 0
    while end_target_index < len(end_target) and end_target[end_target_index] not in text:
        end_target_index += 1
    end = text.index(end_target[end_target_index])
    text = text[:end]
    return text


def string_is_numeric(s: str):
    return s.lstrip("-").replace('.','',1).isdigit()


possible_prefixes = ['(', '[', '{', "\\$", '|']
possible_suffixes = ['.', ',', '?', '!', ':', ';', ')', ']', '}', '\\%', '%',  '|', '\\']
def numbers_to_latex_equations(paragraph: str, key: str):
    numbers = []
    # TODO: handle negative numbers

    words = paragraph.split(' ')
    for i, word in enumerate(words):
        if len(word) == 0:
            continue
        prefix = ''
        suffix = ''

        for pre in possible_prefixes + possible_prefixes:
            if word.startswith(pre):
                word = word[len(pre):]
                prefix += pre
                # break
        for suf in possible_suffixes + possible_suffixes:
            if word.endswith(suf):
                word = word[:-len(suf)]
                suffix = suf + suffix
                # break

        word = word.replace(',', '')  # ex. 1,000,000

        if string_is_numeric(word):
            numbers.append(float(word))
            words[i] = f'{prefix}${{{{ params.{key}.num{len(numbers)} }}}}${suffix}'
    return ' '.join(words), numbers


def handle_word(wordV: str, params_dict: dict):
    prefix = ''
    suffix = ''
    word = wordV
    for pre in possible_prefixes + possible_prefixes:
        if word.startswith(pre):
            word = word[len(pre):]
            prefix += pre
    for suf in possible_suffixes + possible_suffixes:
        if word.endswith(suf):
            word = word[:-len(suf)]
            suffix = suf + suffix
    word = word.replace(',', '')  # ex. 1,000,000

    for value, param_name in params_dict.items():
        if word == value or (string_is_numeric(word) and type(value) is float and float(word) == value):
            if string_is_numeric(word) and not ('$' in prefix or '$' in suffix):
                return f'{prefix}${{{{ params.{param_name.replace("_", ".")} }}}}${suffix}'
            return f'{prefix}{{{{ params.{param_name.replace("_", ".")} }}}}{suffix}'
    return wordV

# Used to apply params to solutions
def apply_params_to_str(paragraph: str, params_dict: dict):
    # TODO: handle negative numbers

    words = paragraph.split(' ')
    # re.split(' |/',paragraph)
    for i, word in enumerate(words):
        if len(word) == 0:
            continue
        # TODO: split word by '\\' too
        arr = [handle_word(w, params_dict) for w in word.split('/')]
        words[i] = '/'.join(arr)

    return ' '.join(words)


def extract_first_number(text: str):
    split = text.split(' ')
    for word in split:
        if string_is_numeric(word.replace(',', '').strip()):
            return word
    raise Exception(f'No number found in {text}')


def split_question_by_calculate(text: str):
    """TODO see if nltk can scan for 'one, two, and three'"""
    pass


def split_question_by_if(text: str):
    questions = ['']
    sentences = nltk.sent_tokenize(text)
    has_question_mark = False
    if_count = 0
    for sentence in sentences:
        if sentence.strip().endswith('?') or 'list' in sentence.lower() or 'state' in sentence.lower():
            has_question_mark = True
        if has_question_mark and 'if' in ' '.join(sentence.split(' ')[0:3]):
            if if_count > 0:
                questions.append('')
            if_count += 1
        questions[-1] += sentence + ' '
    return [q.strip() for q in questions] if len(questions) >= 2 else False

def split_question_by_question_mark(text: str):
    questions = ['']
    sentences = nltk.sent_tokenize(text)
    question_mark_count = 0
    for sentence in sentences:
        if sentence.strip() == '':
            continue
        if sentence.strip().endswith('?'):
            if question_mark_count > 0:
                questions.append('')
            question_mark_count += 1
        questions[-1] += sentence + ' '
    questions = [q.strip() for q in questions if q.strip() != '']
    return [q.strip()[0].upper() + q.strip()[1:] for q in questions] if len(questions) >= 2 else False


def split_question_by_sentence(text: str):
    phrases = ['also compute', 'also calculate']
    questions = ['']
    sentences = nltk.sent_tokenize(text)
    for sentence in sentences:
        if any([sentence.strip().lower().startswith(ph) for ph in phrases]):
            questions.append('')
        questions[-1] += sentence + ' '
    questions = [q.strip() for q in questions if q.strip() != '']
    return [q.strip()[0].upper() + q.strip()[1:] for q in questions] if len(questions) >= 2 else False


def split_question_by_and(text: str):
    calc_phrases = ['what would be', 'calculate', 'compute', 'what is', 'find', 'determine', 'what is', 'what are']
    phrases = {'expected value and standard deviation': ['expected value', 'standard deviation']}
    questions = ['']
    sentences = nltk.sent_tokenize(text)
    for sentence in sentences:
        flag = False
        for (ph, parts) in phrases.items():
            if any([(cph + ' ' + ph) in sentence.lower() or (cph + ' the ' + ph) in sentence.lower() for cph in calc_phrases]):
                flag = True
                for part in parts:
                    sentence.replace(ph, part)
                    questions.append(sentence.replace(ph, part) + ' ')
        if not flag:
            questions[-1] += sentence + ' '
    questions = [q.strip() for q in questions if q.strip() != '']
    return [q.strip()[0].upper() + q.strip()[1:] for q in questions] if len(questions) >= 2 else False


def re_lstrip(string, char="\s"):
    return re.sub(f"^{char}+", "", string)

def re_rstrip(string, char="\s"):
    return re.sub(f"{char}+$", "", string)

def re_strip(string, char="\s"):
    result = re_lstrip(string, char)
    result = re_rstrip(result, char)
    return result

def find_2nd_string(txt, str1):
    return txt.find(str1, txt.find(str1)+1)


def count_decimal_places(num: float):
    """number of digits after decimal point"""
    return str(num)[::-1].find('.')
