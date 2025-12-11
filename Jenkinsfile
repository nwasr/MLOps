pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REGISTRY      = ''   // use default (Docker Hub)
    DOCKERHUB_REPOSITORY    = 'pep34/mlops-proj-01'
    K8S_MANIFEST_DIR        = 'k8s' // directory in repo containing namespace/deploy/service/hpa YAMLs
    // optional: KUBECONFIG_CREDENTIAL should be Jenkins "Secret file" credential id that contains kubeconfig
    KUBECONFIG_CREDENTIAL   = 'kubeconfig-cred' 
  }

  stages {
    stage('Clone Repository') {
      steps {
        checkout scm
      }
    }

    // ... your build/lint/test/trivy/docker build/push stages, unchanged ...
    stage('Build Docker Image') {
      steps {
        script {
          echo 'Building Docker Image...'
          def dockerImage = docker.build("${DOCKERHUB_REPOSITORY}:latest")
          // store image name to env for later push
          env.IMAGE_TAG = "${DOCKERHUB_REPOSITORY}:latest"
        }
      }
    }

    stage('Push Docker Image') {
      steps {
        script {
          echo 'Pushing Docker Image to DockerHub...'
          docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {
            docker.image(env.IMAGE_TAG).push()
            docker.image(env.IMAGE_TAG).push("${BUILD_NUMBER}") // optional build tag
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        script {
          // choose path: use kubeconfig credential if provided, else assume kubectl is already configured
          withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL}", variable: 'KUBECONFIG_FILE')]) {
            // If a kubeconfig credential exists, point KUBECONFIG env to it for kubectl commands
            if (fileExists(env.KUBECONFIG_FILE)) {
              env.KUBECONFIG = env.KUBECONFIG_FILE
              echo "Using kubeconfig from Jenkins credential: ${KUBECONFIG_CREDENTIAL}"
            } else {
              // No kubeconfig credential present — assume kubectl on agent already configured
              echo "No kubeconfig file credential found or not present — assuming kubectl is configured in the environment"
              // Unset env.KUBECONFIG to avoid overriding system
              env.remove('KUBECONFIG')
            }

            // Optionally create docker registry secret in target namespace if docker creds are available.
            // This uses Jenkins username/token stored as username/password credential with ID DOCKERHUB_CREDENTIAL_ID.
            // If the image is public, this step is harmless (will fail only if wrong creds) — optional behavior below uses try/catch.
            def createPullSecret = """
              set -o errexit
              NAMESPACE=mlops
              # Create namespace if not exists
              kubectl get ns $NAMESPACE >/dev/null 2>&1 || kubectl create ns $NAMESPACE

              # If DOCKER credentials available via Jenkins, create dockerhub secret (idempotent)
              echo "Creating dockerhub imagePullSecret (idempotent)..."
            """

            // create secret only if registry credentials exist in Jenkins credentials store
            try {
              withCredentials([usernamePassword(credentialsId: "${DOCKERHUB_CREDENTIAL_ID}", usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
                sh """
                  ${createPullSecret}
                  kubectl create secret docker-registry dockerhub-secret \
                    --docker-username="$DH_USER" \
                    --docker-password="$DH_TOKEN" \
                    --docker-server=https://index.docker.io/v1/ \
                    -n mlops 2>/dev/null || echo "dockerhub-secret already exists or creation skipped"
                """
              }
            } catch (err) {
              // if credentials are not available, skip secret creation
              echo "Skipping imagePullSecret creation (no DOCKER credentials available in Jenkins)."
            }

            // Apply k8s manifests. If a k8s directory exists in repo, apply it; else fallback to inline manifest (you can replace with your manifest)
            if (fileExists(env.WORKSPACE + "/${K8S_MANIFEST_DIR}")) {
              echo "Applying k8s manifests from ${K8S_MANIFEST_DIR}/"
              sh """
                kubectl apply -f ${K8S_MANIFEST_DIR}/ -n mlops || kubectl apply -f ${K8S_MANIFEST_DIR}/
              """
            } else {
              echo "k8s manifest directory not found. Applying inline example manifest..."
              sh '''
                kubectl apply -f - <<'YAML'
                apiVersion: v1
                kind: Namespace
                metadata:
                  name: mlops
                ---
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

            // wait rollout
            sh '''
              kubectl rollout status deploy/mlops-app -n mlops --timeout=120s || (kubectl describe deploy/mlops-app -n mlops; kubectl get pods -n mlops -o wide; exit 1)
            '''

            // show pod status and one-line pod logs for quick debugging
            sh '''
              echo "Pods in mlops namespace:"
              kubectl get pods -n mlops -o wide

              POD=$(kubectl get pods -n mlops -l app=mlops-app -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
              if [ -n "$POD" ]; then
                echo "Recent logs from $POD (tail 200 lines):"
                kubectl logs -n mlops "$POD" --tail=200 || true
              fi
            '''
          } // end withCredentials (kubeconfig)
        } // end script
      } // end steps
    } // end Deploy to Kubernetes

  } // end stages

  post {
    always {
      echo 'Pipeline finished. Gathering minimal diagnostics...'
      sh '''
        echo "kubectl context:"
        kubectl config current-context || true
        echo "kubectl get ns:"
        kubectl get ns || true
      '''
    }
  }
}
