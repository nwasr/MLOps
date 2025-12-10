pipeline {
    agent any

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
                    // If trivy installed on host, leave as is
                    // sh "trivy fs --exit-code 1 --severity HIGH,CRITICAL ."
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker Image...'
                    // Example:
                    // sh "docker build -t your-image:latest ."
                }
            }
        }

        stage('Trivy Docker Image Scan') {
            steps {
                script {
                    echo 'Scanning Docker Image with Trivy...'
                    // Example:
                    // sh "trivy image your-image:latest"
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    echo 'Pushing Docker Image to DockerHub...'
                    // Example:
                    // withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    //     sh "echo $PASS | docker login -u $USER --password-stdin"
                    //     sh "docker push your-image:latest"
                    // }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo 'Deploying to production...'
                }
            }
        }
    }
}
