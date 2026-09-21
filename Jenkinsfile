// Builds the images, pushes them to Docker Hub and rolls them out to the
// kind cluster. Needs two Jenkins credentials (see jenkins/README.md):
//   dockerhub  - username/password (Docker Hub user + access token)
//   kubeconfig - secret file (`kind get kubeconfig --internal --name saiddit`)
pipeline {
    agent any

    // Jenkins runs locally, so GitHub can't reach it with a webhook: poll instead.
    triggers { pollSCM('H/2 * * * *') }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    // API_URL comes from the Jenkins process environment (set on the container
    // in jenkins/compose.yaml). Vite bakes it into the bundle, so it must be the
    // host the Ingress serves.
    environment {
        IMAGES = 'backend frontend garage-init'
    }

    stages {
        stage('Build') {
            steps {
                script {
                    env.TAG = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                }
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    sh '''
                        : "${API_URL:?API_URL is not set in the Jenkins environment}"
                        docker build --target hosting -t "$DOCKERHUB_USER/saiddit-backend:$TAG" backend
                        docker build --target hosting --build-arg VITE_API_URL="$API_URL" -t "$DOCKERHUB_USER/saiddit-frontend:$TAG" frontend
                        docker build -t "$DOCKERHUB_USER/saiddit-garage-init:$TAG" garage-init
                    '''
                }
            }
        }

        stage('Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    sh '''
                        echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin
                        for img in $IMAGES; do
                            docker tag "$DOCKERHUB_USER/saiddit-$img:$TAG" "$DOCKERHUB_USER/saiddit-$img:latest"
                            docker push "$DOCKERHUB_USER/saiddit-$img:$TAG"
                            docker push "$DOCKERHUB_USER/saiddit-$img:latest"
                        done
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN'),
                    file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG'),
                ]) {
                    sh '''
                        k8s/render.sh "$DOCKERHUB_USER" "$TAG" | kubectl apply -f -
                        kubectl -n saiddit rollout status statefulset/postgres --timeout=300s
                        kubectl -n saiddit rollout status deployment/backend --timeout=300s
                        kubectl -n saiddit rollout status deployment/frontend --timeout=300s
                    '''
                }
            }
        }
    }

    post {
        always { sh 'docker logout || true' }
    }
}
