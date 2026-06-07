# Branch protection & release process

Settings to configure once in **GitHub → Settings → Branches → Add branch
ruleset** (or classic *Branch protection rules*) targeting `main`. This mirrors
the guardrails a production team would enforce.

## Required rules for `main`

- [x] **Require a pull request before merging**
  - [x] Require approvals: **1** (or more)
  - [x] **Require review from Code Owners** (uses [`CODEOWNERS`](./CODEOWNERS))
  - [x] Dismiss stale approvals when new commits are pushed
- [x] **Require status checks to pass before merging** — both app CIs:
  - **`Agent service build`** — [`workflows/agent-service.yml`](./workflows/agent-service.yml)
  - **`Frontend build`** — [`workflows/frontend.yml`](./workflows/frontend.yml)
  - [x] Require branches to be up to date before merging
- [x] **Require conversation resolution before merging**
- [x] **Do not allow bypassing the above settings** (applies to admins too)
- [x] **Restrict who can push to matching branches** — no direct pushes; all
      changes land via PR
- [x] **Block force pushes** and **deletions**

## Two pipelines (one per app)

| App | Workflow | CI job | Deploy target |
|---|---|---|---|
| Backend | `agent-service.yml` | `Agent service build` | InsForge Compute (Fly) — image rolled via `compute update` |
| Frontend | `frontend.yml` | `Frontend build` | InsForge Deployments (Vercel) via `deployments deploy` |

Each pipeline: **CI runs automatically** on push/PR; **deploy is manual**
(`workflow_dispatch` → "Run workflow"), gated by the `production` environment.

## Protected deploy environment

In **Settings → Environments → `production`** (shared by both pipelines' deploy jobs):

- [x] **Deployment branches** — restrict to `main` only
- [x] Store deploy secrets on the environment, not as plain repo secrets, so
      they're only exposed to approved deploys:
      `INSFORGE_EMAIL`, `INSFORGE_PASSWORD`, `INSFORGE_PROJECT_ID`,
      `INSFORGE_ORG_ID`, `INSFORGE_API_SERVICE_ID`
- [ ] **Required reviewers** — paid feature on private repos; on the free plan
      the manual `workflow_dispatch` trigger is the approval gate instead.

## Workflow

1. Branch off `main` → open a PR.
2. Both CIs (`Agent service build`, `Frontend build`) must pass; Code Owners must approve.
3. Merge to `main`.
4. To release: open **Actions → the app's workflow → Run workflow → main**.
   - Agent Service: builds + pushes the image, rolls the compute service, health-checks.
   - Frontend: builds + deploys to Vercel via InsForge.

## Private container images (optional hardening)

The pipeline pushes images to **GHCR** and rolls the service with
`compute update --image` (which preserves the service's existing env/secrets).
To keep images private instead of public:

1. Leave the GHCR packages **private** (default).
2. Create a **read-only** GitHub PAT with `read:packages` scope.
3. Contact **InsForge support** to register that PAT as the project's pull
   credential for `ghcr.io` (there is no CLI flag for this today).

Once InsForge has the pull credential, the existing workflow works unchanged
against private images — no edits required.

> Alternative: source-mode deploy (`compute deploy .`) keeps images in InsForge's
> own private `registry.fly.io` with no GHCR at all, but it does not guarantee
> preservation of existing service env vars on redeploy, so it's avoided here to
> protect production secrets.
