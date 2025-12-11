pipeline {
    agent any

    environment{
        DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
        DOCKERHUB_REGISTRY = 'https://registry.hub.docker.com'
        DOCKERHUB_REPOSITORY = 'pep34/mlops-proj-01'
    }

    stages {

        stage('Clone Repository') {
            steps {
                script {
                    echo 'Cloning GitHub Repository...'
                    checkout scmGit(
                        branches: [[name: '*/main']],
                        extensions: [],
                        userRemoteConfigs: [[
                            credentialsId: 'mlops-git-token',
                            url: 'https://github.com/nwasr/MLOps.git'
                        ]]
                    )
                }
            }
        }

        stage('Lint Code') {
            steps {
                script {
                    echo 'Linting Python Code...'
                    sh '''
                        set -euo pipefail
                        # create venv (idempotent)
                        if [ ! -d "venv" ]; then
                          python3 -m venv venv
                        fi
                        # use the venv pip
                        venv/bin/python -m pip install --upgrade pip setuptools wheel
                        venv/bin/pip install -r requirements.txt

                        # run linters via venv
                        venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero || true
                        venv/bin/flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt || true
                        venv/bin/black app.py train.py || true
                    '''
                }
            }
        }

        stage('Test Code') {
            steps {
                script {
                    echo 'Testing Python Code...'
                    sh '''
                      set -euo pipefail
                      # ensure venv and deps (idempotent)
                      if [ ! -d "venv" ]; then
                        python3 -m venv venv
                        venv/bin/python -m pip install --upgrade pip setuptools wheel
                        venv/bin/pip install -r requirements.txt
                      fi
                      venv/bin/pytest -q || true
                    '''
                }
            }
        }

        stage('Trivy FS Scan') {
            steps {
                script {
                    echo 'Scanning filesystem with Trivy (if installed)...'
                    sh '''
                      set -euo pipefail
                      if command -v trivy >/dev/null 2>&1; then
                        trivy fs . \
                          --severity HIGH,CRITICAL \
                          --format json \
                          --output trivy-fs-report.json || true
                      else
                        echo "trivy not found on agent; skipping FS scan."
                      fi
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker Image...'
                    // docker.build requires docker available on agent
                    dockerImage = docker.build("${DOCKERHUB_REPOSITORY}:latest")
                }
            }
        }

        stage('Trivy Docker Image Scan') {
            steps {
                script {
                    echo 'Scanning Docker Image with Trivy (if installed)...'
                    sh '''
                      set -euo pipefail
                      if command -v trivy >/dev/null 2>&1; then
                        trivy image ${DOCKERHUB_REPOSITORY}:latest --format table -o trivy-image-report.json || true
                      else
                        echo "trivy not found on agent; skipping image scan."
                      fi
                    '''
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    echo 'Pushing Docker Image to DockerHub...'
                    docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}"){
                        dockerImage.push('latest')
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo 'Deploying to production...'
                    // Keep this minimal — replace with your actual deploy steps
                }
            }
        }
    }

    post {
        always {
            echo 'Archiving reports...'
            archiveArtifacts artifacts: '*report*.txt, trivy-*.json', allowEmptyArchive: true
        }
    }
}
