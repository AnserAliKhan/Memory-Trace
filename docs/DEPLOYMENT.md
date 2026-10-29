# Deployment: production, PR previews and UAT

Everything here is free. Only the **frontend** is hosted, on Cloudflare Pages. The backend
(torch + ML models, ~1.5–2 GB RAM) is too heavy for free hosting, so **every tester runs the
backend on their own machine** and the hosted page talks to `http://localhost:8000`. That fits
ReFound being local-first.

## The three environments

| Environment | URL | Built from | Purpose |
|---|---|---|---|
| Production | `https://<project>.pages.dev` | `main` | Stable app |
| PR preview | `https://<branch>.<project>.pages.dev` (link is posted on the PR) | the PR's branch | Test one PR on its own |
| UAT | `https://uat.<project>.pages.dev` | the `uat` branch | Test **all open PRs together** before merging |

`<project>` is the Cloudflare Pages project subdomain (see setup).

### How UAT works
The **UAT** workflow (`.github/workflows/uat.yml` → `.github/scripts/assemble_uat.py`) rebuilds
the `uat` branch whenever a PR is opened, pushed, closed, marked ready or draft, or labelled, and
whenever `main` changes:

1. Start from `main`.
2. Take every **eligible** open PR into `main`: non-draft PRs from the owner or collaborators.
   PRs from forks need a maintainer to add the **`uat`** label. A new push to a fork PR removes
   the label, so it has to be re-reviewed and re-labelled.
3. Skip any PR that conflicts with `main` by itself. It needs to merge `main` first.
4. Merge the rest **oldest push first**. Where two PRs change the same lines, the **most recently
   pushed PR wins**. Conflicts git can't settle that way (one PR deletes or renames a file the
   other edits) skip the later PR.
5. Write `frontend/public/uat-manifest.json` and force-push `uat`. Cloudflare Pages deploys it.

Each PR gets a **`uat` commit status**: green = in UAT, yellow = waiting (draft or missing label),
red = skipped because of a conflict. When a PR is skipped, or overrides or is overridden by
another PR, it also gets one auto-updated comment. The UAT page shows a banner listing what's
included.

**Never commit to `uat` by hand.** It is overwritten on every run.

## Testing a PR (or UAT)

1. **Run the backend from the matching code.** The hosted page needs a backend that knows about
   its changes:
   - PR preview: `git fetch origin && git checkout <pr-branch>` (or `gh pr checkout <number>`)
   - UAT: `git fetch origin && git checkout origin/uat`
   - Frontend-only PRs: any recent backend works.
2. Start it: `cd backend && uvicorn main:app --port 8000`. Use the default host, **not**
   `--host 0.0.0.0`, which would expose it to your network.
3. Open the preview or UAT link in **Chrome, Edge or Firefox**. When the browser asks whether the
   site may access devices on your local network, click **Allow**.
4. The nav pill should say **Connected**. The banner (bottom-left) shows the branch, commit, and
   for UAT the included PRs.

### Troubleshooting

| Symptom | Fix |
|---|---|
| "Offline" and the backend is running | Check `http://localhost:8000/api/health` loads in the same browser. Make sure you allowed local network access (Chrome: site settings → "Local network access" → Allow). |
| Works in Chrome, not Safari | Safari blocks `https` pages calling `http://localhost`. Use Chrome, Edge or Firefox. |
| Console shows a CORS error | `CORS_ORIGIN_REGEX` in `backend/.env` must match the preview's address. It defaults to the `refound` project; replace it with the real project subdomain. Restart the backend after editing `.env`. |
| Buttons fail with 404/422 errors | The backend is older or newer than the frontend. Check out the branch shown in the banner. |
| UAT data looks broken after a PR changed the database models | Your local DB was created by older code (`init_db` doesn't add new columns). Stop the backend, move `refound.db` and the `faiss_index*` files aside, and restart. |

## One-time setup (maintainer)

### Cloudflare Pages
1. In Cloudflare, go to **Workers & Pages → Create → Pages → Connect to Git** and choose
   `mrkhan3870/Memory-Trace-`.
2. Build settings:
   - Framework preset: *None* (or Vite)
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Build output directory: `dist`
   - Environment variable: `NODE_VERSION` = `20`
3. Production branch: `main`. Preview deployments: **All non-production branches**. This covers
   PR branches and `uat`.
4. *(Optional, saves builds.)* Under Settings → Builds → **Build watch paths**, include
   `frontend/*`. Backend-only pushes then don't trigger builds. UAT commits always change
   `frontend/public/uat-manifest.json`, so they still build.
5. Note the project's `*.pages.dev` subdomain. Names are global, so it may not be exactly
   `refound`.

No `_redirects` file is needed. Pages serves `index.html` for unknown paths because the app has
no `404.html`.

### GitHub
- **Settings → Secrets and variables → Actions → Variables:** add `PAGES_PROJECT` = the
  subdomain from step 5. The UAT statuses use it to link `https://uat.<project>.pages.dev`.
- **Issues → Labels:** create a label named `uat`, used to opt in fork PRs.
- *(Optional)* **Settings → Rules:** restrict who can push to `uat`, keeping the workflow allowed.
- Run **Actions → UAT → Run workflow** once to create the `uat` branch.

### Backend CORS
If the project subdomain isn't `refound`, set this in each tester's `backend/.env`:
```
CORS_ORIGIN_REGEX=^https://([a-z0-9-]+\.)?<project>\.pages\.dev$
```
Or change the default in `backend/config.py` so nobody has to. The pattern only allows our own
Pages project, so other websites can't read your local backend from your browser.

## Rollback
Production: Cloudflare Pages → project → Deployments → pick an earlier production deployment →
**Rollback**. Or revert the commit on `main`.

## Later
- **Only include PRs whose tests pass:** add a test job, and in `assemble_uat.py` skip PRs whose
  head commit has no green check.
- **Hosted backend:** once a server is available (e.g. a VPS running Docker), deploy `main` and
  `uat` backends next to these frontends and point the default backend URL at them.
