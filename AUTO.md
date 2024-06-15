# opb-utils
 helpers for creating questions for opb stats

- issues_to_questions.py: takes issues from github repo and turns them into questions in the (temporary) /questions directory
- pl.sh: moves questions in /questions into prairelearn
- git-pr.sh: pushes questions in /questions to github (different branch + draft PR for each question)
- git-pr-1.sh: commits + makes a PR for a specified question in /questions to github

To use:
1. create .env file, and copy .env.example there, and fill in.
2. Create an empty completed.txt file.
3. Run `nltk.download('punkt')` and `nltk.download('stopwords')` and something else i've forgotten

TODOS:
- when matching supported: change ifs to match matching instead of dropdown
