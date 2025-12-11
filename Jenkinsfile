pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REGISTRY      = 'https://registry.hub.docker.com'
    DOCKERHUB_REPOSITORY    = 'pep34/mlops-proj-01'
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
            python3 -m venv venv
            venv/bin/pip install --upgrade pip
            venv/bin/pip install -r requirements.txt

            venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero
            venv/bin/flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt
            venv/bin/black app.py train.py || true
          '''
        }
      }
    }

    stage('Test Code') {
      steps {
        script {
          echo 'Testing Python Code...'
          sh "venv/bin/pytest tests/ || true"
        }
      }
    }

    stage('Trivy FS Scan') {
      steps {
        script {
          echo 'Scanning filesystem with Trivy...'
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
          // use env.* to reference declarative environment variables
          def imageName = "${env.DOCKERHUB_REPOSITORY}:latest"
          // declare local variable (avoid creating pipeline-level property)
          def builtImage = docker.build(imageName)
          // export image name for later use
          env.IMAGE_TAG = imageName
          // don't keep 'builtImage' as a pipeline property — recreate when pushing
        }
      }
    }

    stage('Trivy Docker Image Scan') {
      steps {
        script {
          echo 'Scanning Docker Image with Trivy...'
          sh '''
            if command -v trivy >/dev/null 2>&1; then
              trivy image "${IMAGE_TAG}" --format json -o trivy-image-report.json || true
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
          echo "Pushing ${env.IMAGE_TAG} to DockerHub..."
          // use env.* inside Groovy calls
          docker.withRegistry(env.DOCKERHUB_REGISTRY, env.DOCKERHUB_CREDENTIAL_ID) {
            // re-create image handle and push
            docker.image(env.IMAGE_TAG).push('latest')
            docker.image(env.IMAGE_TAG).push("${env.BUILD_NUMBER}")
          }
        }
      }
    }

    stage('Deploy') {
      steps {
        script {
          echo 'Deploying to production...'
          // placeholder; your deploy logic here
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
