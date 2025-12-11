pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
        DOCKERHUB_REGISTRY = 'https://registry.hub.docker.com'
        DOCKERHUB_REPOSITORY = 'pep34/mlops-proj-01'
    }

    stages {

        /* -------------------------------
           CLONE REPO
        --------------------------------*/
        stage('Clone Repository') {
            steps {
                script {
                    echo 'Cloning GitHub Repository...'
                    checkout scmGit(
                        branches: [[name: '*/main']],
                        userRemoteConfigs: [[
                            credentialsId: 'mlops-git-token',
                            url: 'https://github.com/nwasr/MLOps.git'
                        ]]
                    )
                }
            }
        }

        /* -------------------------------
           LINT
        --------------------------------*/
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

        /* -------------------------------
           TEST
        --------------------------------*/
        stage('Test Code') {
            steps {
                script {
                    echo 'Running Unit Tests...' 
                    sh "venv/bin/pytest tests/"
                }
            }
        }

        /* -------------------------------
           TRIVY FS SCAN
        --------------------------------*/
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

        /* -------------------------------
           BUILD DOCKER
        --------------------------------*/
        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker Image...'

                    env.GIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
                    env.FULL_IMAGE = "${DOCKERHUB_REPOSITORY}:${IMAGE_TAG}"

                    dockerImage = docker.build(env.FULL_IMAGE)
                }
            }
        }

        /* -------------------------------
           TRIVY IMAGE SCAN
        --------------------------------*/
        stage('Trivy Docker Image Scan') {
            steps {
                script {
                    echo 'Scanning Docker Image with Trivy...'
                    sh "trivy image ${env.FULL_IMAGE} --format table -o trivy-image-report.json"
                }
            }
        }

        /* -------------------------------
           PUSH TO DOCKER HUB
        --------------------------------*/
        stage('Push Docker Image') {
            steps {
                script {
                    echo "Pushing Docker Image to DockerHub..."

                    docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {
                        dockerImage.push()
                        sh "docker tag ${env.FULL_IMAGE} ${DOCKERHUB_REPOSITORY}:latest"
                        dockerImage.push('latest')
                    }
                }
            }
        }

        /* -------------------------------
           DEPLOY TO K8S
        --------------------------------*/
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying to Kubernetes..."

                    withCredentials([file(credentialsId: 'mlops-kubeconfig', variable: 'KUBECONFIG_FILE')]) {

                        sh '''
                            echo "Preparing kubeconfig..."

                            # create local kube directory INSIDE WORKSPACE (always writable)
                            mkdir -p .kube
                            cp "$KUBECONFIG_FILE" .kube/config
                            export KUBECONFIG=$PWD/.kube/config

                            echo "Testing cluster access:"
                            kubectl get nodes

                            # Copy manifests
                            cp -r k8s k8s-deploy

                            # Replace placeholder with actual image tag
                            sed -i "s|IMAGE_REPLACE|pep34/mlops-proj-01:${IMAGE_TAG}|g" k8s-deploy/deployment.yaml

                            echo "Applying Kubernetes manifests..."
                            kubectl apply -f k8s-deploy/ --recursive

                            echo "Waiting for rollout..."
                            kubectl rollout status deployment/mlops-app -n mlops --timeout=120s
                        '''
                    }
                }
            }
        }

    }

    /* -------------------------------
       POST BUILD
    --------------------------------*/
    post {
        always {
            echo 'Archiving reports...'
            archiveArtifacts artifacts: '*report*.txt, trivy-*.json', allowEmptyArchive: true
        }
    }
}
