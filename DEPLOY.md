# Deploying the Dash app

The Dash app (`dashboard/app.py`) runs on Cloud Run. The Streamlit app keeps deploying from
`main` on Streamlit Community Cloud as before.

| | |
|---|---|
| Cloud Run service | `beauty-pulse` |
| Region | `asia-northeast1` |
| Image | `asia-northeast1-docker.pkg.dev/<PROJECT_ID>/beauty-pulse/dashboard:<short SHA>` |
| Build | `cloudbuild.yaml`, run by a Cloud Build trigger on pushes to `main` |

`cloudbuild.yaml` is the source of truth for the service's settings: memory, CPU, instance
limits and public access are flags on its deploy step. A setting changed in the console is
overwritten by the next deploy. Change it in the file instead.

Each push to `main` runs the test suite, then builds, pushes and deploys. Red tests stop the
deploy.

## One-time setup

In a terminal with the gcloud CLI. `--project` is passed on every command so the CLI's default
project is left alone.

```zsh
PROJECT=<project-id>          # unique across Google Cloud, e.g. beauty-pulse-ss

# 1. Project and billing
gcloud projects create "$PROJECT" --name="Beauty Pulse"
gcloud billing accounts list
gcloud billing projects link "$PROJECT" --billing-account=<ACCOUNT_ID>

# 2. APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com \
  artifactregistry.googleapis.com compute.googleapis.com --project "$PROJECT"

# 3. Roles for the service account the build runs as
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
for role in roles/run.admin roles/iam.serviceAccountUser roles/artifactregistry.writer roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$SA" \
    --role="$role" --condition=None
done

# 4. The image repository
gcloud artifacts repositories create beauty-pulse --repository-format=docker \
  --location=asia-northeast1 --project "$PROJECT"
```

5. **Trigger, in the console.** Connecting GitHub needs a browser sign-in.
   - Cloud Build → Triggers → Connect repository → GitHub → `Stan-DS-Z/beauty-pulse`.
   - Create a trigger: event "Push to a branch", branch `^main$`, configuration `cloudbuild.yaml`.
   - Service account: the Compute Engine default (`…-compute@developer.gserviceaccount.com`).

About step 3: projects created now run Cloud Build as the Compute Engine default service
account, not the older Cloud Build account. It needs Cloud Run Admin and Service Account User to
deploy, Artifact Registry Writer to push the image, and Logs Writer because the trigger names
the account.

Google's pages:
- [Creating projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- [Linking billing](https://cloud.google.com/billing/docs/how-to/modify-project)
- [Enabling APIs](https://cloud.google.com/service-usage/docs/enable-disable)
- [Deploying to Cloud Run with Cloud Build, "Grant permissions"](https://cloud.google.com/build/docs/quickstart-deploy)
- [The Cloud Build service account change](https://cloud.google.com/build/docs/cloud-build-service-account-updates)
- [Creating an Artifact Registry repository](https://cloud.google.com/artifact-registry/docs/repositories/create-repos)
- [Building from GitHub](https://cloud.google.com/build/docs/automating-builds/github/build-repos-from-github)

## Checking a deploy

```zsh
curl -s https://<service-url>/version
# {"version": "<short SHA>", "trends_to": "2026-06", "launches_to": "2026-08"}
```

`version` is the commit the image was built from; it should match the pushed SHA.
`trends_to` and `launches_to` are the last months of the Trends and launch data inside
the image.

## Cold start

Measured against `/shift`, after at least 15 minutes idle for each cold sample:
`curl -o /dev/null -s -w '%{time_starttransfer}\n' https://<service-url>/shift`.

| Date | Cold (s) | Warm (s) | Min instances |
|---|---|---|---|
| — | — | — | 0 |

See [minimum instances](https://cloud.google.com/run/docs/configuring/min-instances) for what
keeping an instance warm changes.
