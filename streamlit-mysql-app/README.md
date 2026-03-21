# Streamlit + MySQL + Helm

## What is included
- Streamlit CRUD application
- Dockerfile
- Helm chart that deploys the app and MySQL
- Sample override values file

## Build the image
```bash
cd app
docker build -t YOUR_DOCKERHUB_USER/streamlit-mysql-app:0.1.0 .
```

## Push to Docker Hub
```bash
docker login
docker push YOUR_DOCKERHUB_USER/streamlit-mysql-app:0.1.0
```

## Deploy with Helm
```bash
helm upgrade --install sales-demo ./helm/streamlit-mysql \
  -f sample-values.yaml \
  --namespace demo \
  --create-namespace
```

## Access from Minikube
```bash
kubectl port-forward -n demo svc/sales-demo-streamlit-mysql-app 8501:8501
```

Open `http://localhost:8501`
