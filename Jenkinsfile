pipeline {
    agent any

    // environment{
    //     OPENAI_API_KEY = credentials('OPENAI_API_KEY')
    //     PYTHON_PATH = "C:\\Users\\rayyan.minhaj\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
    // }

    stages {
        stage('Prepare Environment') {
            steps {
                script {

                    powershell 'gci env:\\ | ft name,value -autosize'
                    
                    powershell '& git config --add remote.origin.fetch +refs/heads/main:refs/remotes/origin/main'
                    
                    powershell '& git fetch --no-tags'
                }
            }
        }

        stage('Generate Git Diff') {
            steps {
                script {
                    // Perform a diff for .py files and save the output with the actual changes to a text file
                    def diffOutput = powershell(returnStdout: true, script: '''
                        git diff origin/main..origin/$env:GITHUB_PR_SOURCE_BRANCH > git_diff.txt
                    ''').trim()

                    // Archive the git diff output as an artifact
                    archiveArtifacts artifacts: 'git_diff.txt', allowEmptyArchive: false
                }
            }
        }

        stage('Generate Report') {
            steps {
                script {
                    // Read the content of git_diff.txt into a variable
                    def gitDiffContent = readFile('git_diff.txt')
                    println gitDiffContent
                    // Define the API endpoint and headers
                    def apiUrl = 'https://f772ceee199cb6b0b0a8903595aa9d11.serveo.net/generate_report'
                    def headers = [
                        'Content-Type': 'text/plain',
                        // 'Authorization': "Bearer ${env.OPENAI_API_KEY}"
                    ]

                    // Make the API call
                    def response = httpRequest(
                        httpMode: 'POST',
                        url: apiUrl,
                        customHeaders: headers,
                        requestBody: 'hello',
                        validResponseCodes: '200:299'
                    )

                    // Save the API response to a file
                    writeFile file: 'PR_Report.txt', text: response.content
                }
            }
        }

        stage('Archive Reports'){
            steps{
                script{
                    archiveArtifacts artifacts: 'git_diff.txt, PR_Report.txt', allowEmptyArchive: false
                }
            }           
        }
    }
}
