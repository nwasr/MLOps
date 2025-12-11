pipeline {
  agent any
  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REGISTRY = 'https://registry.hub.docker.com'
    DOCKERHUB_REPOSITORY = 'iquantc/mlops-proj-01'
    KUBE_CONFIG_CREDENTIAL_ID = 'kubeconfig-cred-id' // Add the kubeconfig file to Jenkins credentials and set the ID here
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Lint & Test') {
      steps {
        sh "python3 -m pip install --upgrade pip"
        sh "python3 -m pip install -r requirements.txt"
        sh "pylint app.py train.py --output=pylint-report.txt --exit-zero || true"
        sh "flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt || true"
        sh "black --check . || true"
        sh "pytest -q || true"
      }
    }
    stage('Train Model') {
      steps {
        echo 'Training model inside CI workspace...'
        sh "python3 -m pip install -r requirements.txt"
        sh "python3 train.py"
        archiveArtifacts artifacts: 'model/iris_model.pkl', fingerprint: true
      }
    }
    stage('Prepare Image Context') {
      steps {
        sh "rm -rf docker_context || true"
        sh "mkdir -p docker_context/model docker_context/templates"
        sh "cp app.py requirements.txt docker_context/"
        sh "cp -r templates docker_context/templates || true"
        sh "cp model/iris_model.pkl docker_context/model/iris_model.pkl"
        sh "cp Dockerfile docker_context/"
      }
    }
    stage('Build Docker Image') {
      steps {
        dir('docker_context') {
          script {
            imageTag = "${DOCKERHUB_REPOSITORY}:${env.BUILD_ID}"
            dockerImage = docker.build(imageTag)
          }
        }
      }
    }
    stage('Scan Image (Trivy)') {
      steps {
        sh "trivy image ${imageTag} --format table -o trivy-image-report.html || true"
        archiveArtifacts artifacts: 'trivy-image-report.html'
      }
    }
    stage('Push Docker Image') {
      steps {
        script {
          docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {
            dockerImage.push()
          }
        }
      }
    }
    stage('Deploy to Kubernetes') {
      steps {
        withCredentials([file(credentialsId: env.KUBE_CONFIG_CREDENTIAL_ID, variable: 'KUBECONFIG_FILE')]) {
          sh 'mkdir -p $HOME/.kube'
          sh 'cp $KUBECONFIG_FILE $HOME/.kube/config'
          // set image and apply manifests
          sh "kubectl set image -n mlops deployment/mlops-app mlops-app=${imageTag} --record || true"
          sh "kubectl apply -f k8s/"
        }
      }
    }
  }
  post {
    always {
      archiveArtifacts artifacts: 'pylint-report.txt,flake8-report.txt,pylint-report.txt,trivy-image-report.html', allowEmptyArchive: true
      junit allowEmptyResults: true, testResults: 'tests/**/TEST-*.xml'
    }
  }
}
