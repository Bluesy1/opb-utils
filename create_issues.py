# requires functions in issues-to-questions.py
from github import Github
import os
from constants import textbook_chapter_to_name, github_profiles, openstax_question_counts
import time
from dotenv import load_dotenv
load_dotenv()

# region settings
TEXTBOOK_PATH = os.environ.get("TEXTBOOK_PATH")
# WRITE_PATH = os.environ.get("WRITE_PATH")
GITHUB_ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN")

WRITE_PATH = './questions'

def write_to_github(all_issues, body):
    """
    {
        "issue_title": "openstax_Q1.1",
        "assignee": "github_username",
    }
    # questions = [{"question_number": i, 'issue_title': f'openstat_Q{chapter}.{i}'} for i in range(1, total_exercises+1,2)]
    """
    g = Github(GITHUB_ACCESS_TOKEN)

    # user = g.get_user()
    # print(user) # will print 'AuthenticatedUser(login=None)'
    # login = user.login
    # print(login)

    # [print(repo) for repo in g.get_repos()]
    repo = g.get_repo("open-resources/instructor_stats_bank")
    for i, issue in enumerate(all_issues[5:20]):
        # 20:33
        try:
            print('issue', issue)
            if "assignee" in issue and issue["assignee"] is not None:
                repo.create_issue(title=issue["issue_title"], body=body, assignee=issue["assignee"])
            else:
                repo.create_issue(title=issue["issue_title"], body=body)
            time.sleep(5)
        except Exception as e:
            print("Q", i)
            print('Error creating issue', issue)
            print(e)
            continue

def create_issues_open_stats():
    # ch7issues = read_all_chapter("7", github_profiles[0:3])
    # ch8issues = read_all_chapter("8", github_profiles[3:])
    # all_issues = ch7issues + ch8issues
    all_issues = []
    body = "This question can be found in the GitHub repo for the OpenIntro Stats textbook. For example, here is a link to one sample chapter: https://github.com/OpenIntroStat/openintro-statistics/blob/master/ch_distributions/TeX/ch_distributions.tex"

    write_to_github(all_issues, body)
    return
    # read_chapter("7", [{"question_number": i, 'issue_title': 'TODO'} for i in range(1,10,2)])

def create_issues_openstax(start_chapter=1, end_chapter=None):
# questions = [{"question_number": i, 'issue_title': f'openstat_Q{chapter}.{i}'} for i in range(1, total_exercises+1,2)]
    if end_chapter is None:
        end_chapter = len(openstax_question_counts)
    chapters = range(start_chapter, end_chapter+1)
    body = "This question can be found in the OpenStax textbook. For example, here is a link to one sample chapter: https://openstax.org/books/statistics/pages/1-practice"

    total_questions = sum(openstax_question_counts[(start_chapter-1):(end_chapter-1)])
    questions_per_person = 10
    # total_questions // (len(github_profiles) + 1)
    print('questions_per_person:', questions_per_person)

    all_issues = []
    for chap in chapters:
        q_count = openstax_question_counts[chap-1]
        q_before = sum(openstax_question_counts[(start_chapter-1):chap-1])
        issues = [{
            "question_number": i,
            'issue_title': f'openstax_C{chap}_Q{i}',
            "assignee": github_profiles[(q_before+i-1) // (questions_per_person * 2)] if (q_before+i-1) // questions_per_person < len(github_profiles) else None,
        } for i in range(1, q_count+1, 2)]
        all_issues += issues
    print('all_issues:', all_issues)
    write_to_github(all_issues, body)

if __name__ == "__main__":
    print('hi')

    # with open('issues.txt', 'w') as f:
    #     f.write('')

    create_issues_openstax(1, 1)

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