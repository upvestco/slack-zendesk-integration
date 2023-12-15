# GCP Setup

I guess you could consider this file "Terraform pseudo-code", somewhat. ;-) Or, how about "Brain-dump of a Terraform-illiterate person"?

## Cloud Run

We have 1 Cloud Run service "slack-zendesk-int": https://console.cloud.google.com/run/detail/europe-west3/slack-zendesk-int/metrics?project=zendesk-int-381915 .

It gets deployed from a GHA, like this:

```shell
gcloud run deploy \
    --project=zendesk-int-381915 \
    --region=europe-west3 \
    --image=eu.gcr.io/zendesk-int-381915/slack-zendesk-int:${GIT_HASH} \
    --platform=managed \
    --ingress=all \
    --allow-unauthenticated \
    --timeout=30 \
    --min-instances=1 \
    --max-instances=1 \
    --cpu=1 \
    --memory=512Mi \
    --execution-environment=gen1 \
    --set-cloudsql-instances=zendesk-int-381915:europe-west3:slack-zendesk-integration-state \
    --set-secrets=SLACK_CLIENT_ID=upvest-escalations-slack-client-id:latest,SLACK_CLIENT_SECRET=upvest-escalations-slack-client-secret:latest,SLACK_SIGNING_SECRET=upvest-escalations-slack-signing-secret:latest,POSTGRES_PASSWORD=upvest-escalations-postgres-password:latest \
    --set-env-vars=POSTGRES_HOST=/cloudsql/zendesk-int-381915:europe-west3:slack-zendesk-integration-state,POSTGRES_PORT=5432,POSTGRES_USER=postgres,POSTGRES_DATABASE=state \
    --service-account=cloud-runner-784@zendesk-int-381915.iam.gserviceaccount.com \
    --description="Upvest escalations Slack App, integrated with Zendesk" \
    slack-zendesk-int
```



## Secrets

We have 4 Secrets, they contain the credentials for the [Upvest escalations Slack App](https://api.slack.com/apps/A04R5GPMZ2T) and a password for the [database](https://console.cloud.google.com/sql/instances/slack-zendesk-integration-state/overview?project=zendesk-int-381915).

The values for the Slack credentials can be found [here](https://api.slack.com/apps/A04R5GPMZ2T/general).

The DB password is also [in 1password](https://start.1password.com/open/i?a=LRYSLLDT6REF3EBM4T7IXCC2II&v=tol3fz3lhaw725i2rboi5fpfby&i=frinfjawgpskvmmmet33o2av3y&h=upvest.1password.com).

- https://console.cloud.google.com/security/secret-manager/secret/upvest-escalations-slack-client-id/versions?project=zendesk-int-381915
- https://console.cloud.google.com/security/secret-manager/secret/upvest-escalations-slack-client-secret/versions?project=zendesk-int-381915
- https://console.cloud.google.com/security/secret-manager/secret/upvest-escalations-slack-signing-secret/versions?project=zendesk-int-381915
- https://console.cloud.google.com/security/secret-manager/secret/upvest-escalations-postgres-password/versions?project=zendesk-int-381915



## Service Accounts

We have 2 Service Accounts:


### cloud-runner-784@zendesk-int-381915.iam.gserviceaccount.com

https://console.cloud.google.com/iam-admin/serviceaccounts/details/106178929943731079581?project=zendesk-int-381915

The Cloud Run instance is running as this SA. I was prompted to create an SA specifically to include the "Secret Manager Secret Accessor" role, since the Cloud Run instance needs to read 2 GCP secrets which contain the credentials for the Slack App.

Roles:

- Cloud Run Service Agent
- Secret Manager Secret Accessor


### image-pusher-and-run-deployer@zendesk-int-381915.iam.gserviceaccount.com

https://console.cloud.google.com/iam-admin/serviceaccounts/details/107035969383200572101?project=zendesk-int-381915

This Service Account is a vehicle to allow Docker image pushing and Cloud Run deployment, both triggered from a Github Action, via Workload Identity Federation.

Roles:

- Cloud Run Developer
- Cloud Run Invoker: Possibly not needed, I'm not 100% sure though.
- Container Registry Service Agent
- Service Account User: Possibly not needed, I'm not 100% sure though.
- Workload Identity User

- Docker Image Pusher Storage Access: This is a CUSTOM ROLE! Originally I was prompted to grant the ["Storage Legacy Bucket Writer"](https://console.cloud.google.com/iam-admin/roles/details/roles%3Cstorage.legacyBucketWriter?project=zendesk-int-381915) role as per these [GCP docs](https://cloud.google.com/container-registry/docs/access-control#permissions_and_roles), but was not allowed (?) to grant that to an SA. So I copied the same set of permissions into a custom role (see below).

This Service Account had a IAM policy binding applied to enable Workload Identity Federation (see below).



## Workload Identity Federation

This Workload Identity Pool & Provider enable us to deploy directly to GCP from within a Github Action (GHA).

https://console.cloud.google.com/iam-admin/workload-identity-pools/pool/push-and-deploy-from-gha?project=zendesk-int-381915

### Workload Identity Pool

```shell
gcloud iam workload-identity-pools create "push-and-deploy-from-gha" \
  --project="zendesk-int-381915" \
  --location="global" \
  --display-name="Push and Deploy from GHA"
```


### Workload Identity Provider

```shell
gcloud iam workload-identity-pools providers create-oidc “github-actions”  \
  --location="global"  \
  --project="zendesk-int-381915" \
  --workload-identity-pool="push-and-deploy-from-gha"  \
  --display-name="Github Actions"  \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner,attribute.actor=assertion.actor,attribute.aud=assertion.aud" \
  --issuer-uri="https://token.actions.githubusercontent.com"   
```


### Workload Identity Access Grants (a.k.a. IAM Policy Binding)

This Workload Identity Pool was granted permission to act as the "Image Pusher And Run Deployer" Service Account, but limited to access originating from the `toknapp/slack-zendesk-int` Github repo:

```shell
gcloud iam service-accounts add-iam-policy-binding "image-pusher-and-run-deployer@zendesk-int-381915.iam.gserviceaccount.com" \
  --project="zendesk-int-381915" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/371520436899/locations/global/workloadIdentityPools/push-and-deploy-from-gha/attribute.repository/toknapp/slack-zendesk-int"
```



## Custom Role

This Custom Role was created because I found myself not allowed to assign the "Storage Legacy Bucket Writer" Role to a Service Account. So I copied the "Storage Legacy Bucket Writer" Role with the same exact permissions set. I called it "Docker Image Pusher Storage Access". I then was allowed to assign that copied Role to a Service Account without any problems.

https://console.cloud.google.com/iam-admin/roles/details/projects%3Czendesk-int-381915%3Croles%3CDockerImagePusherStorageAccess?project=zendesk-int-381915

Permissions:

- storage.buckets.get
- storage.multipartUploads.abort
- storage.multipartUploads.create
- storage.multipartUploads.list
- storage.multipartUploads.listParts
- storage.objects.create
- storage.objects.delete
- storage.objects.list



## Epilogue

> I hope I didn't forget anything.

... Yeah, that's why we have Terraform, right?

