# K8S Deploy Guide

This directory contains the base Kubernetes manifests used by the GitHub Actions deploy workflow.

## Image publishing

Images are published to GHCR by `.github/workflows/publish-images.yml`:

- `ghcr.io/<owner>/ai-control-backend`
- `ghcr.io/<owner>/ai-control-frontend`
- `ghcr.io/<owner>/ai-control-mock-prometheus`

Published tags:

- `latest` on `main`
- `sha-<commit>`

## GitHub Environment variables

Create GitHub Environments such as `staging` and `production`, then configure:

### Variables

- `FRONTEND_ORIGIN`
- `JWT_ACCESS_TTL_MINUTES`
- `JWT_REFRESH_TTL_DAYS`
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_DEFAULT_TENANT_NAME`
- `BOOTSTRAP_DEFAULT_TENANT_SLUG`
- `PROMETHEUS_BASE_URL`
- `PROMETHEUS_TIMEOUT`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`

### Secrets

- `KUBE_CONFIG`
  - base64 encoded kubeconfig
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `BOOTSTRAP_ADMIN_PASSWORD`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `GHCR_USERNAME`
- `GHCR_TOKEN`

## Deployment

Run `.github/workflows/deploy-k8s.yml` manually with:

- `environment`: `staging` or `production`
- `namespace`: target namespace, default `ai-monitor`
- `image_tag`: `latest` or a published `sha-...` tag

The workflow will:

- ensure the namespace exists
- create/update the GHCR pull secret
- create/update ConfigMap and Secret from GitHub Environment values
- apply the base manifests
- set backend/frontend images to the requested tag
- wait for rollout completion
