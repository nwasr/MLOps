pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REGISTRY = 'https://registry.hub.docker.com'
    DOCKERHUB_REPOSITORY = 'pep34/mlops-proj-01'
    GIT_CREDENTIALS = 'mlops-git-token'
    KUBECONFIG_CREDENTIAL_ID = 'mlops-kubeconfig'   // secret file in Jenkins
    ANSIBLE_INVENTORY = 'ansible/inventory.ini'
    ANSIBLE_PLAYBOOK = 'ansible/site.yml'
  }

  options {
    ansiColor('xterm')
    timestamps()
    timeout(time: 90, unit: 'MINUTES')
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

    stage('Setup & Lint') {
      steps {
        sh '''
          set -euo pipefail
          python3 -m venv venv
          . venv/bin/activate
          pip install --upgrade pip
          venv/bin/pip install -r requirements.txt || true

          # linters -> produce reports but don't fail build on style-only issues
          venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero || true
          venv/bin/flake8 app.py train.py --ignore=E501 --output-file=flake8-report.txt || true
          venv/bin/black --check app.py train.py || true || true
        '''
      }
    }

    stage('Unit Tests') {
      steps {
        sh '''
          set -euo pipefail
          . venv/bin/activate
          mkdir -p tests
          venv/bin/pytest --junitxml=tests/results.xml tests/ || true
        '''
      }
    }

    stage('Trivy FS Scan') {
      steps {
        sh '''
          set -euo pipefail
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
          set -euo pipefail
          echo "Building image ${FULL_IMAGE}"
          docker build -t "${FULL_IMAGE}" .
        '''
      }
    }

    stage('Trivy Image Scan') {
      steps {
        sh '''
          set -euo pipefail
          trivy image "${FULL_IMAGE}" --severity HIGH,CRITICAL --format json --output trivy-image.json || true
          trivy image "${FULL_IMAGE}" --format table -o trivy-image-report.txt || true
        '''
      }
    }

    stage('Push Image') {
      steps {
        script {
          docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {
            sh '''
              set -euo pipefail
              echo "Pushing ${FULL_IMAGE} to Docker Hub..."
              docker push "${FULL_IMAGE}"
              echo "Tagging and pushing latest..."
              docker tag "${FULL_IMAGE}" "${DOCKERHUB_REPOSITORY}:latest" || true
              docker push "${DOCKERHUB_REPOSITORY}:latest" || true
            '''
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL_ID}", variable: 'KUBECONFIG_FILE')]) {
          sh '''
            set -euo pipefail
            export KUBECONFIG="$KUBECONFIG_FILE"

            # sanity check
            echo "Checking kubectl connectivity..."
            if ! kubectl --request-timeout=5s get nodes >/dev/null 2>&1; then
              echo "ERROR: kubectl cannot reach API server from this agent. Aborting Kubernetes deploy."
              kubectl config view --minify || true
              kubectl cluster-info || true
              exit 1
            fi

            echo "Applying k8s manifests (namespace/service/hpa)..."
            kubectl apply -f k8s/ --recursive --validate=false

            echo "Atomically updating deployment image to ${FULL_IMAGE}..."
            kubectl set image deployment/mlops-app mlops-app="${FULL_IMAGE}" -n mlops --record

            echo "Waiting for rollout (timeout 300s)..."
            kubectl rollout status deployment/mlops-app -n mlops --timeout=300s || {
               echo "Rollout timed out or failed - printing pods & events for debugging"
               kubectl get pods -n mlops -o wide || true
               kubectl get events -n mlops --sort-by='.metadata.creationTimestamp' || true
               exit 1
            }

            echo "Kubernetes deployment complete."
          '''
        }
      }
    }

    stage('Ansible Deploy (optional)') {
      steps {
        echo "Running minimal Ansible playbook (local) to deploy pulled image (if ansible is available)..."
        sh '''
          set -euo pipefail
          # show chosen image
          echo "Image passed to Ansible: ${FULL_IMAGE}"

          # check ansible present; if not, skip gracefully
          if ! command -v ansible-playbook >/dev/null 2>&1; then
            echo "ansible-playbook not found on agent — skipping Ansible deploy. (Run 'sudo apt install ansible' to enable)"
            exit 0
          fi

          # run the playbook from repo's ansible folder; use local connection
          cd ansible
          ansible-playbook -i inventory.ini site.yml --connection=local -e "image=${FULL_IMAGE}"
        '''
      }
    }

  } // stages

  post {
    always {
      echo 'Archiving artifacts...'
      archiveArtifacts artifacts: 'pylint-report.txt, flake8-report.txt, trivy-*.json, trivy-*.txt, tests/results.xml', allowEmptyArchive: true
      junit allowEmptyResults: true, testResults: 'tests/**/results.xml'
    }
    success {
      echo "Pipeline succeeded — Deployed ${FULL_IMAGE}"
    }
    failure {
      echo "Pipeline failed — check console output"
    }
  }
}
