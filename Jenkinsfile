pipeline {
  agent any

  environment {
    OLLAMA_URL = 'http://localhost:11434'
  }

  stages {
    stage('fetch code') {
      steps {
        checkout scm
        // ? Ensure `origin/master` exists for git comparisons
        sh 'git fetch origin master:refs/remotes/origin/master'
      }
    }

    stage('AI Code Review') {
      when {
        expression { return env.CHANGE_ID != null }  // ? Only run for PRs
      }
      steps {
        script {
          def base = sh(script: 'git merge-base origin/master HEAD', returnStdout: true).trim()
          def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
          def diffFiles = sh(script: "git diff --name-only ${base} HEAD", returnStdout: true).trim().split('\n')

          def diffOutput = sh(script: "git diff ${base} HEAD", returnStdout: true).trim()

def prompt = """Review the following code changes for logic issues or bad practices.
Only comment on actual changes.

${diffOutput}

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

          echo "?? AI Code Review:\n${message}"

          emailext (
            subject: "AI Code Review for PR #${env.CHANGE_ID}",
            body: """<h2>AI Review for Pull Request</h2><pre>${message}</pre>""",
            mimeType: 'text/html',
            to: 'pradeep.o@lirisoft.com'
          )
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


