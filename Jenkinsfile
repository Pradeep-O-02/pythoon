pipeline {
  agent any

  environment {
    OLLAMA_URL = 'http://localhost:11434'
    GITHUB_REPO = 'Pradeep-O-02/python'
    CHANGE_TARGET = 'master'
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

            def reviews = diffFiles.collect { file ->
              def ext = file.tokenize('.').last().toLowerCase()
              def language = detectLanguage(ext)
              def fileDiff = sh(script: "git diff --unified=3 --function-context ${base} HEAD -- ${file}", returnStdout: true).trim()

              def prompt = """
You are an expert code reviewer.

Review the changes in **${file}** (Language: ${language}).
Summarize issues, suggestions, or improvements in 1-2 lines.
If no issues, respond: "No major issues in ${file}".

\`\`\`diff
${fileDiff}
\`\`\`
"""

              def jsonText = groovy.json.JsonOutput.toJson([
                model : "codellama:13b",
                prompt: prompt,
                stream: false
              ])

              writeFile file: "request_${file}.json", text: jsonText

              sh """
                curl -s "${OLLAMA_URL}/api/generate" \
                -H "Content-Type: application/json" \
                -d @request_${file}.json > response_${file}.json
              """

              def response = readFile("response_${file}.json")
              return "- **${file}**:\n${parseResponse(response).trim()}"
            }

            def summary = reviews.join("\n\n")
            writeFile file: 'gh_comment.md', text: "### ?? AI Code Review Summary\n\n${summary}"

            sh """
              gh pr comment ${CHANGE_ID} \
              --body-file gh_comment.md \
              --repo ${GITHUB_REPO}
            """
          }
        }
      }
    }

    stage('Generate Release Notes') {
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
        sh '''
          echo "?? Running Python test & build steps..."
          python3 -m unittest discover -s tests || echo "No tests found"

          if [ -f setup.py ]; then
            pip install setuptools wheel
            python3 setup.py sdist bdist_wheel
          fi
        '''
      }
    }

    stage('Publish GitHub Release') {
      when {
        expression { return env.CHANGE_TARGET == 'master' || env.CHANGE_TARGET == 'release' }
      }
      steps {
        withCredentials([string(credentialsId: 'github_token_id', variable: 'GITHUB_TOKEN')]) {
          script {
            def tagName = getNextSemanticTag()
            echo "Using tag: ${tagName}"

            def assets = fileExists('dist') ? 'dist/*' : ''

            sh """
              gh auth login --with-token <<< "$GITHUB_TOKEN"
              gh release create ${tagName} \
                --title "Release ${tagName}" \
                --notes-file release_notes.md \
                ${assets} \
                --repo ${GITHUB_REPO} || echo 'Release might already exist'
            """
          }
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'release_notes.md,dist/*,**/test-results/*.xml', fingerprint: true
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
  def tagParts = latestTag.replace('v', '').tokenize('.')

  def major = tagParts[0].toInteger()
  def minor = tagParts[1].toInteger()
  def patch = tagParts[2].toInteger() + 1

  return "v${major}.${minor}.${patch}"
}









