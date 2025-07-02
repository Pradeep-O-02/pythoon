pipeline {
  agent any

  environment {
    OLLAMA_URL = 'http://localhost:11434'
    GITHUB_REPO = 'Pradeep-O-02/pythoon'
	GITHUB_TOKEN = credentials('githubpass')
  }

  stages {
    stage('fetch code') {
      steps {
        checkout scm
        // Ensure `origin/master` exists for git comparisons
        sh 'git fetch origin master:refs/remotes/origin/master'
      }
    }

    stage('AI Code Review') {
      when {
        expression { return env.CHANGE_ID != null } // Only run for PRs
      }
      steps {
        script {
          def base = sh(script: 'git merge-base origin/master HEAD', returnStdout: true).trim()
          def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
          def diffFiles = sh(script: "git diff --name-only ${base} HEAD", returnStdout: true).trim().split('\n')

          def beforeAfterPairs = diffFiles.collect { file ->
            def before = sh(script: "git show ${base}:${file}", returnStdout: true).trim()
            def after = sh(script: "git show HEAD:${file}", returnStdout: true).trim()
            return "**File: ${file}**\n\n--- BEFORE ---\n${before}\n\n--- AFTER ---\n${after}\n"
          }.join("\n\n")

          def prompt = """Compare the following code changes for logic errors, bugs, and best practices.
Each file shows the full content before and after the change.

${beforeAfterPairs}

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

          withEnv(["GITHUB_TOKEN=${env.GITHUB_TOKEN}"]) {
            sh """
              gh auth login --with-token <<< "${GITHUB_TOKEN}"
              gh pr comment ${env.CHANGE_ID} --body-file gh_comment.md --repo ${GITHUB_REPO}
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


