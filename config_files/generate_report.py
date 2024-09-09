import os
from dotenv import load_dotenv
from openai import Client


load_dotenv()
key = os.getenv("OPENAI_API_KEY")


client = Client(api_key=key)

def generate_report(diff_file):
    with open(diff_file, 'r') as f:
        diff_content = f.read()


    prompt = f"""You are a PR Review bot, a lanugage model trained by OpenAI. Your purpose is to analyse a git diff file containing code changes and act like a
    very nit-picky and highly experienced software engineer and give feedback over 5 different headings (PR Title, Description, File Differences,
    Instructions, Change Hunks). The most important thing is the triage status. If applicable, your response should include a note about alterations to the signatures of exported functions, global data structures and variables, and any changes that might affect the external interface or 
    behavior of the code. Your response is going to be copy pasted into the PR comment thread hence it needs to follow correct markdown file syntax.

    IMPORTANT:
    - Do not include any explanations for the triage decision or details about potential impacts in the summary.
    - Focus solely on delivering a succinct summary and an impact assessment.
    - Please evaluate the diff thoroughly and take into account factors such as the number of lines changed, the potential impact on the overall system, and the likelihood of 
    introducing new bugs or security vulnerabilities. When in doubt, always err on the side of caution and triage the diff as `NEEDS_REVIEW`.
    - In your summary do not mention that the file needs a through review or caution about potential issues.
    - Do not provide any reasoning why you triaged the diff as `NEEDS_REVIEW` or `APPROVED`.
    - Do not mention that these changes affect the logic or functionality of the code in the summary. You must only use the triage status format above to indicate that.

    
    Here is the git diff file: {diff_content}. If there are multiple git diffs here, then you need to output different reviews for each git diff command. The report you provide to me need to strictly adhere to the following output:

    PR Title - [This section is a heading and can not be left empty]
    - This should be replaced with a catchy title, should not exceed 4-5 words.

    Description - [This section can not be left empty]
    - This should be replaced with a brief description that elaborates on the changes that have occurred. MAX 3 sentences.

    File differences - [This section is a heading and can not be left empty]
    - List down each and every change that has occurred in as much detail as possible.
    - Analyse each and every function and output what the changes do. 
    - Provide a line by line review of the given + and - lines.

    Instructions - [This section is a heading and can not be left empty]
    Please provide a comprehensive report on the changes detailed in the diff. Your report should include:

    1. **Summary of Changes**: Offer a clear and concise summary of the modifications present in the diff. Highlight the key changes, including any adjustments to function signatures, global variables, or other elements that could impact the code’s external behavior or interface. Aim to summarize these changes within 150 words.

    2. **Impact Assessment**: Evaluate the potential impact of these changes on the overall system. Consider whether the changes introduce new functionality, modify existing functionality, or affect the code's logic. Indicate whether these changes might introduce any bugs or security issues. 

    3. **Triaging**: Based on your assessment, classify the diff as NEEDS_REVIEW or APPROVED according to the following criteria:
    - **NEEDS_REVIEW**: If the diff involves modifications to code logic or functionality, including changes to control structures, function calls, or variable assignments.
    - **APPROVED**: If the diff contains only minor changes such as formatting fixes or renaming variables that do not affect the code logic.
    * If the diff involves any modifications to the logic or functionality, even if they seem minor, triage it as `NEEDS_REVIEW`. This includes changes to control structures, 
    function calls, or variable assignments that might impact the behavior of the code.
    * If the diff only contains very minor changes that don't affect the code logic, such as fixing typos, formatting, or renaming variables for clarity, triage it as `APPROVED`.

    Please provide the triage status clearly using the format below:
    [TRIAGE]: APPROVED OR NEEDS REVIEW [THIS CAN NOT BE LEFT EMPTY]

    Change Hunks - [This section is a heading can not be left empty]
    Provide ALL the + and - lines that have been changed in the code here. The lines with + in the beginning need to be highlighted in green and the lines with - need to be highlighted in red (green for added lines of code, red for removed lines of code)



    Example:

    ### Refactor hello_world.py
    This PR refactors the hello_world.py file by making changes to the sum_func and div_func functions. The sum_func function now assigns the sum of a and b to a new variable c before returning it. The div_func function has been removed entirely.

    ### File Differences 
    - The sum_func function has been modified to assign the sum of a and b to a new variable c before returning it.
    - The div_func function has been removed entirely.


    ### Changes (Hunks)
    ---new_hunk---
    + function add(x, y) 
    +   return x + y;
    + 
    ---old_hunk---
    - function add(x, y) 
    -   return x + y;
    - 

    ### Example Summary

    - **Summary**: Added a new `add` function that returns the sum of two numbers.
    - **Impact**: This addition introduces new functionality that was previously missing. No existing functionality was altered.

    [TRIAGE]: APPROVED"""
    
    
    response = client.chat.completions.create(
        model='gpt-3.5-turbo-16k',
        messages=[{"role": "assistant", "content": [{"type": "text", "text": prompt}]}],
        max_tokens=3000,
        temperature=0.1,
        top_p=1.0
    )
    
    
    content = response.choices[0].message.content
        
    return content

if __name__ == "__main__":
    
    import sys
    diff_file = sys.argv[1]
    report = generate_report(diff_file)
    print(report)
