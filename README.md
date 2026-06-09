<<<<<<< HEAD
# DevOps 101 — Learn Tools One at a Time

A minimal app built specifically for learning DevOps tools in order.
Each tool is introduced one at a time with clear explanations.

## The App

A simple webpage that shows which environment it's in — colour changes per env:
- 🟢 **Green** = dev
- 🟠 **Orange** = qa  
- 🔴 **Red** = prod

## Learning Order

| Step | Tool | What you learn |
|------|------|----------------|
| 1 | **Git** | push code, branch, commit history |
| 2 | **Docker** | build image, run locally, push to Docker Hub |
| 3 | **Kubernetes** | deploy with raw YAML, pods, services, ingress |
| 4 | **Helm** | templates, values overrides, rollback |
| 5 | **GitHub Actions** | CI pipeline, Trivy scan, auto-push |
| 6 | **Argo CD** | GitOps, auto-sync, drift detection |
| 7 | **Promote to prod** | manual GitOps promotion flow |

## Follow the guide

👉 Open `docs/LEARN.md` and follow it top to bottom.

## Project Structure

```
devops-101/
├── app/                   The Flask app (one file!)
├── docker/                Dockerfile + docker-compose
├── kubernetes/            Raw K8s YAML per environment (Step 3)
├── helm/devops101/        Helm chart (Step 4)
├── gitops/                Values overrides + Argo CD apps (Steps 5-6)
├── .github/workflows/     GitHub Actions CI (Step 5)
└── docs/LEARN.md          Step-by-step guide
```

## KodeKloud Playground limits

- AKS node size: **Standard_B2s only**
- Max nodes: **2**
- Disable Container Insights + Alerting when creating AKS
- Use your existing **ODL-* resource group**
=======
# deepanshu-devops
Deepanshu Project
>>>>>>> 1f7d10d248a8a293d9ffc207e45ef030ee105ca2
