#!/bin/sh
# Prints every manifest in k8s/ with the image placeholders filled in, ready
# for `kubectl apply -f -`.
#
#   k8s/render.sh <dockerhub-user> [tag] | kubectl apply -f -
set -eu

user="${1:?usage: render.sh <dockerhub-user> [tag]}"
tag="${2:-latest}"

for f in "$(dirname "$0")"/*.yaml; do
    sed -e "s#DOCKERHUB_USER#$user#g" -e "s#IMAGE_TAG#$tag#g" "$f"
    echo '---'
done
