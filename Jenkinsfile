pipeline {
  agent any

  environment {
    OLLAMA_URL = 'http://localhost:11434'
  }

  stages {
    stage('Fetch Code') {
      steps {
        checkout scm

        // Dynamically fetch the destination branch (CHANGE_TARGET)
        sh 'echo "Fetching destination branch for merge-base..."'
        sh "git fetch origin +refs/heads/${CHANGE_TARGET}:refs/remotes/origin/${CHANGE_TARGET}"
      }
    }

    stage('AI Code Review') {
      when {
        expression { return env.CHANGE_ID != null }
      }
      steps {
        withCredentials([string(credentialsId: 'github_token_id', variable: 'GITHUB_TOKEN')]) {
          script {
            // Use merge-base between destination and current PR source
            def base = sh(script: "git merge-base origin/${CHANGE_TARGET} HEAD", returnStdout: true).trim()
            def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
            def diffFiles = sh(script: "git diff --name-only ${base} HEAD", returnStdout: true).trim().split('\n')

            echo "Source branch: ${CHANGE_BRANCH}"
            echo "Destination branch: ${CHANGE_TARGET}"
            echo "Merge base: ${base}"
            echo "Changed files: ${diffFiles.join(', ')}"

            def changedContent = diffFiles.collect { file ->
              def fileDiff = sh(
                script: "git diff ${base} HEAD -- ${file}",
                returnStdout: true
              ).trim()
              return "**File: ${file}**\n```diff\n${fileDiff}\n```"
            }.join("\n\n")

            def prompt = """You are a code reviewer. Review the following Pull Request diff for:

- Logic errors
- Linting or syntax issues
- Bad practices
- Commit message formatting

The expected commit message format is:
[TICKET_ID]: Ticket-Title
{CHANGE_DESCRIPTION}

If everything looks good, respond exactly with:
"Verified Pull Request: No Change Needed"

------------------------

Pull Request from `${CHANGE_BRANCH}` to `${CHANGE_TARGET}`

Commit Message:
${commitMessage}

Changed Code:
${changedContent}
"""

            def jsonText = groovy.json.JsonOutput.toJson([
              model : "codellama:13b",
              prompt: prompt,
              stream: false
            ])

            writeFile file: 'ollama_request.json', text: jsonText

            sh """
              curl -s "${OLLAMA_URL}/api/generate" \
              -H "Content-Type: application/json" \
              -d @ollama_request.json > ai_response.json
            """

            def responseText = readFile('ai_response.json')
            def message = parseResponse(responseText)

            writeFile file: 'gh_comment.md', text: "### ?? AI Code Review\n\n${message}"

            // Post comment to GitHub PR dynamically
            sh """
              echo "$GITHUB_TOKEN" | gh auth login --with-token
              gh pr comment ${CHANGE_ID} \
                --body-file gh_comment.md \
                --repo "$(git config --get remote.origin.url | sed -E 's|.*github.com[:/](.+)\\.git|\\1|')"
            """
          }
        }
      }
    }
  }
}

// Parse Ollama response JSON
@NonCPS
String parseResponse(String jsonText) {
  def slurper = new groovy.json.JsonSlurper()
  def parsed = slurper.parseText(jsonText)
  return parsed?.response ?: parsed?.message?.content ?: 'No response from AI model.'
}





