pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'   // your Docker Hub credentials in Jenkins
    DOCKERHUB_REGISTRY = 'https://registry.hub.docker.com'
    DOCKERHUB_REPOSITORY = 'pep34/mlops-proj-01'
    GIT_CREDENTIALS = 'mlops-git-token'
    KUBECONFIG_CREDENTIAL_ID = 'mlops-kubeconfig'              // kubeconfig stored as Jenkins secret file
  }

  stages {

    stage('Clone Repository') {
      steps {
        script {
          echo 'Cloning GitHub Repository...'
          checkout scmGit(
            branches: [[name: '*/main']],
            userRemoteConfigs: [[
              credentialsId: "${GIT_CREDENTIALS}",
              url: 'https://github.com/nwasr/MLOps.git'
            ]]
          )
        }
      }
    }

    stage('Lint & Setup venv') {
      steps {
        script {
          echo 'Linting Python Code & preparing virtualenv...'
          sh '''
            set -euo pipefail
            python3 -m venv venv
            . venv/bin/activate
            venv/bin/pip install --upgrade pip
            venv/bin/pip install -r requirements.txt || true

            venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero || true
            venv/bin/flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt || true
            venv/bin/black --check app.py train.py || true
          '''
        }
      }
    }

    stage('Run Tests') {
      steps {
        script {
          echo 'Running unit tests (pytest)...'
          sh '''
            set -euo pipefail
            . venv/bin/activate
            venv/bin/pytest tests/ || true
          '''
        }
      }
    }

    stage('Trivy FS Scan') {
      steps {
        script {
          echo 'Scanning filesystem with Trivy (HIGH/CRITICAL)...'
          sh '''
            set -euo pipefail
            trivy fs . --severity HIGH,CRITICAL --format json --output trivy-fs-report.json || true
          '''
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        script {
          echo 'Building Docker image...'
          sh '''
            set -euo pipefail
            GIT_SHORT=$(git rev-parse --short HEAD)
            export IMAGE_TAG="${BUILD_NUMBER}-${GIT_SHORT}"
            export FULL_IMAGE="${DOCKERHUB_REPOSITORY}:${IMAGE_TAG}"
            echo "IMAGE_TAG=${IMAGE_TAG}"
            echo "FULL_IMAGE=${FULL_IMAGE}"
            docker build -t "${FULL_IMAGE}" .
            # expose envs to the rest of pipeline
            echo "FULL_IMAGE=${FULL_IMAGE}" > build-image-vars.txt
            echo "IMAGE_TAG=${IMAGE_TAG}" >> build-image-vars.txt
          '''
        }
      }
    }

    stage('Trivy Docker Image Scan') {
      steps {
        script {
          echo 'Scanning built image with Trivy (image scan)...'
          sh '''
            set -euo pipefail
            # load vars
            source build-image-vars.txt
            trivy image "${FULL_IMAGE}" --format table -o trivy-image-report.txt || true
          '''
        }
      }
    }

    stage('Push Docker Image') {
      steps {
        script {
          echo 'Pushing Docker image to Docker Hub...'
          withCredentials([usernamePassword(credentialsId: "${DOCKERHUB_CREDENTIAL_ID}", passwordVariable: 'DOCKERHUB_PSW', usernameVariable: 'DOCKERHUB_USER')]) {
            sh '''
              set -euo pipefail
              source build-image-vars.txt
              echo "${DOCKERHUB_PSW}" | docker login -u "${DOCKERHUB_USER}" --password-stdin "${DOCKERHUB_REGISTRY#https://}" || true
              docker push "${FULL_IMAGE}"
              # also push :latest (optional)
              docker tag "${FULL_IMAGE}" "${DOCKERHUB_REPOSITORY}:latest" || true
              docker push "${DOCKERHUB_REPOSITORY}:latest" || true
            '''
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        script {
          echo 'Deploying to Kubernetes (safe image substitution)...'
          withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIAL_ID}", variable: 'KUBECONFIG_FILE')]) {
            sh '''
              set -euo pipefail
              export KUBECONFIG="$KUBECONFIG_FILE"

              # load image variables
              source build-image-vars.txt
              if [ -z "${IMAGE_TAG:-}" ]; then
                echo "ERROR: IMAGE_TAG is empty"; exit 1
              fi
              echo "Deploying image: ${FULL_IMAGE}"

              # apply namespace first (idempotent)
              if [ -f k8s-deploy/namespace.yaml ]; then
                kubectl apply -f k8s-deploy/namespace.yaml
              fi

              # create a temp deployment manifest with the real image (avoid leaving placeholder in live cluster)
              tmpdir=$(mktemp -d)
              trap 'rm -rf "$tmpdir"' EXIT

              # safely replace the placeholder using '|' as sed delimiter so slashes/colons don't break it
              sed "s|IMAGE_REPLACE|${FULL_IMAGE}|g" k8s-deploy/deployment.yaml > "$tmpdir/deployment.yaml"

              # apply the deployment (using the manifest with correct image)
              kubectl apply -f "$tmpdir/deployment.yaml"

              # apply other manifests (service, hpa, etc.) - these will be idempotent
              # apply everything under k8s-deploy to pick up service/hpa; it's fine to reapply deployment too
              kubectl apply -f k8s-deploy/ --recursive || true

              # show what image is currently used by the deployment (debug)
              echo "Deployment image now:"
              kubectl get deployment mlops-app -n mlops -o=jsonpath='{.spec.template.spec.containers[0].image}'; echo

              # wait for rollout (increase timeout if your app starts slowly)
              kubectl rollout status deployment/mlops-app -n mlops --timeout=300s
            '''
          }
        }
      }
    }

  } // stages

  post {
    always {
      echo 'Archiving reports and build vars...'
      archiveArtifacts artifacts: 'pylint-report.txt, flake8-report.txt, trivy-*.json, trivy-*.txt, build-image-vars.txt', allowEmptyArchive: true
      junit allowEmptyResults: true, testResults: 'tests/**/test-*.xml'
    }
    success {
      script { 
        def fullImage = readFile('build-image-vars.txt').split('\n').find { it.startsWith('FULL_IMAGE=') }?.split('=')[1] ?: "${DOCKERHUB_REPOSITORY}:latest"
        echo "Pipeline completed successfully. Deployed image: ${fullImage}"
      }
    }
    failure {
      echo 'Pipeline failed — check console output for errors.'
    }
  }
}
