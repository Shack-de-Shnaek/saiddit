#!/bin/sh
# One-time local setup (jenkins/README.md, steps 1 and 2): creates the kind
# cluster with ingress-nginx and metrics-server, writes the kubeconfig Jenkins
# needs, starts Jenkins and prints its initial admin password. Safe to re-run.
#
#   ./setup.sh
set -eu

cd "$(dirname "$0")"

cluster=saiddit
ctx="kind-$cluster"
kubeconfig=/tmp/kind-internal.kubeconfig

echo '==> kind cluster'
if kind get clusters | grep -qx "$cluster"; then
    echo "cluster '$cluster' already exists"
else
    kind create cluster --config k8s/kind/cluster.yaml
fi

echo '==> ingress-nginx'
kubectl --context "$ctx" apply -f k8s/kind/ingress-nginx.yaml
kubectl --context "$ctx" -n ingress-nginx wait --for=condition=ready pod \
    -l app.kubernetes.io/component=controller --timeout=180s

# Without it the frontend/backend HPAs report <unknown> CPU and never scale.
echo '==> metrics-server'
kubectl --context "$ctx" apply -f k8s/kind/metrics-server.yaml
kubectl --context "$ctx" -n kube-system rollout status deployment/metrics-server --timeout=180s

echo "==> kubeconfig for Jenkins -> $kubeconfig"
kind get kubeconfig --internal --name "$cluster" > "$kubeconfig"

echo '==> Jenkins'
docker compose -f jenkins/compose.yaml up -d --build

# Only exists until the setup wizard is completed, and takes a moment on first boot.
password_file=/var/jenkins_home/secrets/initialAdminPassword
password=''
for _ in $(seq 60); do
    if password=$(docker compose -f jenkins/compose.yaml exec -T jenkins cat "$password_file" 2>/dev/null); then
        break
    fi
    sleep 2
done

cat <<EOF

Done. Remaining manual steps (jenkins/README.md, step 2):
  1. Open http://localhost:8081 and unlock with: ${password:-<already set up, or not ready yet>}
  2. "Select plugins -> None", create the admin user.
  3. Add credentials 'dockerhub' (username + access token) and
     'kubeconfig' (secret file: $kubeconfig).
  4. Create the Pipeline job from SCM (Jenkinsfile) and click Build Now.
EOF
