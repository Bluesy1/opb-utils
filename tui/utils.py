def apply_indent(lines, indent='        '):
    return [indent + x for x in lines]


def string_is_numeric(s: str):
    return s.lstrip("-").replace('.','',1).isdigit()


possible_prefixes = ['(', '[', '{', "\\$", '|']
possible_suffixes = ['.', ',', '?', '!', ':', ';', ')', ']', '}', '\\%', '%',  '|', '\\']

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


def count_decimal_places(num: float):
    """number of digits after decimal point"""
    return str(num)[::-1].find('.')
