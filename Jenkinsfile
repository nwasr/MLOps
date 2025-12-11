pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REGISTRY = 'https://registry.hub.docker.com'
    DOCKERHUB_REPOSITORY = 'pep34/mlops-proj-01'
    GIT_CREDENTIALS = 'mlops-git-token'
    KUBECONFIG_CREDENTIAL_ID = 'mlops-kubeconfig'   // file credential
  }

  options {
    ansiColor('xterm')
    timestamps()
    timeout(time: 60, unit: 'MINUTES')
  }

  stages {

    stage('Clone Repository') {
      steps {
        echo 'Cloning repository...'
        checkout scmGit(
          branches: [[name: '*/main']],
          userRemoteConfigs: [[
            credentialsId: "${GIT_CREDENTIALS}",
            url: 'https://github.com/nwasr/MLOps.git'
          ]]
        )
      }
    }

    stage('Lint & Setup venv') {
      steps {
        echo 'Setting up virtualenv and running linters...'
        sh '''
          set -euo pipefail
          python3 -m venv venv
          . venv/bin/activate
          venv/bin/pip install --upgrade pip
          venv/bin/pip install -r requirements.txt || true

          # produce reports but don't fail the build for style issues
          venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero || true
          venv/bin/flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt || true
          venv/bin/black --check app.py train.py || true || true
        '''
      }
    }

    stage('Unit Tests') {
      steps {
        echo 'Running unit tests...'
        sh '''
          set -euo pipefail
          . venv/bin/activate
          mkdir -p tests
          venv/bin/pytest --junitxml=tests/junit-report.xml tests/ || true
        '''
      }
    }

    stage('Trivy FS Scan') {
      steps {
        echo 'Running Trivy filesystem scan (HIGH,CRITICAL)...'
        sh '''
          set -euo pipefail
          # If trivy is not present on agent, this will fail
          trivy fs . --severity HIGH,CRITICAL --format json --output trivy-fs-report.json || true
        '''
      }
    }

    stage('Build Docker Image') {
      steps {
        echo 'Building Docker image...'
        sh '''
          set -euo pipefail
          GIT_SHORT=$(git rev-parse --short HEAD)
          IMAGE_TAG="${BUILD_NUMBER}-${GIT_SHORT}"
          FULL_IMAGE="${DOCKERHUB_REPOSITORY}:${IMAGE_TAG}"
          echo "IMAGE_TAG=${IMAGE_TAG}" > build-image-vars.txt
          echo "FULL_IMAGE=${FULL_IMAGE}" >> build-image-vars.txt
          echo "Building ${FULL_IMAGE}..."
          docker build -t "${FULL_IMAGE}" .
        '''
      }
    }

    stage('Trivy Image Scan') {
      steps {
        echo 'Running Trivy image scan...'
        sh '''
          set -euo pipefail
          source build-image-vars.txt
          trivy image "${FULL_IMAGE}" --severity HIGH,CRITICAL --format json --output trivy-image-report.json || true
          trivy image "${FULL_IMAGE}" --format table -o trivy-image-report.txt || true
        '''
      }
    }

    stage('Push Image') {
      steps {
        echo 'Pushing image to Docker Hub...'
        withCredentials([usernamePassword(credentialsId: "${DOCKERHUB_CREDENTIAL_ID}", usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_PSW')]) {
          sh '''
            set -euo pipefail
            source build-image-vars.txt
            echo "${DOCKERHUB_PSW}" | docker login -u "${DOCKERHUB_USER}" --password-stdin "${DOCKERHUB_REGISTRY#https://}" || true
            docker push "${FULL_IMAGE}"
            docker tag "${FULL_IMAGE}" "${DOCKERHUB_REPOSITORY}:latest" || true
            docker push "${DOCKERHUB_REPOSITORY}:latest" || true
          '''
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        echo 'Deploying to Kubernetes (apply manifests + set image + wait for rollout)'
        withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL_ID}", variable: 'KUBECONFIG_FILE')]) {
          sh '''
            set -euo pipefail
            export KUBECONFIG="$KUBECONFIG_FILE"
            source build-image-vars.txt

            # safety: ensure IMAGE_TAG is set
            if [ -z "${IMAGE_TAG:-}" ]; then
              echo "ERROR: IMAGE_TAG is empty"; exit 1
            fi

            echo "KUBECONFIG in use: $KUBECONFIG"
            echo "Applying manifests (namespace/service/hpa etc):"
            kubectl apply -f k8s-deploy/ --recursive

            echo "Now setting deployment image to: ${FULL_IMAGE}"
            kubectl set image deployment/mlops-app mlops-app="${FULL_IMAGE}" -n mlops --record

            echo "Deployment image (post-set):"
            kubectl get deployment mlops-app -n mlops -o=jsonpath='{.spec.template.spec.containers[0].image}'; echo

            echo "Waiting for rollout to finish (timeout 300s)..."
            kubectl rollout status deployment/mlops-app -n mlops --timeout=300s || {
              echo "Rollout status timed out or failed — printing pod status and events for debug";
              kubectl get pods -n mlops -o wide || true
              kubectl get events -n mlops --sort-by='.metadata.creationTimestamp' || true
              exit 1
            }

            echo "Rollout completed."
          '''
        }
      }
    }

  } // stages

  post {
    always {
      echo 'Archiving reports and build metadata...'
      archiveArtifacts artifacts: 'pylint-report.txt, flake8-report.txt, trivy-*.json, trivy-*.txt, build-image-vars.txt', allowEmptyArchive: true
      junit allowEmptyResults: true, testResults: 'tests/**/junit-report.xml'
    }
    success {
      script {
        def full = readFile('build-image-vars.txt').split('\n').find{ it.startsWith('FULL_IMAGE=') }?.split('=')[1] ?: "${DOCKERHUB_REPOSITORY}:latest"
        echo "Pipeline succeeded — Deployed: ${full}"
      }
    }
    failure {
      echo 'Pipeline failed — check console output'
    }
  }
}
