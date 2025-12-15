# MLOps Pipeline for Iris Flower Classification

test1
test2

A complete CI/CD pipeline for deploying an Iris Flower Classification model using Jenkins, Docker, Kubernetes, GitHub Webhooks, and Minikube.

---

## Tech Stack

* Python, scikit-learn, Flask
* Docker for containerization
* Jenkins for CI/CD automation
* Kubernetes (Minikube) for deployment
* Trivy for vulnerability scanning
* GitHub Webhooks for automatic triggers

---

## Pipeline Overview

1. GitHub push triggers Jenkins via webhook
2. CI stages:

   * Linting (pylint, flake8)
   * Testing (pytest)
   * Filesystem scan (Trivy)
3. Docker image build and push to DockerHub
4. CD stages:

   * Apply Kubernetes manifests
   * Update deployment image using `kubectl set image`
   * Rolling update and rollout monitoring
5. Application becomes available at:

```
http://<minikube-ip>:30007
```

---

## Machine Learning Model

A simple classifier trained on the Iris dataset, predicting:

* Setosa
* Versicolor
* Virginica

Flask API endpoints:

```
/          → Home UI
/predict   → Returns predicted class name
/health    → Liveness probe
/ready     → Readiness probe
```

---

## Kubernetes Components

* Deployment with 2 replicas
* NodePort service exposing port 5000 on 30007
* Horizontal Pod Autoscaler (1–4 pods, CPU-based)
* Liveness and readiness probes for reliability

---

## Deployment Commands (Manual)

```
kubectl apply -f k8s/ --recursive
kubectl set image deployment/mlops-app mlops-app=<image:tag> -n mlops
kubectl rollout status deployment/mlops-app -n mlops
```

---

## Run Locally

Train the model:

```
python train.py
```

Start the server:

```
python app.py
```

Visit:

```
http://127.0.0.1:5000
```

---

## Project Structure

```
.
├── app.py
├── train.py
├── model/iris_model.pkl
├── Jenkinsfile
├── k8s/
├── tests/
└── requirements.txt
```

