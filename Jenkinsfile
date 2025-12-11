pipeline {
    agent any

    environment {
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

        stage('Train Model') {
            steps {
                script {
                    echo 'Training model in CI workspace...'
                    sh '''
                      if [ ! -d "venv" ]; then
                        python3 -m venv venv
                        venv/bin/pip install --upgrade pip
                        venv/bin/pip install -r requirements.txt
                      fi
                      venv/bin/python train.py
                    '''
                }
            }
            post {
                success {
                    archiveArtifacts artifacts: 'model/iris_model.pkl', fingerprint: true
                }
            }
        }

        stage('Lint Code') {
            steps {
                script {
                    echo 'Linting Python Code...'
                    sh '''
                        # venv idempotent
                        python3 -m venv venv || true
                        venv/bin/pip install --upgrade pip
                        venv/bin/pip install -r requirements.txt

                        venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero
                        venv/bin/flake8 app.py train.py --ignore=E501,E302 --exit-zero --output-file=flake8-report.txt
                        venv/bin/black app.py train.py || true
                    '''
                }
            }
        }

        stage('Test Code') {
            steps {
                script {
                    echo 'Testing Python Code (generating junit xml)...'
                    sh '''
                      if [ ! -d "venv" ]; then
                        python3 -m venv venv
                        venv/bin/pip install --upgrade pip
                        venv/bin/pip install -r requirements.txt
                      fi
                      # create tests output dir
                      mkdir -p tests
                      # run pytest and write JUnit XML for Jenkins
                      venv/bin/pytest -q --junitxml=tests/junit-results.xml
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
                    // build a uniquely tagged image and also tag latest
                    env.IMAGE_TAG = "${DOCKERHUB_REPOSITORY}:${env.BUILD_ID}"
                    echo "Building image ${env.IMAGE_TAG} ..."
                    // build with docker CLI (requires docker on agent)
                    sh "docker build -t ${env.IMAGE_TAG} -t ${DOCKERHUB_REPOSITORY}:latest ."
                    // store a text file with the image tag for records
                    sh "echo ${env.IMAGE_TAG} > image-tag.txt"
                    archiveArtifacts artifacts: 'image-tag.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Trivy Docker Image Scan') {
            steps {
                script {
                    echo 'Scanning Docker Image with Trivy (if available)...'
                    sh '''
                        if command -v trivy >/dev/null 2>&1; then
                          trivy image ${IMAGE_TAG} --format table -o trivy-image-report.json || true
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
                    docker.withRegistry('', "${DOCKERHUB_CREDENTIAL_ID}") {
                        // use docker CLI to push the specific tag(s)
                        sh "docker push ${IMAGE_TAG}"
                        sh "docker push ${DOCKERHUB_REPOSITORY}:latest"
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo 'Deploying to production (placeholder)...'
                    // Add deployment logic here (kubectl/helm). Use a kubeconfig file credential if needed.
                }
            }
        }
    }

    post {
        always {
            echo 'Archiving reports and publishing test results...'
            archiveArtifacts artifacts: '*report*.txt, trivy-*.json,image-tag.txt', allowEmptyArchive: true
            junit allowEmptyResults: true, testResults: 'tests/junit-results.xml'
        }
        success {
            echo "Pipeline finished successfully. Image pushed: ${env.IMAGE_TAG}"
        }
        failure {
            echo "Pipeline failed — check console logs for details."
        }
    }
}
