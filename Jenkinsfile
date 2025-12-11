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
                        # create venv (idempotent)
                        python3 -m venv venv

                        venv/bin/pip install --upgrade pip
                        venv/bin/pip install -r requirements.txt

                        # pylint: non-fatal
                        venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero

                        # flake8: run but don't fail the build (report only)
                        venv/bin/flake8 app.py train.py --ignore=E501,E302 --exit-zero --output-file=flake8-report.txt

                        # black: formatting; allow it to fail non-fatally
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
                      # ensure venv exists and deps installed
                      if [ ! -d "venv" ]; then
                        python3 -m venv venv
                        venv/bin/pip install --upgrade pip
                        venv/bin/pip install -r requirements.txt
                      fi
                      # run tests (allow test failures to be visible by returning non-zero)
                      venv/bin/pytest -q
                    '''
                }
            }
        }

        stage('Trivy FS Scan') {
            steps {
                script {
                    echo 'Scanning filesystem with Trivy (if available)...'
                    sh '''
                        if command -v trivy >/dev/null 2>&1; then
                          trivy fs . --severity HIGH,CRITICAL --format json --output trivy-fs-report.json || true
                        else
                          echo "trivy not found — skipping FS scan."
                        fi
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker Image...'
                    dockerImage = docker.build("${DOCKERHUB_REPOSITORY}:latest")
                }
            }
        }

        stage('Trivy Docker Image Scan') {
            steps {
                script {
                    echo 'Scanning Docker Image with Trivy (if available)...'
                    sh '''
                        if command -v trivy >/dev/null 2>&1; then
                          trivy image ${DOCKERHUB_REPOSITORY}:latest --format table -o trivy-image-report.json || true
                        else
                          echo "trivy not found — skipping image scan."
                        fi
                    '''
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    echo 'Pushing Docker Image to DockerHub...'
                    docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {
                        dockerImage.push('latest')
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo 'Deploying to production (placeholder)...'
                    // add deployment steps here
                }
            }
        }
    }

    post {
        always {
            echo 'Archiving reports...'
            archiveArtifacts artifacts: '*report*.txt, trivy-*.json', allowEmptyArchive: true
            junit allowEmptyResults: true, testResults: 'tests/**/TEST-*.xml'
        }
    }
}
