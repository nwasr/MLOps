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

    stage('Lint Code') {
      steps {
        script {
          echo 'Linting Python Code...'
          sh '''
            python3 -m venv venv
            . venv/bin/activate
            venv/bin/pip install --upgrade pip
            venv/bin/pip install -r requirements.txt || true

            # Reports shouldn't fail the build, but we still run them
            venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero || true
            venv/bin/flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt || true
            venv/bin/black --check app.py train.py || true
          '''
        }
      }
    }

    stage('Test Code') {
      steps {
        script {
          echo 'Running unit tests...'
          sh '''
            . venv/bin/activate
            venv/bin/pytest tests/ || true
          '''
        }
      }
    }

    stage('Trivy FS Scan') {
      steps {
        script {
          echo 'Scanning filesystem with Trivy...'
          sh '''
            # if trivy not installed on agent, this will fail — ensure agent has trivy
            trivy fs . --severity HIGH,CRITICAL --format json --output trivy-fs-report.json || true
          '''
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        script {
          echo 'Building Docker image...'

          // create unique image tag
          env.GIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
          env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
          env.FULL_IMAGE = "${DOCKERHUB_REPOSITORY}:${IMAGE_TAG}"

          // build
          dockerImage = docker.build(env.FULL_IMAGE)
        }
      }
    }

    stage('Trivy Docker Image Scan') {
      steps {
        script {
          echo 'Scanning built image with Trivy...'
          // scan the uniquely tagged image
          sh "trivy image ${env.FULL_IMAGE} --format table -o trivy-image-report.txt || true"
        }
      }
    }

    stage('Push Docker Image') {
      steps {
        script {
          echo "Pushing Docker images to Docker Hub..."
          docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {
            // push uniquely-tagged image
            dockerImage.push()
            // tag + push latest (optional)
            sh "docker tag ${env.FULL_IMAGE} ${DOCKERHUB_REPOSITORY}:latest || true"
            dockerImage.push('latest')
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        script {
          echo "Deploying to Kubernetes..."

          withCredentials([file(credentialsId: 'mlops-kubeconfig', variable: 'KUBECONFIG_FILE')]) {
            sh '''
              set -euo pipefail
              echo "Using kubeconfig provided by Jenkins secret"
              export KUBECONFIG="$KUBECONFIG_FILE"

              echo "Cluster connectivity:"
              kubectl get nodes

              # copy manifests so we don't mutate repo
              cp -r k8s k8s-deploy || true

              # replace placeholder with actual image
              sed -i "s|IMAGE_REPLACE|${DOCKERHUB_REPOSITORY}:${IMAGE_TAG}|g" k8s-deploy/deployment.yaml

              # apply namespace first (idempotent)
              echo "Applying namespace..."
              kubectl apply -f k8s-deploy/namespace.yaml

              # wait for namespace to become Active (best-effort)
              echo "Waiting for namespace 'mlops' to become Active (timeout 60s)..."
              timeout=60
              elapsed=0
              while true; do
                phase=$(kubectl get ns mlops -o jsonpath='{.status.phase}' 2>/dev/null || echo "")
                if [ "$phase" = "Active" ]; then
                  echo "namespace/mlops is Active"
                  break
                fi
                sleep 2
                elapsed=$((elapsed+2))
                if [ $elapsed -ge $timeout ]; then
                  echo "Timed out waiting for namespace to be Active (status: '$phase'). Continuing..."
                  break
                fi
              done

              # apply remaining manifests
              echo "Applying manifests (deployment, service, hpa if present)..."
              kubectl apply -f k8s-deploy/ --recursive

              # wait for rollout
              echo "Waiting for deployment rollout..."
              kubectl rollout status deployment/mlops-app -n mlops --timeout=180s
            '''
          }
        }
      }
    }

  } // stages

  post {
    always {
      echo 'Archiving reports...'
      archiveArtifacts artifacts: 'pylint-report.txt, flake8-report.txt, trivy-*.json, trivy-*.txt', allowEmptyArchive: true
      junit allowEmptyResults: true, testResults: 'tests/**/test-*.xml'
    }
    success {
      echo "Pipeline completed successfully: ${env.FULL_IMAGE}"
    }
    failure {
      echo "Pipeline failed — check console output"
    }
  }
}
