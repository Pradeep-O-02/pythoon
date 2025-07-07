pipeline {
  agent any

  environment {
    OLLAMA_URL = 'http://localhost:11434'
  }

  stages {
    stage('Fetch Code') {
      steps {
        checkout scm
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
            def base = sh(script: "git merge-base origin/${CHANGE_TARGET} HEAD", returnStdout: true).trim()
            def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
            def diffFiles = sh(script: "git diff --name-only ${base} HEAD", returnStdout: true).trim().split('\n')

            echo "Source branch: ${CHANGE_BRANCH}"
            echo "Destination branch: ${CHANGE_TARGET}"
            echo "Merge base: ${base}"
            echo "Changed files: ${diffFiles.join(', ')}"

            def changedContent = diffFiles.collect { file ->
              def ext = file.tokenize('.').last().toLowerCase()
              def language = detectLanguage(ext)

              def fileDiff = sh(
                script: "git diff --unified=3 --function-context ${base} HEAD -- ${file}",
                returnStdout: true
              ).trim()

              return "**File: ${file}** _(Language: ${language})_\n```diff\n${fileDiff}\n```"
            }.join("\n\n")

            def prompt = """You are an expert code reviewer.

Your task is to review the following pull request diff for:

- Logic errors
- Linting or syntax issues
- Bad practices
- Commit message formatting

Commit Message Format:
[TICKET_ID]: Ticket-Title
{CHANGE_DESCRIPTION}

If everything looks good, respond with **exactly**:
"Verified Pull Request: No Change Needed"

Pull Request: `${CHANGE_BRANCH}` ? `${CHANGE_TARGET}`

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

            echo "Final Prompt Sent to Ollama:\n${prompt}"

            writeFile file: 'ollama_request.json', text: jsonText

            sh """
              curl -s "${OLLAMA_URL}/api/generate" \
              -H "Content-Type: application/json" \
              -d @ollama_request.json > ai_response.json
            """

            def responseText = readFile('ai_response.json')
            def message = parseResponse(responseText)

            writeFile file: 'gh_comment.md', text: "### AI Code Review\n\n${message}"

            sh '''
             gh pr comment $CHANGE_ID \
             --body-file gh_comment.md \
             --repo Pradeep-O-02/pythoon
            '''
          }
        }
      }
    }

    stage('Generate Release Notes') {
      when {
        expression { return env.CHANGE_ID != null }
      }
      steps {
        script {
          def base = sh(script: "git merge-base origin/${CHANGE_TARGET} HEAD", returnStdout: true).trim()
          def releaseNotes = sh(
            script: "git log ${base}..HEAD --pretty=format:'- %s' | grep -i 'fix\\|bug' || true",
            returnStdout: true
          ).trim()

          if (!releaseNotes) {
            releaseNotes = "No bug fixes found in recent commits."
          }

          def formatted = "### Bug Fixes\n\n${releaseNotes}"
          writeFile file: 'release_notes.md', text: formatted
          echo "Release Notes:\n${formatted}"
        }
      }
    }

    stage('Build') {
      steps {
        sh './gradlew build' // or use your own build command
      }
    }

    stage('Publish GitHub Release') {
      when {
        expression { return env.CHANGE_TARGET == 'main' || env.CHANGE_TARGET == 'release' }
      }
      steps {
        withCredentials([string(credentialsId: 'github_token_id', variable: 'GITHUB_TOKEN')]) {
          script {
            def tagName = getNextSemanticTag()
            echo "Using tag: ${tagName}"

            sh """
              gh auth login --with-token <<< "$GITHUB_TOKEN"
              gh release create ${tagName} \
                --title "Release ${tagName}" \
                --notes-file release_notes.md \
                target/*.jar \
                --repo Pradeep-O-02/python
            """
          }
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'release_notes.md,target/*.jar', fingerprint: true
    }
  }
}

// ----------- Helpers -----------

@NonCPS
String parseResponse(String jsonText) {
  def slurper = new groovy.json.JsonSlurper()
  def parsed = slurper.parseText(jsonText)
  return parsed?.response ?: parsed?.message?.content ?: 'No response from AI model.'
}

@NonCPS
String detectLanguage(String ext) {
  switch(ext) {
    case 'py': return 'Python'
    case 'js': return 'JavaScript'
    case 'ts': return 'TypeScript'
    case 'java': return 'Java'
    case 'rb': return 'Ruby'
    case 'go': return 'Go'
    case 'cpp': case 'cc': case 'cxx': return 'C++'
    case 'c': return 'C'
    case 'cs': return 'C#'
    case 'kt': return 'Kotlin'
    case 'sh': return 'Shell'
    case 'yaml': case 'yml': return 'YAML'
    case 'json': return 'JSON'
    case 'html': return 'HTML'
    case 'css': return 'CSS'
    case 'php': return 'PHP'
    case 'scala': return 'Scala'
    case 'rs': return 'Rust'
    default: return 'Unknown'
  }
}

@NonCPS
String getNextSemanticTag() {
  def latestTag = sh(script: "git describe --tags --abbrev=0 || echo v0.0.0", returnStdout: true).trim()
  def (major, minor, patch) = latestTag.replace('v', '').tokenize('.').collect { it.toInteger() }
  patch += 1
  return "v${major}.${minor}.${patch}"
}







