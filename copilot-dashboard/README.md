# Copilot Metrics Dashboard

A self-hosted dashboard that pulls GitHub Copilot usage data daily and
displays it as interactive charts — no third-party service required.

---

## How it works

1. A GitHub Actions workflow (`copilot-metrics.yml`) runs every day at 06:00 UTC.
2. It calls the [GitHub Copilot Usage API](https://docs.github.com/en/rest/copilot/copilot-usage) and saves the results to `data/metrics.json`.
3. The dashboard (`index.html`) reads that JSON file and renders charts automatically.

---

## ✅ One-time setup (the only manual step)

You need to create a secret called **`COPILOT_METRICS_TOKEN`** in this repository.

### Step 1 — Create a Personal Access Token

1. Go to **GitHub.com → your profile → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Click **"Generate new token"**
3. Set:
   - **Token name**: `copilot-metrics-dashboard` (or anything you like)
   - **Resource owner**: `DewDropstempest` (the organization)
   - **Repository access**: `Only select repositories` → pick this repo
   - **Permissions → Organization permissions → GitHub Copilot Business → Access: Read-only**
4. Click **"Generate token"** and **copy the token value** (you only see it once)

> If Fine-grained tokens don't show a Copilot permission yet, create a **Classic token** with the `manage_billing:copilot` scope instead.

### Step 2 — Add the secret to this repository

1. Go to **this repository → Settings → Secrets and variables → Actions**
2. Click **"New repository secret"**
3. Name: `COPILOT_METRICS_TOKEN`
4. Value: paste the token you just copied
5. Click **"Add secret"**

That's it — you're done!

---

## Viewing the dashboard

### Option A — GitHub Pages (recommended, zero extra cost)

1. Go to **this repository → Settings → Pages**
2. Under **"Source"** choose **"Deploy from a branch"**
3. Branch: `main` (or whichever branch this code is on), Folder: `/copilot-dashboard`
4. Click **Save**

Your dashboard will be live at:
```
https://DewDropstempest.github.io/psl/
```

### Option B — Open locally

Just open `copilot-dashboard/index.html` in any modern browser (after the first
workflow run has populated `data/metrics.json`).

---

## Triggering the first run

Don't want to wait until 06:00 UTC? Run it now:

1. Go to **this repository → Actions → Copilot Metrics Collector**
2. Click **"Run workflow" → Run workflow**

The `data/metrics.json` file will be committed automatically and the dashboard will show data within a minute or two.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Workflow fails with `HTTP 403` | Token missing or wrong scope | Re-check Step 1 — ensure Copilot read permission is set |
| Workflow succeeds but dashboard shows "No data yet" | API returned an empty array | Make sure Copilot is enabled for the org and at least one seat is active |
| Workflow fails with `HTTP 404` | Org doesn't have Copilot Business/Enterprise | Purchase a Copilot plan for the org |
| Dashboard shows stale data | Workflow hasn't run yet today | Trigger manually (see above) |
