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

                emailext(
                    to: recipient,
                    recipientProviders: [developers()],
                    subject: "Jenkins Build ${currentBuild.currentResult}: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                    mimeType: 'text/html',
                    attachLog: true,
                    body: """<h2>Build ${currentBuild.currentResult}</h2>
                             <p><b>Job:</b> ${env.JOB_NAME} #${env.BUILD_NUMBER}</p>
                             <p><b>Pushed by:</b> ${author}</p>
                             <p><b>Duration:</b> ${currentBuild.durationString}</p>
                             <p><b>Build details:</b> <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                             <p><b>Application:</b> <a href="http://${ip}:8001">http://${ip}:8001</a></p>
                             <p>The full console log is attached.</p>"""
                )
            }
        }
    }
}
