import ast

from openai import OpenAI


client = OpenAI()


def ask_number_code(question: str, answer: str | float | int) -> str:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""I am creating a number-input question. The question is: "{question}"
                The correct answer is "{answer}". Write me the python code to solve the question. Use variables when possible.
                Answer with only the python code.""",
            }
        ],
        model="gpt-3.5-turbo",
    )
    for choice in chat_completion.choices:
        print(choice.message.content)
    res = chat_completion.choices[0].message.content
    # check that res is a list of strings
    assert isinstance(res, str)
    return res


def ask_mc_options(options: list[str], answer: str, question: str, num_to_generate: int):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""I am creating a multiple choice question. The question is: "{question}"
                Here are the options: {options}. The correct answer is "{answer}". Generate me {num_to_generate} incorrect options.
                Answer with only a python list of strings.""",
            }
        ],
        model="gpt-3.5-turbo",
    )
    for choice in chat_completion.choices:
        print(choice.message.content)
    try:
        res = ast.literal_eval(chat_completion.choices[0].message.content)  # pyright: ignore[reportArgumentType]
    except Exception as e:
        print(e)
        res = "\n".split(chat_completion.choices[0].message.content)
    # check that res is a list of strings
    assert isinstance(res, list)
    assert all(isinstance(x, str) for x in res)
    return res
