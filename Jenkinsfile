pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REPOSITORY = 'pep34/mlops-proj-01'
    GIT_CREDENTIALS = 'mlops-git-token'
    KUBECONFIG_CREDENTIAL_ID = 'mlops-kubeconfig'
  }

  stages {

    stage('Clone Repository') {
      steps {
        checkout scmGit(
          branches: [[name: '*/main']],
          userRemoteConfigs: [[
            credentialsId: "${GIT_CREDENTIALS}",
            url: 'https://github.com/nwasr/MLOps.git'
          ]]
        )
      }
    }

    stage('Setup & Lint') {
      steps {
        sh '''
          python3 -m venv venv
          . venv/bin/activate
          pip install -r requirements.txt || true

          pylint app.py train.py --output=pylint-report.txt --exit-zero || true
          flake8 app.py train.py --ignore=E501 --output-file=flake8-report.txt || true
        '''
      }
    }

    stage('Unit Tests') {
      steps {
        sh '''
          . venv/bin/activate
          pytest --junitxml=tests/results.xml tests/ || true
        '''
      }
    }

    stage('Trivy FS Scan') {
      steps {
        sh '''
          trivy fs . --severity HIGH,CRITICAL --format json --output trivy-fs.json || true
        '''
      }
    }

    stage('Build Docker Image') {
      steps {
        script {
          env.GIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
          env.IMAGE_TAG = "${BUILD_NUMBER}-${env.GIT_SHORT}"
          env.FULL_IMAGE = "${DOCKERHUB_REPOSITORY}:${IMAGE_TAG}"
        }

        sh '''
          docker build -t ${FULL_IMAGE} .
        '''
      }
    }

    stage('Trivy Image Scan') {
      steps {
        sh '''
          trivy image ${FULL_IMAGE} --format json --output trivy-image.json || true
        '''
      }
    }

    stage('Push Image') {
      steps {
        script {
          docker.withRegistry('', "${DOCKERHUB_CREDENTIAL_ID}") {
            sh "docker push ${FULL_IMAGE}"
            sh "docker tag ${FULL_IMAGE} ${DOCKERHUB_REPOSITORY}:latest"
            sh "docker push ${DOCKERHUB_REPOSITORY}:latest"
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL_ID}", variable: 'KUBECONFIG_FILE')]) {
          sh '''
            export KUBECONFIG=$KUBECONFIG_FILE

            echo "Applying Kubernetes manifests from k8s/..."
            kubectl apply -f k8s/ --recursive

            echo "Forcing Deployment to use correct image..."
            kubectl set image deployment/mlops-app mlops-app=${FULL_IMAGE} -n mlops --record

            echo "Waiting for rollout..."
            kubectl rollout status deployment/mlops-app -n mlops --timeout=20s

            echo "Deployment completed."
          '''
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: '*.txt, *.json, tests/**/*.xml', allowEmptyArchive: true
      junit allowEmptyResults: true, testResults: 'tests/**/*.xml'
    }
  }
}