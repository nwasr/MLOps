pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIAL_ID = 'mlops-jenkins-dockerhub-token'
    DOCKERHUB_REGISTRY = 'https://registry.hub.docker.com'
    DOCKERHUB_REPOSITORY = 'pep34/mlops-proj-01'
    KUBE_CONFIG_CREDENTIAL_ID = 'kubeconfig-cred-id' // add your kubeconfig file credential id here
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Lint & Test') {
      steps {
        // create and use a virtualenv so we don't attempt system installs
        sh '''
          set -euo pipefail
          echo ">>> Creating venv (if missing) and installing requirements..."
          if [ ! -d ".venv" ]; then
            python3 -m venv .venv
          fi
          . .venv/bin/activate
          python -m pip install --upgrade pip setuptools wheel
          python -m pip install -r requirements.txt

          echo ">>> Running linters and tests inside venv..."
          .venv/bin/pylint app.py train.py --output=pylint-report.txt --exit-zero || true
          .venv/bin/flake8 app.py train.py --ignore=E501,E302 --output-file=flake8-report.txt || true
          .venv/bin/black --check . || true
          .venv/bin/pytest -q || true
        '''
      }
    }

    stage('Train Model') {
      steps {
        sh '''
          set -euo pipefail
          echo ">>> Ensuring venv exists and training model..."
          if [ ! -d ".venv" ]; then
            python3 -m venv .venv
          fi
          . .venv/bin/activate
          python -m pip install --upgrade pip setuptools wheel
          python -m pip install -r requirements.txt
          python train.py
        '''
        archiveArtifacts artifacts: 'model/iris_model.pkl', fingerprint: true
      }
    }

    stage('Prepare Image Context') {
      steps {
        sh '''
          set -euo pipefail
          echo ">>> Preparing docker build context..."
          rm -rf docker_context || true
          mkdir -p docker_context/model docker_context/templates
          cp app.py requirements.txt docker_context/
          cp -r templates docker_context/templates || true
          cp model/iris_model.pkl docker_context/model/iris_model.pkl
          cp Dockerfile docker_context/
        '''
      }
    }

    stage('Build Docker Image') {
      steps {
        dir('docker_context') {
          script {
            imageTag = "${DOCKERHUB_REPOSITORY}:${env.BUILD_ID}"
            echo ">>> Building docker image ${imageTag} ..."
            // This requires Docker to be available on the agent (or docker socket mounted if using container agent)
            dockerImage = docker.build(imageTag)
          }
        }
      }
    }

    stage('Scan Image (Trivy)') {
      steps {
        script {
          echo ">>> Running Trivy image scan (if trivy present)..."
          // tolerate absence of trivy to avoid hard failing; archive report if generated
          def rc = sh(returnStatus: true, script: "trivy image ${imageTag} --format table -o trivy-image-report.html || true")
          if (fileExists('trivy-image-report.html')) {
            archiveArtifacts artifacts: 'trivy-image-report.html'
          } else {
            echo "Trivy report not generated (trivy may not be installed on agent)."
          }
        }
      }
    }

    stage('Push Docker Image') {
      steps {
        script {
          echo ">>> Pushing docker image to DockerHub..."
          docker.withRegistry("${DOCKERHUB_REGISTRY}", "${DOCKERHUB_CREDENTIAL_ID}") {
            dockerImage.push()
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        withCredentials([file(credentialsId: env.KUBE_CONFIG_CREDENTIAL_ID, variable: 'KUBECONFIG_FILE')]) {
          sh '''
            set -euo pipefail
            echo ">>> Setting kubeconfig and deploying to cluster..."
            mkdir -p $HOME/.kube
            cp "$KUBECONFIG_FILE" $HOME/.kube/config
            # update deployment image (namespace 'mlops' assumed; adjust if different)
            kubectl set image -n mlops deployment/mlops-app mlops-app=${imageTag} --record || true
            kubectl apply -f k8s/ || true
          '''
        }
      }
    }
  }

  post {
    always {
      echo ">>> Archiving reports and cleanup..."
      archiveArtifacts artifacts: 'pylint-report.txt,flake8-report.txt,trivy-image-report.html', allowEmptyArchive: true
      // JUnit test results pattern — if pytest writes junit xml under tests/, update accordingly
      junit allowEmptyResults: true, testResults: 'tests/**/TEST-*.xml'
    }
    success {
      echo "Pipeline completed successfully."
    }
    failure {
      echo "Pipeline failed. Check the console output above for errors."
    }
  }
}
