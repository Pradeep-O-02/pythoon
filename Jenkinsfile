pipeline {
  agent any

  environment {
    OLLAMA_URL = 'http://localhost:11434'
  }

  stages {
    stage('fetch code') {
      steps {
        checkout scm
        sh 'git fetch origin master:refs/remotes/origin/master'
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

            // Extract only changed function definitions using git diff chunks
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


            sh """
              gh pr comment ${env.CHANGE_ID} \
              --body-file gh_comment.md \
              --repo Pradeep-O-02/pythoon \
              --auth "\$GITHUB_TOKEN"
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



