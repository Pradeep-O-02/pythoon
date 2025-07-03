pipeline {
  agent any

  environment {
    OLLAMA_URL = 'http://localhost:11434'
  }

  stages {
    stage('Fetch Code') {
      steps {
        checkout scm
        // Force-fetch latest master to ensure merge-base works correctly
        sh 'git fetch origin +refs/heads/master:refs/remotes/origin/master'
      }
    }

    stage('AI Code Review') {
      when {
        expression { return env.CHANGE_ID != null } // Only for PRs
      }
      steps {
        withCredentials([string(credentialsId: 'github_token_id', variable: 'GITHUB_TOKEN')]) {
          script {
            def base = sh(script: 'git merge-base origin/master HEAD', returnStdout: true).trim()
            def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
            def diffFiles = sh(script: "git diff --name-only ${base} HEAD", returnStdout: true).trim().split('\n')

            // Debugging output
            echo "Merge base: ${base}"
            echo "Changed files: ${diffFiles.join(', ')}"

            // Extract changed function-level diffs from modified files
            def changedFuncs = diffFiles.collect { file ->
              def funcDiff = sh(
                script: "git diff ${base} HEAD -- ${file} | awk '/^@@/,/^@@/'",
                returnStdout: true
              ).trim()
              return "**File: ${file}**\n\n${funcDiff}"
            }.join("\n\n")

            def prompt = """Review the following Python function changes for logic errors, bugs, or bad practices.
Only comment on the parts that were modified.

${changedFuncs}

Commit message:
${commitMessage}
"""

            def jsonText = """{
              "model": "codellama:13b",
              "prompt": ${groovy.json.JsonOutput.toJson(prompt)},
              "stream": false
            }"""

            writeFile file: 'ollama_request.json', text: jsonText

            sh """
              curl -s \$OLLAMA_URL/api/generate \
              -H "Content-Type: application/json" \
              -d @ollama_request.json > ai_response.json
            """

            def responseText = readFile('ai_response.json')
            def message = parseResponse(responseText)

            writeFile file: 'gh_comment.md', text: "### ?? AI Code Review\n\n${message}"

            // Authenticate once using GITHUB_TOKEN
            sh """
             gh pr comment ${env.CHANGE_ID} \
             --body-file gh_comment.md \
             --repo Pradeep-O-02/pythoon
           """
          }
        }
      }
    }
  }
}

@NonCPS
String parseResponse(String jsonText) {
  def slurper = new groovy.json.JsonSlurper()
  def parsed = slurper.parseText(jsonText)
  return parsed?.response ?: parsed?.message?.content ?: 'No response from AI'
}





