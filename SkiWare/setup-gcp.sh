#!/usr/bin/env bash
#
# setup-gcp.sh — One-time GCP bootstrap for CI/CD with GitHub Actions
#
# Uses Workload Identity Federation (no JSON key files!) so you avoid
# the service-account-key headaches in Cloud Shell.
#
# Usage:
#   chmod +x setup-gcp.sh
#   ./setup-gcp.sh <GCP_PROJECT_ID> <GITHUB_ORG/REPO>
#
# Example:
#   ./setup-gcp.sh my-cool-project myuser/gcp-hello-world
#
set -euo pipefail

# ── Args ────────────────────────────────────────────────────────────
PROJECT_ID="${1:?Usage: $0 <PROJECT_ID> <GITHUB_ORG/REPO>}"
GITHUB_REPO="${2:?Usage: $0 <PROJECT_ID> <GITHUB_ORG/REPO>}"
REGION="us-central1"
SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"
REPO_NAME="cloud-run-apps"

echo "══════════════════════════════════════════════════════════════"
echo "  GCP Project:   $PROJECT_ID"
echo "  GitHub Repo:   $GITHUB_REPO"
echo "  Region:        $REGION"
echo "══════════════════════════════════════════════════════════════"
echo ""

# ── Set project ─────────────────────────────────────────────────────
gcloud config set project "$PROJECT_ID"

# ── Enable required APIs ────────────────────────────────────────────
echo "→ Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com

# ── Create Artifact Registry repo ──────────────────────────────────
echo "→ Creating Artifact Registry repository..."
gcloud artifacts repositories describe "$REPO_NAME" \
  --location="$REGION" 2>/dev/null || \
gcloud artifacts repositories create "$REPO_NAME" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Cloud Run container images"

# ── Create Service Account ──────────────────────────────────────────
echo "→ Creating service account..."
gcloud iam service-accounts describe "$SA_EMAIL" 2>/dev/null || \
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="GitHub Actions Deployer"

echo "→ Waiting for service account to propagate..."
sleep 15

# ── Grant roles ─────────────────────────────────────────────────────
echo "→ Granting IAM roles..."
for ROLE in \
  roles/run.admin \
  roles/artifactregistry.writer \
  roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --condition=None \
    --quiet
done

# ── Workload Identity Federation ────────────────────────────────────
echo "→ Setting up Workload Identity Federation..."

# Create pool (idempotent check)
gcloud iam workload-identity-pools describe "$POOL_NAME" \
  --location="global" 2>/dev/null || \
gcloud iam workload-identity-pools create "$POOL_NAME" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create OIDC provider
gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
  --workload-identity-pool="$POOL_NAME" \
  --location="global" 2>/dev/null || \
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --workload-identity-pool="$POOL_NAME" \
  --location="global" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GITHUB_REPO}'"

# Allow the GitHub repo to impersonate the SA
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/$(
    gcloud iam workload-identity-pools describe "$POOL_NAME" \
      --location="global" --format="value(name)"
  )/attribute.repository/${GITHUB_REPO}" \
  --quiet

# ── Print GitHub Secrets ────────────────────────────────────────────
WIF_PROVIDER=$(gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
  --workload-identity-pool="$POOL_NAME" \
  --location="global" \
  --format="value(name)")

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  ✅  DONE! Add these as GitHub Repository Secrets:"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  GCP_PROJECT_ID       = $PROJECT_ID"
echo "  WIF_PROVIDER         = $WIF_PROVIDER"
echo "  WIF_SERVICE_ACCOUNT  = $SA_EMAIL"
echo ""
echo "  Go to: https://github.com/${GITHUB_REPO}/settings/secrets/actions"
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Then just push to 'main' and GitHub Actions will build"
echo "  and deploy to Cloud Run automatically!"
echo "══════════════════════════════════════════════════════════════"
