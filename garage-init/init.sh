#!/bin/sh
# Provisions the local Garage cluster the backend stores uploads in: assigns
# the node a role, creates the bucket, imports the S3 key and grants it access.
#
# Runs on every `docker compose up`; each step is skipped once it is done, so
# repeat runs are no-ops. The container shares garage's network namespace, so
# the CLI reaches the node over 127.0.0.1, exactly as garage.toml expects.
set -eu

: "${AWS_ACCESS_KEY_ID:?is required}"
: "${AWS_SECRET_ACCESS_KEY:?is required}"
: "${AWS_STORAGE_BUCKET_NAME:?is required}"

ZONE="${GARAGE_ZONE:-dc1}"
CAPACITY="${GARAGE_CAPACITY:-1G}"
KEY_NAME="${GARAGE_KEY_NAME:-$AWS_STORAGE_BUCKET_NAME}"

echo "garage-init: waiting for the node to answer"
until garage status >/dev/null 2>&1; do
    sleep 1
done

# Every bucket and key call fails with 'Layout not ready' until the node has
# been given a role, which makes it the check for a never-provisioned cluster.
if ! garage bucket list >/dev/null 2>&1; then
    node_id="$(garage node id -q | cut -d@ -f1)"
    echo "garage-init: assigning layout to ${node_id} (zone ${ZONE}, capacity ${CAPACITY})"
    garage layout assign -z "$ZONE" -c "$CAPACITY" "$node_id"
    # A fresh cluster is at version 0, so the first applied layout is 1.
    garage layout apply --version 1

    echo "garage-init: waiting for the layout to settle"
    until garage bucket list >/dev/null 2>&1; do
        sleep 1
    done
fi

if garage bucket info "$AWS_STORAGE_BUCKET_NAME" >/dev/null 2>&1; then
    echo "garage-init: bucket ${AWS_STORAGE_BUCKET_NAME} already exists"
else
    echo "garage-init: creating bucket ${AWS_STORAGE_BUCKET_NAME}"
    garage bucket create "$AWS_STORAGE_BUCKET_NAME"
fi

if garage key info "$AWS_ACCESS_KEY_ID" >/dev/null 2>&1; then
    echo "garage-init: key ${AWS_ACCESS_KEY_ID} already imported"
else
    echo "garage-init: importing key ${AWS_ACCESS_KEY_ID}"
    garage key import --yes -n "$KEY_NAME" "$AWS_ACCESS_KEY_ID" "$AWS_SECRET_ACCESS_KEY"
fi

# Granting rights that are already granted changes nothing.
garage bucket allow --read --write --owner "$AWS_STORAGE_BUCKET_NAME" --key "$AWS_ACCESS_KEY_ID"

# Website mode is what lets anonymous readers fetch objects, which is how the
# browser gets an unsigned, environment-independent URL for an upload.
if [ "${GARAGE_BUCKET_PUBLIC:-true}" = "true" ]; then
    echo "garage-init: exposing ${AWS_STORAGE_BUCKET_NAME} publicly"
    garage bucket website --allow "$AWS_STORAGE_BUCKET_NAME"
else
    echo "garage-init: leaving ${AWS_STORAGE_BUCKET_NAME} private"
fi

echo "garage-init: ready — ${AWS_STORAGE_BUCKET_NAME} is writable by ${AWS_ACCESS_KEY_ID}"
