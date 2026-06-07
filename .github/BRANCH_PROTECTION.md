# Branch protection & release process

Settings to configure once in **GitHub → Settings → Branches → Add branch
ruleset** (or classic *Branch protection rules*) targeting `main`. This mirrors
the guardrails a production team would enforce.

## Required rules for `main`

- [x] **Require a pull request before merging**
  - [x] Require approvals: **1** (or more)
  - [x] **Require review from Code Owners** (uses [`CODEOWNERS`](./CODEOWNERS))
  - [x] Dismiss stale approvals when new commits are pushed
- [x] **Require status checks to pass before merging**
  - Required check: **`Lint & build`** (the `ci` job in
    [`workflows/ci-deploy.yml`](./workflows/ci-deploy.yml))
  - [x] Require branches to be up to date before merging
- [x] **Require conversation resolution before merging**
- [x] **Do not allow bypassing the above settings** (applies to admins too)
- [x] **Restrict who can push to matching branches** — no direct pushes; all
      changes land via PR
- [x] **Block force pushes** and **deletions**

## Protected deploy environment

In **Settings → Environments → `production`**:

- [x] **Required reviewers** — at least one approver before the `deploy` job runs
- [x] **Deployment branches** — restrict to `main` only
- [x] Store deploy secrets (`INSFORGE_ACCESS_TOKEN`, etc.) **on the environment**,
      not as plain repo secrets, so they're only exposed to approved deploys

## Workflow

1. Branch off `main` → open a PR.
2. CI (`Lint & build`) must pass; Code Owners must approve.
3. Merge to `main` → the `deploy` job waits for `production` environment approval,
   then rolls the InsForge compute service to the new SHA-pinned image and runs a
   post-deploy health check.

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
