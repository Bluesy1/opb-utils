import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def ask_mc_options(options: list, answer: str, question: str, num_to_generate: int):
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
    res = eval(chat_completion.choices[0].message.content)
    # check that res is a list of strings
    assert isinstance(res, list)
    assert all(isinstance(x, str) for x in res)
    return res
