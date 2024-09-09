import os
from github import Github
from dotenv import load_dotenv
from openai import Client
import re

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")

client = Client(api_key=openai_key)
g = Github(github_token)

repo_name = 'RayyanMinhaj/jenkins-demo'
pr_number = int(os.getenv('PR_NUMBER'))




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

    Note:
    - Line numbers should be based on the context provided by the diff hunk.
    - Provide comments for both additions (lines starting with '+') and removals (lines starting with '-').
    - If a line number does not have a corresponding comment, skip it.
    """

    response = client.chat.completions.create(
        model='gpt-3.5-turbo-16k',
        messages=[{"role": "assistant", "content": [{"type": "text", "text": prompt}]}],
        max_tokens=3000,
        temperature=0.1,
        top_p=1.0
    )



    return response.choices[0].message.content


#################### Functions Added #############################

def parse_diff_file(diff_content):
    """Parse the diff file and return a list of tuples containing hunk details."""
    hunks = []
    current_hunk = None
    hunk_content = []

    for line in diff_content.splitlines():
        if line.startswith('+++ b/'):
            file_path = line[6:].strip()
        elif line.startswith('@@'):
            if current_hunk:
                current_hunk['lines'] = hunk_content
                hunks.append(current_hunk)
            hunk_info = re.match(r'@@ -(\d+),\d+ \+(\d+),\d+ @@', line)
            if hunk_info:
                old_line = int(hunk_info.group(1))
                new_line = int(hunk_info.group(2))
                current_hunk = {
                    'new_start': new_line,
                    'lines': [],
                    'file_path': file_path,
                    'diff_hunk': line
                }
                hunk_content = []
        elif current_hunk is not None:
            hunk_content.append(line)
    
    if current_hunk:
        current_hunk['lines'] = hunk_content
        hunks.append(current_hunk)

    return hunks


def get_hunk_line_number(hunks, line_number, side):
    """Match a line number from OpenAI's response to the correct hunk line number."""
    for hunk in hunks:
        hunk_line_number = hunk['new_start']
        for line in hunk['lines']:
            if side == "RIGHT" and line.startswith('+'):
                if hunk_line_number == line_number:
                    return hunk_line_number, hunk['file_path'], hunk['diff_hunk']
                hunk_line_number += 1
            elif side == "LEFT" and line.startswith('-'):
                if hunk_line_number == line_number:
                    return hunk_line_number, hunk['file_path'], hunk['diff_hunk']
                hunk_line_number += 1
    return None, None, None

#####################################################################################



def post_inline_comments(diff_file, ai_comments):
    with open(diff_file, 'r', encoding="utf-16-le") as f:
        diff_content = f.read()

    repo = g.get_repo(repo_name)
    pull_request = repo.get_pull(pr_number)
    comments = ai_comments.split('\n')

    commit_id = os.getenv('GITHUB_PR_HEAD_SHA')
    commit = repo.get_commit(commit_id)
    

    file_path_match = re.search(r'\+\+\+ b/(.+)', diff_content) 
    file_path = file_path_match.group(1)
        


    #hunk_lines = []
    #for line in diff_content.splitlines():
    #    if line.startswith('+++ b/'):
    #        file_path = line[6:].strip()
    #    elif line.startswith('@@'):
    #        hunk_lines.append(line)
    
    hunks = parse_diff_file(diff_content)



    for comment in comments:
        if comment.strip():
            try:
                line_info, ai_comment = comment.split(':', 1)
                line_number = int(line_info.strip().lstrip("+-"))

                side = "RIGHT" if "+" in line_info else "LEFT"



                matching_line, file_path, diff_hunk = get_hunk_line_number(hunks, line_number, side)
                if not matching_line or not file_path or not diff_hunk:
                    print(f"No matching hunk found for line {line_number}, skipping comment.")
                    continue




                pull_request.create_review_comment(
                    body=ai_comment.strip(), 
                    path=file_path, 
                    commit=commit,
                    #line=line_number,
                    line=matching_line,
                    side=side,
                    start_side="RIGHT" if side == "RIGHT" else "LEFT",
                    start_line=matching_line,
                    diff_hunk=diff_hunk 
                )

                
            except Exception as e:
                print(f"Error posting comment: {e}")




if __name__ == "__main__":
    import sys
    diff_file = sys.argv[1]

    ai_comments = generate_ai_comments(diff_file)
    print(ai_comments)

    post_inline_comments(diff_file, ai_comments)
