pipeline {
  agent any

  environment {
    // set the registry explicitly so Groovy won't complain
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REGISTRY      = 'https://registry.hub.docker.com' // <- explicit
    DOCKERHUB_REPOSITORY    = 'pep34/mlops-proj-01'
    KUBECONFIG_CREDENTIAL   = 'kubeconfig-cred' // optional
  }

  stages {
    stage('Clone Repository') {
      steps { checkout scm }
    }

    stage('Build Docker Image') {
      steps {
        script {
          echo 'Building Docker Image...'
          def imageName = "${env.DOCKERHUB_REPOSITORY}:latest"
          // build and keep local reference
          def built = docker.build(imageName)
          // publish image name to env for later stages
          env.IMAGE_TAG = imageName
          // store reference in a local variable to avoid implicit field creation
          // (we won't try to use 'built' across steps; we'll re-create the reference when pushing)
        }
      }
    }

    stage('Push Docker Image') {
      steps {
        script {
          echo "Pushing ${env.IMAGE_TAG} to Docker Hub..."
          // Use env.* when referencing env vars in Groovy
          docker.withRegistry("${env.DOCKERHUB_REGISTRY}", "${env.DOCKERHUB_CREDENTIAL_ID}") {
            // create image handle and push
            docker.image(env.IMAGE_TAG).push()
            docker.image(env.IMAGE_TAG).push("${env.BUILD_NUMBER}")
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        script {
          // use kubeconfig cred if present, else assume kubectl configured
          if (fileExists("${env.WORKSPACE}/.kube/config")) {
            echo "Found kube config in workspace"
          } else {
            echo "If you need a kubeconfig from Jenkins credentials, set KUBECONFIG_CREDENTIAL and uncomment code below."
          }

          // apply manifests (either folder k8s/ or inline)
            sh "kubectl apply -f k8s/ -n mlops || kubectl apply -f k8s/"
          }

          // wait for rollout and print diagnostics
          sh '''
            kubectl rollout status deploy/mlops-app -n mlops --timeout=120s || (kubectl describe deploy mlops-app -n mlops; kubectl get pods -n mlops -o wide; exit 1)
            kubectl get pods -n mlops -o wide || true
          '''
        }
      }
    }
  }

  post {
    always {
      echo 'Pipeline finished.'
      sh 'kubectl get ns || true'
    }
  }
}
