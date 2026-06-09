# DevOps 101 — Learn Each Tool Step by Step
# ─────────────────────────────────────────────────────────────────────────────
# Goal: understand WHAT each tool does and WHY before moving to the next.
# Each step builds on the last. Don't skip steps.
# ─────────────────────────────────────────────────────────────────────────────

## Fill these in first — you'll use them throughout
DOCKERHUB_USERNAME="your-dockerhub-username"   # e.g. miku123
GITHUB_USERNAME="your-github-username"
RG="your-ODL-resource-group"                   # from KodeKloud portal
AKS_NAME="devops101-aks"


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 1 — GIT
# What it does: saves your code history, lets you collaborate, triggers CI/CD
# ═══════════════════════════════════════════════════════════════════════════════

# 1. Create a new GitHub repo called "devops-101" at https://github.com/new

# 2. Push this project to it:
cd /path/to/devops-101
git init
git add .
git commit -m "feat: initial devops101 project"
git branch -M main
git remote add origin https://github.com/$GITHUB_USERNAME/devops-101.git
git push -u origin main

# What just happened?
#  - git init    → created a .git folder to track changes
#  - git add     → staged files for commit
#  - git commit  → saved a snapshot with a message
#  - git push    → uploaded to GitHub

# ✅ CHECK: You can see your files at github.com/<username>/devops-101


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 2 — DOCKER
# What it does: packages your app + all its dependencies into a portable image.
#               The same image runs on your laptop, CI, and Kubernetes.
# ═══════════════════════════════════════════════════════════════════════════════

# First, look at the Dockerfile (docker/Dockerfile) and read the comments.
# Then run these commands:

# 2a. Build the image
docker build -t devops101:local -f docker/Dockerfile ./app

# What just happened?
#  - Docker read the Dockerfile top to bottom
#  - Stage 1: installed Python packages
#  - Stage 2: copied only what's needed into a clean slim image
#  - Tagged it as "devops101:local"

# 2b. Run it locally
docker run -p 5000:5000 \
  -e APP_ENV=local \
  -e APP_COLOR=#0078d4 \
  devops101:local

# Open http://localhost:5000 — you should see the blue DevOps 101 page!
# Press Ctrl+C to stop.

# 2c. Push to Docker Hub (so Kubernetes can pull it)
docker login                            # enter your Docker Hub credentials
docker tag devops101:local $DOCKERHUB_USERNAME/devops101:v1
docker push $DOCKERHUB_USERNAME/devops101:v1
docker push $DOCKERHUB_USERNAME/devops101:latest

# What just happened?
#  - docker tag    → gave the image a new name with your Docker Hub username
#  - docker push   → uploaded it to hub.docker.com

# ✅ CHECK: Go to hub.docker.com → your profile → you see devops101 repository

# Useful Docker commands to know:
docker images                           # list all local images
docker ps                               # list running containers
docker logs <container-id>              # see container output
docker exec -it <container-id> sh       # get a shell inside the container
docker rmi devops101:local              # delete a local image


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 3 — KUBERNETES (raw YAML — no Helm yet)
# What it does: runs your Docker containers at scale, restarts them if they
#               crash, balances traffic across multiple copies.
# ═══════════════════════════════════════════════════════════════════════════════

# 3a. Create AKS cluster (KodeKloud playground rules: Standard_B2s, 2 nodes max)
az login
az aks create \
  --resource-group $RG \
  --name $AKS_NAME \
  --node-vm-size Standard_B2s \
  --node-count 2 \
  --generate-ssh-keys \
  --enable-managed-identity

# Get kubectl credentials
az aks get-credentials --resource-group $RG --name $AKS_NAME

# Verify the cluster is ready
kubectl get nodes
# You should see 2 nodes with STATUS = Ready

# 3b. Create the namespaces (think of these as separate "rooms" in the cluster)
kubectl create namespace dev
kubectl create namespace qa
kubectl create namespace prod
kubectl create namespace argocd
kubectl create namespace ingress-nginx

# 3c. Install nginx-ingress (the "front door" for external traffic)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --set controller.replicaCount=1

