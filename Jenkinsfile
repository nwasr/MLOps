pipeline {
    agent any
    stages {
        stage('Clone Repository') {
            steps {
                // Clone Repository
                script {
                    echo 'Cloning GitHub Repository...'
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'mlops-git-token', url: 'https://github.com/nwasr/MLOps.git']])
                }
            }
        }
        stage('Lint Code') {
            steps {
                // Lint code
                script {
                    echo 'Linting Python Code...'
                    //create venv
                    sh """
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    """
                    sh "pylint app.py train.py --output=pylint-report.txt --exit-zero"
                    sh "flake8 app.py train.py 
                    sh "black app.py train.py"
                }
            }
        }
        stage('Test Code') {
            steps {
                // Pytest code
                script {
                    echo 'Testing Python Code...'
                }
            }
        }
        stage('Trivy FS Scan') {
            steps {
                // Trivy Filesystem Scan
                script {
                    echo 'Scannning Filesystem with Trivy...'
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                // Build Docker Image
                script {
                    echo 'Building Docker Image...'
                }
            }
        }
        stage('Trivy Docker Image Scan') {
            steps {
                // Trivy Docker Image Scan
                script {
                    echo 'Scanning Docker Image with Trivy...'
                }
            }
        }
        stage('Push Docker Image') {
            steps {
                // Push Docker Image to DockerHub
                script {
                    echo 'Pushing Docker Image to DockerHub...'
                    
                }
            }
        }
        stage('Deploy') {
            steps {
                // Deploy Image to Amazon ECS
                script {
                    echo 'Deploying to production...'
                    }
                }
            }
        }
    }
