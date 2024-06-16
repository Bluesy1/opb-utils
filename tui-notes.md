# My notes on the TUI

## Issues with running the script:

Requirements not listed - the following packages had to be pip-installed:
- questionary
- github (PyGithub on PyPI)
- dotenv (python-dotenv on PyPI)
- pandoc
- pdf2image (pdf2image on PyPI)
- pandas
- sklearn (scikit-learn on PyPI)
- openai
- problem-bank-scripts (implicitly)

I was prompted by nltk to also install `wordnet`.

## Comments on UX:

Using the saved data still prompts for the user to input a lot of the data again, like if there's tables/images/graphs, which reduces a lot of the savings.
The prompts aren't very clear - I had to check the code to see what it was asking for in a lot of cases.

As an example, it would make more sense to ask for the question type before the correct answer - different question variants have different types of correct answers, and it would be easier to know what to input if you knew what type of question you were creating, as well as it would enable input validation, e.g, if the question is a number-input, it should only accept numerical inputs as the correct answer.

Also, when prompted to paste in a table, it would be helpful to know the expected format - its not clear that its tab delimited columns, newline delimited rows.

There's no way to cancel the running of the program - I can't use `ctrl(cmd)+c` (SIGINT), `ctrl(cmd)+z` (SIGTSTP), or even `ctrl(cmd)+\` (SIGQUIT) to cancel the program, I would have to close the terminal window.

At least on boxplots, the mean shows up twice in the list which is confusing.

Using the chapter number for the topic is confusing/wrong - the chapter number does not necessarily correspond to the topic number, and the topic is what is used in the question yaml.

You have about 61 system specific paths in your code, that don't rely on env variables. You also have an implicit reliance on problem bank scripts, but it seems you're relying on a dev/uninstalled build instead of a installed build, which may not work since it relies on a data file that it looks for using `importlib.resources.files(__package__)`, at least on the main branch.

## Initial suggestions for improvement:

- Don't rely on `checkq.py` - call into problem bank scripts directly.
- Don't try to manually write the yaml - use the a yaml library.