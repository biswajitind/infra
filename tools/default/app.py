from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from kubernetes import client, config
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def load_k8s():
    try:
        config.load_incluster_config()
    except Exception:
        config.load_kube_config()


def get_ingress_urls():
    load_k8s()
    api = client.NetworkingV1Api()

    namespace = os.getenv("TARGET_NAMESPACE", "")
    ingress_class = os.getenv("INGRESS_CLASS", "")

    if namespace:
        items = api.list_namespaced_ingress(namespace=namespace).items
    else:
        items = api.list_ingress_for_all_namespaces().items

    urls = []

    for ing in items:
        if ingress_class:
            cls = ing.spec.ingress_class_name
            if cls != ingress_class:
                continue

        if not ing.spec.rules:
            continue

        for rule in ing.spec.rules:
            host = rule.host or "localhost"
            if not rule.http or not rule.http.paths:
                continue

            for p in rule.http.paths:
                path = p.path or "/"
                if host == "localhost":
                    url = f"http://localhost{path}"
                else:
                    url = f"http://{host}{path}"
                urls.append(
                    {
                        "namespace": ing.metadata.namespace,
                        "ingress": ing.metadata.name,
                        "host": host,
                        "path": path,
                        "url": url,
                    }
                )

    return sorted(urls, key=lambda x: (x["namespace"], x["ingress"], x["host"], x["path"]))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    urls = get_ingress_urls()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "urls": urls,
        },
    )