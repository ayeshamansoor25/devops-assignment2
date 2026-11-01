pipeline {
    agent any

    triggers {
        githubPush()   // run on every push to GitHub (via webhook)
    }

    environment {
        COMPOSE_FILE_P2  = 'docker-compose.jenkins.yml'
        INSTRUCTOR_EMAIL = 'qasimalik@gmail.com'
    }

    stages {
        stage('Fetch Code') {
            steps {
                // Code is fetched from GitHub by the Git plugin (checkout scm)
                sh 'git log -1 --pretty=format:"Commit %h by %an <%ae>: %s"'
            }
        }

        stage('Build in Docker') {
            steps {
                script {
                    // Docker Pipeline plugin: run the build check inside a Python container
                    docker.image('python:3.11-slim').inside {
                        sh 'python --version'
                        sh 'python -c "import ast; ast.parse(open(\'app.py\').read()); print(\'app.py syntax OK\')"'
                    }
                }
            }
        }

        stage('Deploy with Docker Compose') {
            steps {
                sh 'docker compose -f $COMPOSE_FILE_P2 config -q'
                sh 'docker compose -f $COMPOSE_FILE_P2 down || true'
                sh 'docker compose -f $COMPOSE_FILE_P2 up -d'
                sh 'docker compose -f $COMPOSE_FILE_P2 ps'
            }
        }

        stage('Health Check') {
            steps {
                // wait (max ~2.5 min) until the app answers and the database is connected
                sh 'for i in $(seq 1 30); do if curl -fs http://localhost:8001/health; then echo; echo "App is UP"; exit 0; fi; sleep 5; done; echo "App did not become healthy"; docker logs part2-web; exit 1'
            }
        }
    }

    post {
        always {
            script {
                def author = sh(script: 'git log -1 --pretty=format:%ae 2>/dev/null || true', returnStdout: true).trim()
                def recipient = (author && !author.contains('noreply')) ? author : env.INSTRUCTOR_EMAIL
                def ip = sh(script: 'curl -s --max-time 5 https://checkip.amazonaws.com || echo SERVER-IP', returnStdout: true).trim()
                def status = currentBuild.currentResult

                // Build the email (HTML) and send it through Gmail SMTP with curl.
                // Gmail login is stored on the server in /var/lib/jenkins/.gmail (not in GitHub).
                writeFile file: '.build-email.txt', text: """From: Jenkins <ayeshamansoor2005@gmail.com>
To: ${recipient}
Cc: ayeshamansoor2005@gmail.com
Subject: Jenkins Build ${status}: ${env.JOB_NAME} #${env.BUILD_NUMBER}
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8

<html><body>
<h2>Build ${status}</h2>
<p><b>Job:</b> ${env.JOB_NAME} #${env.BUILD_NUMBER}</p>
<p><b>Pushed by:</b> ${author}</p>
<p><b>Duration:</b> ${currentBuild.durationString}</p>
<p><b>Build details:</b> <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
<p><b>Console log:</b> <a href="${env.BUILD_URL}console">${env.BUILD_URL}console</a></p>
<p><b>Application:</b> <a href="http://${ip}:8001">http://${ip}:8001</a></p>
</body></html>
"""
                sh """curl -s --url 'smtps://smtp.gmail.com:465' --user "\$(cat /var/lib/jenkins/.gmail)" \\
                      --mail-from 'ayeshamansoor2005@gmail.com' \\
                      --mail-rcpt '${recipient}' --mail-rcpt 'ayeshamansoor2005@gmail.com' \\
                      --upload-file .build-email.txt \\
                      && echo 'Email sent to ${recipient}' || echo 'Email could not be sent'
                      rm -f .build-email.txt"""
            }
        }
    }
}
