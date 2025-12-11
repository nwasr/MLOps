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

        stage('Lint Code') {
            steps {
                script {
                    sh """
                        python3 -m venv venv
                        venv/bin/pip install -r requirements.txt

                        venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero
                        venv/bin/flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt
                    """
                }
            }
        }

        stage('Test Code') {
            steps {
                script {
                    sh "venv/bin/pytest tests/"
                }
            }
        }

        stage('Trivy FS Scan') {
            steps {
                script {
                    sh """
                        trivy fs . --severity HIGH,CRITICAL \
                        --format json --output trivy-fs-report.json
                    """
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    env.GIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
                    env.FULL_IMAGE = "${DOCKERHUB_REPOSITORY}:${IMAGE_TAG}"
                    dockerImage = docker.build(env.FULL_IMAGE)
                }
            }
        }

        stage('Trivy Docker Image Scan') {
            steps {
                script {
                    sh "trivy image ${FULL_IMAGE} --format table -o trivy-image-report.json"
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {
                        dockerImage.push()
                        sh "docker tag ${FULL_IMAGE} ${DOCKERHUB_REPOSITORY}:latest"
                        dockerImage.push("latest")
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'mlops-kubeconfig', variable: 'KUBECONFIG_FILE')]) {
                        sh '''
                            echo "Deploying to Kubernetes..."

                            # Use kubeconfig directly from Jenkins secret file
                            export KUBECONFIG="$KUBECONFIG_FILE"

                            echo "Cluster nodes:"
                            kubectl get nodes

                            cp -r k8s k8s-deploy

                            sed -i "s|IMAGE_REPLACE|pep34/mlops-proj-01:${IMAGE_TAG}|g" k8s-deploy/deployment.yaml

                            kubectl apply -f k8s-deploy/ --recursive

                            kubectl rollout status deployment/mlops-app -n mlops --timeout=120s
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '*report*.txt, trivy-*.json', allowEmptyArchive: true
        }
    }
}
