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
                    sh """
                        python3 -m venv venv
                        venv/bin/pip install --upgrade pip
                        venv/bin/pip install -r requirements.txt

                        venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero
                        venv/bin/flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt
                        venv/bin/black app.py train.py
                    """
                }
            }
        }

        stage('Test Code') {
            steps {
                script {
                    echo 'Testing Python Code...'
                    sh "venv/bin/pytest tests/"
                }
            }
        }

        stage('Trivy FS Scan') {
            steps {
                script {
                    echo 'Scanning filesystem with Trivy...'
                    sh """
                        trivy fs . \
                          --severity HIGH,CRITICAL \
                          --format json \
                          --output trivy-fs-report.json
                    """
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker Image...'

                    // Create unique tag for this build
                    env.GIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
                    env.FULL_IMAGE = "${DOCKERHUB_REPOSITORY}:${IMAGE_TAG}"

                    dockerImage = docker.build(env.FULL_IMAGE)
                }
            }
        }

        stage('Trivy Docker Image Scan') {
            steps {
                // Trivy Docker Image Scan
                script {
                    echo 'Scanning Docker Image with Trivy...'
                    sh "trivy image ${DOCKERHUB_REPOSITORY}:latest --format table -o trivy-image-report.json"
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    echo "Pushing Docker Image to DockerHub..."

                    docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {

                        // Push uniquely tagged image
                        dockerImage.push()

                        // Also update latest (optional, but useful)
                        sh "docker tag ${env.FULL_IMAGE} ${DOCKERHUB_REPOSITORY}:latest"
                        dockerImage.push("latest")
                    }
                }
            }
        }


        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying to Kubernetes..."

                    withCredentials([file(credentialsId: 'mlops-kubeconfig', variable: 'KUBECONFIG_FILE')]) {

                        sh '''
                            # Prepare kubeconfig
                            mkdir -p $HOME/.kube
                            cp "$KUBECONFIG_FILE" $HOME/.kube/config

                            echo "Using kubeconfig:"
                            kubectl config view

                            # DEBUG: check cluster connectivity
                            kubectl get nodes

                            # Make a working copy of the k8s manifests
                            cp -r k8s k8s-deploy

                            # Replace the image tag in deployment manifest
                            sed -i "s|pep34/mlops-proj-01:latest|pep34/mlops-proj-01:${IMAGE_TAG}|g" k8s-deploy/deployment.yaml

                            echo "Applying manifests..."
                            kubectl apply -f k8s-deploy/

                            echo "Waiting for rollout..."
                            kubectl rollout status deployment/mlops-app -n mlops --timeout=120s
                        '''
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
