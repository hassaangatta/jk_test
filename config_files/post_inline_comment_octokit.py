import os
import re
from dotenv import load_dotenv
from github import Github
from openai import Client
from octokit import Octokit

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")

client = Client(api_key=openai_key)
g = Github(github_token)

repo_name = 'hassaangatta/jk_test'
pr_number = int(os.getenv('PR_NUMBER'))
commit_sha = os.getenv('GITHUB_PR_HEAD_SHA')


octokit = Octokit(auth='token', token = github_token)


def generate_ai_comments(diff_file):
    with open(diff_file, 'r') as f:
        diff_content = f.read()

    prompt = f"""
    You are reviewing code changes in a GitHub pull request. For each line added (marked with '+') or removed (marked with '-'), 
    provide a detailed comment about what the code does and any potential improvements or issues. 

    Here is the git diff file:
    {diff_content}

    Your response should strictly follow this format for each change:
    LINE NUMBER (relative to the file): COMMENT

    Example:
    + 12: This function adds two numbers and returns the result. Consider error handling.
    - 15: This line removes error handling for null values, which may cause issues.
    """

    response = client.chat.completions.create(
        model='gpt-3.5-turbo-16k',
        messages=[{"role": "assistant", "content": [{"type": "text", "text": prompt}]}],
        max_tokens=3000,
        temperature=0.1,
        top_p=1.0
    )

    return response.choices[0].message.content


def post_inline_comments(diff_file, ai_comments):
    with open(diff_file, 'r', encoding="utf-16-le") as f:
        diff_content = f.read()

    comments = ai_comments.split('\n')

    # Extract file path and hunks from git diff
    file_hunks = re.findall(r'@@ (.*) @@', diff_content)
    file_path = re.search(r'\+\+\+ b/(.+)', diff_content).group(1)

    for comment in comments:
        if comment.strip():
            try:
                line_info, ai_comment = comment.split(':', 1)
                line_number = int(line_info.strip().lstrip("+-"))

                # Match the corresponding hunk for the comment
                matching_hunk = next((hunk for hunk in file_hunks if str(line_number) in hunk), None)
                if not matching_hunk:
                    print(f"No matching hunk found for line {line_number}, skipping comment.")
                    continue

                # Post inline comment using Octokit
                octokit.pulls.create_review_comment(
                    owner="RayyanMinhaj",
                    repo="jenkins-demo",
                    pull_number=pr_number,
                    commit_id=commit_sha,
                    body=ai_comment.strip(),
                    path=file_path,
                    line=line_number,
                    side="RIGHT" if "+" in line_info else "LEFT",
                    start_line=None,  # Assuming no multi-line hunks
                    diff_hunk=matching_hunk  # Send the matching hunk
                )

            except Exception as e:
                print(f"Error posting comment: {e}")

if __name__ == "__main__":
    import sys
    diff_file = sys.argv[1]

    ai_comments = generate_ai_comments(diff_file)
    print(ai_comments)

    post_inline_comments(diff_file, ai_comments)