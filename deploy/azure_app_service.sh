#!/usr/bin/env bash
set -euo pipefail

# FIEL API deployment for Azure Cloud Shell.
# The defaults target the hackathon resources already validated on 2026-10-23.
SUBSCRIPTION_ID="${FIEL_SUBSCRIPTION_ID:-c3839efa-b8cb-402a-b405-536ee5bc5d64}"
RESOURCE_GROUP="${FIEL_RESOURCE_GROUP:-fiel-rg}"
LOCATION="${FIEL_LOCATION:-australiaeast}"
FOUNDRY_ACCOUNT="${FIEL_FOUNDRY_ACCOUNT:-fiel-foundry}"
FOUNDRY_DEPLOYMENT="${FOUNDRY_DEPLOYMENT:-gpt-5-mini}"
APP_SERVICE_PLAN="${FIEL_APP_SERVICE_PLAN:-fiel-api-free-plan}"
APP_NAME="${FIEL_APP_NAME:-fiel-api-c3839e}"
PACKAGE="/tmp/fiel-api-deploy.zip"

command -v az >/dev/null || { echo "Azure CLI (az) is required." >&2; exit 1; }
command -v git >/dev/null || { echo "git is required." >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required." >&2; exit 1; }

az account set --subscription "$SUBSCRIPTION_ID"
az group show --name "$RESOURCE_GROUP" --output none

echo "Deploying FIEL API to Azure App Service"
echo "  resource group: $RESOURCE_GROUP"
echo "  region:         $LOCATION"
echo "  app:            $APP_NAME"

if ! az appservice plan show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_SERVICE_PLAN" \
  --output none 2>/dev/null; then
  az appservice plan create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_SERVICE_PLAN" \
    --location "$LOCATION" \
    --sku F1 \
    --is-linux \
    --output none
fi

if ! az webapp show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --output none 2>/dev/null; then
  az webapp create \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$APP_SERVICE_PLAN" \
    --name "$APP_NAME" \
    --runtime "PYTHON:3.12" \
    --output none
fi

az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --startup-file "python -m uvicorn fiel.api:app --host 0.0.0.0 --port 8000" \
  --output none

# Fetch the Foundry key inside Azure and send it straight to the App Service
# configuration. The value is never printed or written into the repository.
FOUNDRY_API_KEY="$(az cognitiveservices account keys list \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FOUNDRY_ACCOUNT" \
  --query key1 \
  --output tsv)"

if [[ -z "$FOUNDRY_API_KEY" ]]; then
  echo "Could not read the Foundry key." >&2
  exit 1
fi

az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    ENABLE_ORYX_BUILD=true \
    PYTHONUNBUFFERED=1 \
    FOUNDRY_ENDPOINT="https://${FOUNDRY_ACCOUNT}.openai.azure.com/openai/v1" \
    FOUNDRY_DEPLOYMENT="$FOUNDRY_DEPLOYMENT" \
    FOUNDRY_API_KEY="$FOUNDRY_API_KEY" \
  --output none
unset FOUNDRY_API_KEY

git archive --format=zip --output "$PACKAGE" HEAD

az webapp deploy \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --src-path "$PACKAGE" \
  --type zip \
  --clean true \
  --restart true \
  --async false \
  --output none

BASE_URL="https://${APP_NAME}.azurewebsites.net"
echo "Waiting for $BASE_URL/health"

for attempt in $(seq 1 30); do
  if HEALTH="$(curl --fail --silent --show-error "$BASE_URL/health" 2>/dev/null)"; then
    echo "Health check passed: $HEALTH"
    echo "API docs: $BASE_URL/docs"
    exit 0
  fi
  sleep 10
done

echo "Deployment finished, but the health endpoint was not ready in five minutes." >&2
echo "Inspect logs with:" >&2
echo "az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME" >&2
exit 1
