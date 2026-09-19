# CI/CD: Jenkins → Docker Hub → kind

Every push to `master` (polled every ~2 min) builds `saiddit-backend`,
`saiddit-frontend` and `saiddit-garage-init`, pushes them to Docker Hub as
`<user>/saiddit-<name>:<short-sha>` and `:latest`, then applies `k8s/` to the
kind cluster (namespace `saiddit`) with the new tag.

## 1. Cluster

```sh
kind create cluster --config k8s/kind/cluster.yaml
kubectl apply -f https://kind.sigs.k8s.io/examples/ingress/deploy-ingress-nginx.yaml
kubectl -n ingress-nginx wait --for=condition=ready pod -l app.kubernetes.io/component=controller --timeout=180s
kind get kubeconfig --internal --name saiddit > /tmp/kind-internal.kubeconfig
```

## 2. Jenkins

```sh
docker compose -f jenkins/compose.yaml up -d --build
docker compose -f jenkins/compose.yaml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open http://localhost:8081, paste the password, pick "Select plugins → None"
(the needed ones are preinstalled), create the admin user.

**Manage Jenkins → Credentials → System → Global → Add credentials:**

| ID           | Kind                  | Value                                         |
|--------------|-----------------------|-----------------------------------------------|
| `dockerhub`  | Username with password | Docker Hub username + access token (Read & Write) |
| `kubeconfig` | Secret file           | `/tmp/kind-internal.kubeconfig`               |

**New Item → Pipeline →** Definition "Pipeline script from SCM", Git,
repo `https://github.com/Shack-de-Shnaek/saiddit.git` (add GitHub credentials
if the repo is private), branch `*/master`, script path `Jenkinsfile`.
Click **Build Now** once; after that the `pollSCM` trigger picks up pushes.

## 3. Demo

```sh
kubectl -n saiddit get all,ingress,pvc,configmap,secret
kubectl -n saiddit get pods -o wide
curl -i http://saiddit.localhost/api/docs
```

Open http://saiddit.localhost in the browser.

Manual deploy without Jenkins: `k8s/render.sh <dockerhub-user> latest | kubectl apply -f -`.
