# Streamlit MySQL App

A small CRUD dashboard built with Streamlit and MySQL.

## Local run

```bash
docker build -t YOUR_DOCKERHUB_USER/streamlit-mysql-app:0.1.0 .
docker run --rm -p 8501:8501 \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=3306 \
  -e DB_NAME=appdb \
  -e DB_USER=appuser \
  -e DB_PASSWORD=apppassword \
  YOUR_DOCKERHUB_USER/streamlit-mysql-app:0.1.0
```
