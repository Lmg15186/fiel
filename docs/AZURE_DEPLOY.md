# Deploy the FIEL API to Azure

The judge-facing web experience remains on GitHub Pages. The FastAPI service can
run separately on Azure App Service so the public deployment exposes `/health`,
`/matches`, receipts and the OpenAPI documentation.

## Cost guardrail

The deployment script requests an **F1 Free** Linux App Service plan. Before
continuing, confirm that the Azure portal shows the plan as Free. If the
subscription cannot create F1, stop and review the offered SKU instead of
silently choosing a paid tier.

## Deploy from Azure Cloud Shell

Open Bash in Azure Cloud Shell and run:

```bash
git clone https://github.com/Lmg15186/fiel.git
cd fiel
bash deploy/azure_app_service.sh
```

The script is safe to run again. It deploys to the subscription currently
selected in Cloud Shell (`az account show`); to target another one, set
`FIEL_SUBSCRIPTION_ID=<id>` before running it. No subscription or tenant id is
stored in the repository. It:

1. confirms the subscription in use and that `fiel-rg` exists;
2. reuses `fiel-rg` and `fiel-foundry`;
3. creates or reuses an F1 Linux App Service plan;
4. creates or reuses the FIEL API web app;
5. transfers the Foundry key directly into protected App Service settings;
6. deploys only Git-tracked files, so `.env` is never uploaded;
7. waits for `/health` and prints the `/docs` URL.

The default public hostname is:

```text
https://fiel-api-c3839e.azurewebsites.net
```

Override the globally unique app name if necessary:

```bash
FIEL_APP_NAME=fiel-api-your-unique-name bash deploy/azure_app_service.sh
```

## Validate

```bash
curl --fail https://fiel-api-c3839e.azurewebsites.net/health
curl --fail https://fiel-api-c3839e.azurewebsites.net/matches
```

Open `https://fiel-api-c3839e.azurewebsites.net/docs` for Swagger UI.

## Security

- Never paste the Foundry key into chat, screenshots or GitHub.
- `.env` is ignored and the deployment archive is created with `git archive`.
- The script suppresses Azure command output while configuring secrets.
- Rotate the key in Azure if it is ever disclosed.

## Remove the API hosting resources

This removes the web app and its App Service plan but preserves Foundry and the
rest of `fiel-rg`:

```bash
az webapp delete --resource-group fiel-rg --name fiel-api-c3839e
az appservice plan delete --resource-group fiel-rg --name fiel-api-free-plan --yes
```