# Wait for the external IP (takes ~2 minutes)
kubectl get svc -n ingress-nginx -w
# When EXTERNAL-IP shows a real IP (not <pending>), press Ctrl+C
INGRESS_IP=$(kubectl get svc ingress-nginx-controller \
  -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Your app will be at: http://$INGRESS_IP"

# 3d. Update the image name in the kubernetes manifests
sed -i "s|YOUR_DOCKERHUB_USERNAME|$DOCKERHUB_USERNAME|g" \
  kubernetes/dev/manifests.yaml \
  kubernetes/qa/manifests.yaml \
  kubernetes/prod/manifests.yaml

# 3e. Deploy to dev namespace using raw YAML
kubectl apply -f kubernetes/dev/manifests.yaml
kubectl apply -f kubernetes/dev/ingress.yaml

# Watch the pod start up
kubectl get pods -n dev -w
# Wait until STATUS = Running, then Ctrl+C

# 3f. Test it!
curl http://$INGRESS_IP/health         # should return {"status":"ok","env":"dev",...}
# Or open http://$INGRESS_IP in your browser — you'll see a GREEN page (dev color)

# What just happened?
#  Kubernetes read your YAML and created:
#  - ConfigMap   → stores APP_ENV, APP_COLOR env vars
#  - Deployment  → told K8s to run 1 pod with your Docker image
#  - Service     → gave the pod a stable internal address
#  - Ingress     → routed external traffic to the service

# Useful kubectl commands to know:
kubectl get pods -n dev                 # list pods
kubectl describe pod -n dev <pod-name> # detailed info + events
kubectl logs -n dev <pod-name>          # see app output
kubectl exec -it -n dev <pod-name> -- sh  # shell into pod
kubectl get all -n dev                  # everything in dev namespace
kubectl delete pod -n dev <pod-name>   # delete pod (K8s recreates it!)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 4 — HELM
# What it does: packages Kubernetes YAML as reusable templates.
#               Instead of 3 copies of the same YAML with small differences,
#               you have 1 template + 3 tiny override files.
# ═══════════════════════════════════════════════════════════════════════════════

# Look at helm/devops101/templates/all.yaml
# Notice {{ .Values.replicaCount }}, {{ .Values.app.color }} etc.
# Those {{ }} placeholders get filled in from values files.

# 4a. Deploy to dev using Helm (replaces the raw kubectl apply from step 3)
helm install devops101-dev ./helm/devops101 \
  --namespace dev \
  --values gitops/dev/values-dev.yaml \
  --set image.repository=$DOCKERHUB_USERNAME/devops101

# 4b. Deploy to qa
helm install devops101-qa ./helm/devops101 \
  --namespace qa \
  --values gitops/qa/values-qa.yaml \
  --set image.repository=$DOCKERHUB_USERNAME/devops101

# 4c. Look at what Helm is managing
helm list -A                            # all releases across all namespaces
helm status devops101-dev -n dev        # status of dev release
helm get values devops101-dev -n dev    # see what values were used

# 4d. Make a change and upgrade (this is the power of Helm!)
# Edit gitops/dev/values-dev.yaml — change color to red (#E24B4A)
# Then upgrade without rewriting all YAML:
helm upgrade devops101-dev ./helm/devops101 \
  --namespace dev \
  --values gitops/dev/values-dev.yaml \
  --set image.repository=$DOCKERHUB_USERNAME/devops101

# The page color changes! No YAML editing required.

# 4e. Rollback if something breaks
helm rollback devops101-dev 1 -n dev    # roll back to revision 1
helm history devops101-dev -n dev       # see all revisions

# What Helm gives you vs raw YAML:
#  Raw YAML: copy-paste 3 files, manually edit each one, easy to make mistakes
#  Helm:     1 template + 3 tiny value overrides, rollback built in


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 5 — GITHUB ACTIONS (CI/CD)
# What it does: automatically builds, tests, scans and pushes your image
#               every time you push code to GitHub.
# ═══════════════════════════════════════════════════════════════════════════════

# 5a. Add secrets to your GitHub repo:
#   GitHub → repo → Settings → Secrets and variables → Actions → New secret
#
#   DOCKERHUB_USERNAME  = your Docker Hub username
#   DOCKERHUB_TOKEN     = Docker Hub → Account Settings → Security → New Token

# 5b. Make a small change to test the pipeline:
echo "# trigger CI" >> app/app.py
git add app/app.py
git commit -m "test: trigger CI pipeline"
git push

# 5c. Watch it run:
#   GitHub → your repo → Actions tab
#   You'll see: Build, Scan & Push job running
#   Steps: Build image → Trivy scan → Push to Docker Hub → Update values file

# What just happened automatically?
#  1. GitHub saw your push
#  2. Started a runner (free Linux VM)
#  3. Built your Docker image
#  4. Trivy scanned it for security vulnerabilities (fails on CRITICAL/HIGH)
#  5. Pushed image to Docker Hub with a tag like "a1b2c3d4"
#  6. Updated gitops/dev/values-dev.yaml with the new tag
#  7. Committed and pushed that change back to GitHub

# ✅ CHECK: In GitHub, look at gitops/dev/values-dev.yaml
#   The image.tag should now be an 8-char SHA, not "latest"


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 6 — ARGO CD (GitOps)
# What it does: watches your Git repo and automatically keeps the cluster
#               in sync with whatever is in Git. Git = source of truth.
# ═══════════════════════════════════════════════════════════════════════════════

# 6a. Install Argo CD
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm install argocd argo/argo-cd \
  --namespace argocd \
  --set configs.params."server\.insecure"=true

# Wait for all pods to be Running (~2 minutes)
kubectl get pods -n argocd -w

# 6b. Get the admin password
kubectl get secret argocd-initial-admin-secret \
  -n argocd -o jsonpath="{.data.password}" | base64 -d
# Copy this password!

# 6c. Open the Argo CD UI
kubectl port-forward svc/argocd-server -n argocd 8080:80
# Open http://localhost:8080
# Username: admin   Password: (from above)

# 6d. Update the Argo CD application YAMLs with your details
sed -i "s|YOUR_GITHUB_USERNAME|$GITHUB_USERNAME|g" gitops/argocd-apps.yaml
sed -i "s|YOUR_DOCKERHUB_USERNAME|$DOCKERHUB_USERNAME|g" gitops/argocd-apps.yaml

# 6e. Apply the Argo CD applications (tells Argo WHAT to watch)
kubectl apply -f gitops/argocd-apps.yaml

# 6f. Go back to Argo CD UI at http://localhost:8080
#  You'll see 3 apps: devops101-dev, devops101-qa, devops101-prod
#  dev and qa will auto-sync. prod stays "OutOfSync" until you click Sync.

# What is GitOps?
#  Traditional: "kubectl apply" or "helm upgrade" run by a human or script
#  GitOps:      Argo CD watches Git, notices a change, applies it automatically
#               No human runs kubectl. Git is the only way to change the cluster.
#               This means: full audit trail, easy rollback (just revert a commit)

# 6g. Test GitOps in action — make a code change:
# Edit app/app.py — change something visible (e.g. add an emoji to the title)
git add app/app.py
git commit -m "feat: update title"
git push

# Watch what happens:
#  1. GitHub Actions builds new image, tags it with SHA, pushes to Docker Hub
#  2. GitHub Actions updates gitops/dev/values-dev.yaml with new SHA
#  3. Argo CD sees the values file changed
#  4. Argo CD runs helm upgrade in the dev namespace automatically
#  5. New pod starts, old pod stops — zero downtime rolling update

# ✅ FULL GITOPS CYCLE COMPLETE!


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL 7 — PROMOTE TO PROD (manual GitOps)
# ═══════════════════════════════════════════════════════════════════════════════

# 1. Find the image tag you want to promote (from GitHub Actions summary or Docker Hub)
NEW_TAG="a1b2c3d4"   # replace with your actual 8-char SHA

# 2. Update the prod values file
sed -i "s|  tag: \"SET_ME\"|  tag: \"${NEW_TAG}\"|" gitops/prod/values-prod.yaml
sed -i "s|  version: \"SET_ME\"|  version: \"${NEW_TAG}\"|" gitops/prod/values-prod.yaml

# 3. Commit and push
git add gitops/prod/values-prod.yaml
git commit -m "chore: promote ${NEW_TAG} to production"
git push

# 4. Go to Argo CD UI → devops101-prod → click SYNC button
#    Argo CD applies the new image tag to prod namespace
#    You'll see the red page updated with the new version

# ✅ CHECK all 3 environments are running:
kubectl get pods -A | grep devops101
kubectl get hpa   -A | grep devops101

# ═══════════════════════════════════════════════════════════════════════════════
# QUICK REFERENCE — commands you'll use daily
# ═══════════════════════════════════════════════════════════════════════════════

# Kubernetes
kubectl get pods -n dev                   # are pods running?
kubectl logs -n dev -l app=devops101      # see app logs
kubectl describe pod -n dev <name>        # why is pod crashing?
kubectl top pods -n dev                   # CPU/memory usage

# Helm
helm list -A                              # all releases
helm rollback devops101-dev 1 -n dev      # rollback

# Argo CD
kubectl port-forward svc/argocd-server -n argocd 8080:80   # open UI

# Docker
docker ps                                 # running containers
docker build -t test -f docker/Dockerfile ./app && docker run -p 5000:5000 test
