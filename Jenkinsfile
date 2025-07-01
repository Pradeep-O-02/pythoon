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
    expression { return env.CHANGE_ID != null }
  }
  steps {
    script {
      def base = sh(script: 'git merge-base origin/master HEAD', returnStdout: true).trim()
      def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
      def diffFiles = sh(script: "git diff --name-only ${base} HEAD -- '*.py'", returnStdout: true).trim().split('\n')

      def beforeAfterPairs = diffFiles.collect { file ->
        def diffLines = sh(script: "git diff ${base} HEAD -- ${file}", returnStdout: true).trim()
        
        // Extract function names from the diff
        def changedFunctions = diffLines.readLines()
          .findAll { it.startsWith('+def ') || it.startsWith('-def ') }
          .collect { it.replaceAll(/^[+-]/, '').replaceAll(/\s.*/, '') } // get only `def funcname`

        // De-duplicate function names
        changedFunctions = changedFunctions.unique()

        // For each function, extract full function block from both versions
        def functionDiffs = changedFunctions.collect { func ->
          def safeFunc = func.replaceAll(/[^\w]/, '') // sanitize for grep
          def before = sh(script: """git show ${base}:${file} | awk '/^def ${safeFunc}\\(/,/^\\$/'""", returnStdout: true).trim()
          def after  = sh(script: """git show HEAD:${file} | awk '/^def ${safeFunc}\\(/,/^\\$/'""", returnStdout: true).trim()


          return """**${file}  Function: ${func}**

--- BEFORE ---
${before}

--- AFTER ---
${after}
"""
        }
 
        return functionDiffs.join("\n\n")
      }.join("\n\n")

      def prompt = """Please review the following Python function changes for correctness, logic issues, and best practices.
Only the modified functions are included.

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


