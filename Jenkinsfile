pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REGISTRY      = 'https://registry.hub.docker.com'
    DOCKERHUB_REPOSITORY    = 'pep34/mlops-proj-01'
    KUBECONFIG_CREDENTIAL   = 'kubeconfig-cred' // optional: secret file credential id containing kubeconfig
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
          def built = docker.build(imageName)
          env.IMAGE_TAG = imageName
        }
      }
    }

    stage('Push Docker Image') {
      steps {
        script {
          echo "Pushing ${env.IMAGE_TAG} to Docker Hub..."
          docker.withRegistry("${env.DOCKERHUB_REGISTRY}", "${env.DOCKERHUB_CREDENTIAL_ID}") {
            docker.image(env.IMAGE_TAG).push()
            docker.image(env.IMAGE_TAG).push("${env.BUILD_NUMBER}")
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        script {
          // If you have a kubeconfig stored as a Jenkins "Secret file" credential,
          // set KUBECONFIG_CREDENTIAL to its id. We'll use it if available.
          try {
            withCredentials([file(credentialsId: "${env.KUBECONFIG_CREDENTIAL}", variable: 'KUBECONFIG_FILE')]) {
              if (fileExists(env.KUBECONFIG_FILE)) {
                env.KUBECONFIG = env.KUBECONFIG_FILE
                echo "Using kubeconfig from Jenkins credential ${env.KUBECONFIG_CREDENTIAL}"
              } else {
                echo "kubeconfig credential not found on agent; assuming kubectl already configured."
              }
            }
          } catch (e) {
            echo "No kubeconfig credential bound (KUBECONFIG_CREDENTIAL). Assuming kubectl context is configured on the agent."
          }

          // Apply manifests from repo/k8s if present, else apply a small inline manifest
          if (fileExists("${env.WORKSPACE}/k8s")) {
            echo "Applying manifests from k8s/ directory"
            sh "kubectl apply -f k8s/ -n mlops || kubectl apply -f k8s/"
          } else {
            echo "k8s/ not found — applying inline manifest"
            sh '''
              kubectl create ns mlops --dry-run=client -o yaml | kubectl apply -f -
              kubectl apply -f - <<'YAML'
              apiVersion: apps/v1
              kind: Deployment
              metadata:
                name: mlops-app
                namespace: mlops
              spec:
                replicas: 1
                selector:
                  matchLabels:
                    app: mlops-app
                template:
                  metadata:
                    labels:
                      app: mlops-app
                  spec:
                    imagePullSecrets:
                      - name: dockerhub-secret
                    containers:
                      - name: mlops-app
                        image: ${DOCKERHUB_REPOSITORY}:latest
                        ports:
                          - containerPort: 5000
              ---
              apiVersion: v1
              kind: Service
              metadata:
                name: mlops-service
                namespace: mlops
              spec:
                type: NodePort
                selector:
                  app: mlops-app
                ports:
                  - protocol: TCP
                    port: 5000
                    targetPort: 5000
                    nodePort: 30007
              YAML
            '''
          }

          // Wait for rollout and show diagnostics if something goes wrong
          sh '''
            kubectl rollout status deployment/mlops-app -n mlops --timeout=120s || (kubectl describe deployment/mlops-app -n mlops; kubectl get pods -n mlops -o wide; exit 1)
            kubectl get pods -n mlops -o wide || true
          '''
        }
      }
    }
  } // stages

  post {
    always {
      echo 'Pipeline finished.'
      sh 'kubectl get ns || true'
    }
  }
}
