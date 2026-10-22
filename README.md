# Color CI/CD Demo

A tiny Python (Flask) web app that **changes colour on every deployment**. Push code → GitHub Actions tests it, scans it with SonarQube, builds a Docker image, scans the image with Trivy, pushes it to Docker Hub and runs it on an EC2 instance. Open `http://<EC2-public-IP>:8080` and the page shows a new colour and build number.

```
git push ─► 1. Checkout, build & test ─► 2. SonarQube ─► 3. Docker build ─► Trivy scan ─► push ─► 4. Deploy on EC2 ─► http://<ip>:8080
             (pytest + coverage)          (quality gate)    (image)          (CVE gate)    (Docker Hub) (docker run)
```

| Stage | Where in `.github/workflows/ci-cd.yml` | Tool |
|---|---|---|
| Code checkout | every job, `actions/checkout` | GitHub Actions |
| Build + unit tests | job **1. Checkout, build & test** | pip, pytest, pytest-cov |
| Static code analysis | job **2. Static code analysis** | SonarQube Cloud + Quality Gate |
| Image build | job **3**, step *Build the Docker image* | Docker |
| Image scan | job **3**, steps *Trivy scan* / *Trivy gate* | Trivy |
| Push to registry | job **3**, step *Push the image* | Docker Hub |
| Run container on EC2 | job **4. Deploy & run on EC2** | SSH + Docker |

Pull requests run jobs 1–3 (no push, no deploy). Pushes to `main` run everything.

**Why the colour changes:** the pipeline passes `BUILD_NUMBER=${{ github.run_number }}` into the image (`docker build --build-arg`). The app turns that number into a colour, and consecutive builds are always far apart on the colour wheel.

---

## Project files

```
color-cicd-demo/
├── app.py                        # Flask app: /  /health  /api/info
├── tests/test_app.py             # unit tests (pytest)
├── requirements.txt              # runtime: flask, gunicorn
├── requirements-dev.txt          # + pytest, pytest-cov
├── Dockerfile                    # python:3.12-alpine, non-root, healthcheck
├── .dockerignore
├── sonar-project.properties      # SonarQube Cloud settings
├── scripts/setup-ec2.sh          # installs Docker on the EC2 instance
└── .github/workflows/ci-cd.yml   # the pipeline
```

---

## One-time setup (about 30 minutes)

### Step 1 — Create the repository and push the code

1. On GitHub: **+** → **New repository** → name **`color-cicd-demo`** → **Public** → do **not** add a README → **Create repository**.
2. Unzip this project, open a terminal inside the `color-cicd-demo` folder and run:

```bash
git init
git add .
git commit -m "Initial commit: color CI/CD demo"
git branch -M main
git remote add origin https://github.com/Rupessh-Metra/color-cicd-demo.git
git push -u origin main
```

> The first pipeline run **will fail** at SonarQube because the secrets don't exist yet. That's expected. Finish the setup, then re-run it.

### Step 2 — Docker Hub token

1. Sign in at **hub.docker.com** → avatar → **Account settings** → **Personal access tokens** → **Generate new token**.
2. Description `github-actions`, permissions **Read & Write** → **Generate** → copy the token (shown only once).

The pipeline pushes to `<your-dockerhub-username>/color-cicd-demo`. Docker Hub creates the repository on the first push. Keep it **public** so the EC2 instance can pull without logging in.

### Step 3 — SonarQube Cloud

1. Go to **sonarcloud.io** → **Log in with GitHub**.
2. **+** → **Analyze new project** → import your GitHub account **Rupessh-Metra** as an organization (choose the **Free** plan) → pick the **color-cicd-demo** repository → **Set up**.
3. Choose **Previous version** as the new-code definition if asked.
4. **Turn off Automatic Analysis** — required for CI-based scans: project → **Administration** → **Analysis Method** → switch **Automatic Analysis** off.
5. On the same page choose **GitHub Actions** as the analysis method. It shows a **SONAR_TOKEN** value — copy it.
6. Open project → **Information** and check that **Organization key** and **Project key** match `sonar-project.properties`:

```properties
sonar.organization=rupessh-metra
sonar.projectKey=Rupessh-Metra_color-cicd-demo
```

If they differ, edit the file, then commit and push.

### Step 4 — EC2 instance (from your teammate)

You need: the **public IP**, the **SSH user** (`ec2-user` for Amazon Linux, `ubuntu` for Ubuntu) and the **private key** (`.pem` file).

1. **Security group inbound rules:**

| Port | Source | Why |
|---|---|---|
| 22 (SSH) | `0.0.0.0/0` | GitHub's runners connect from many IPs (demo shortcut — restrict it for real projects) |
| 8080 (TCP) | `0.0.0.0/0` | so anyone can open the app |

2. **Install Docker** (from your laptop):

```bash
chmod 400 mykey.pem
scp -i mykey.pem scripts/setup-ec2.sh <user>@<public-ip>:~
ssh -i mykey.pem <user>@<public-ip>
bash setup-ec2.sh
exit
# log in again, then check:
ssh -i mykey.pem <user>@<public-ip> "docker run --rm hello-world"
```

### Step 5 — GitHub secrets and variables

Repository → **Settings** → **Secrets and variables** → **Actions**.

**Secrets tab** → *New repository secret*:

| Name | Value |
|---|---|
| `DOCKERHUB_TOKEN` | Docker Hub token from Step 2 |
| `SONAR_TOKEN` | SonarQube Cloud token from Step 3 |
| `EC2_SSH_KEY` | Full content of the `.pem` file, including the `-----BEGIN…` and `-----END…` lines |

**Variables tab** → *New repository variable* (not secret, so they show in logs and the run summary):

| Name | Value |
|---|---|
| `DOCKERHUB_USERNAME` | your Docker Hub username |
| `EC2_HOST` | EC2 public IP, e.g. `13.233.10.20` |
| `EC2_USER` | `ec2-user` (Amazon Linux) or `ubuntu` (Ubuntu) |

### Step 6 — First full run

**Actions** → **CI/CD Pipeline** → **Run workflow** → `main`. All four jobs should turn green. Open `http://<EC2_HOST>:8080`.

---

## Classroom demo script

| # | What to do | What to show / say |
|---|---|---|
| 1 | Open `http://<ip>:8080` | Current colour + build number. The page auto-refreshes every 10 s. |
| 2 | Edit any file (e.g. the footer text in `app.py`), commit, `git push` | "One push starts everything." |
| 3 | Actions tab → open the run | The graph: 4 jobs in a chain (`needs:`). |
| 4 | Job 1 | Checkout, `pip install`, tests and coverage — the same commands you'd type by hand. |
| 5 | Job 2 + sonarcloud.io | Bugs, code smells, coverage %, **Quality Gate: Passed**. `sonar.qualitygate.wait=true` makes a failed gate stop the pipeline. |
| 6 | Job 3 | `docker build --build-arg BUILD_NUMBER=…`, then the Trivy table of HIGH/CRITICAL CVEs, the CRITICAL gate, and the push to Docker Hub with two tags (`:<sha>` and `:latest`). |
| 7 | Job 4 | SSH into EC2 → `docker pull` → remove old container → `docker run -p 8080:5000`. Then a `curl` health check from the runner. |
| 8 | Back to the browser | **New colour, new build number.** |
| 9 | (optional) `ssh` into EC2, run `docker ps`, `docker logs color-app` | The running container that the pipeline started. |

**Break it on purpose (optional):**

- **Failing test:** change `"Hello from CI/CD!"` in `app.py` → job 1 fails. Nothing gets built or deployed, so the site keeps its old colour.
- **Pull request flow:** push a branch and open a PR → jobs 1–3 run as checks, with no push or deploy. Merge it → full pipeline.
- **Quality gate:** add new code with an obvious issue, e.g. a hard-coded `password = "admin123"`. The quality gate usually fails on the unreviewed security hotspot.
- **Trivy gate:** change `FROM python:3.12-alpine` to a very old image such as `python:3.7-alpine`. It usually has fixable CRITICAL CVEs, so the Trivy gate fails before anything is pushed.

---

## Run it locally with Docker

```bash
docker build --build-arg BUILD_NUMBER=5 --build-arg APP_VERSION=local -t color-cicd-demo .
docker run -d --name color-app -p 8080:5000 color-cicd-demo
# open http://localhost:8080, then try BUILD_NUMBER=6 for a different colour
docker rm -f color-app
```

Run the tests without Docker:

```bash
pip install -r requirements-dev.txt
pytest --cov=app
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Sonar: *"You are running CI analysis while Automatic Analysis is enabled"* | Turn off Automatic Analysis (Step 3.4). |
| Sonar: *"Project not found"* / not authorized | `sonar.organization` / `sonar.projectKey` don't match sonarcloud.io, or `SONAR_TOKEN` is wrong. |
| Sonar: *Quality Gate failed* | Open the link in the job log, fix the issue or review the hotspot. |
| Image name looks like `/color-cicd-demo:abc1234` | The `DOCKERHUB_USERNAME` **variable** is missing. It's a variable, not a secret. |
| Docker login: *incorrect username or password* | Token needs **Read & Write**. Check `DOCKERHUB_TOKEN`. |
| Deploy: *ssh: handshake failed* / *i/o timeout* | Check `EC2_HOST`, `EC2_USER`, the full `.pem` in `EC2_SSH_KEY`, and that port 22 is open. |
| Deploy: *permission denied … docker.sock* | `setup-ec2.sh` adds your user to the `docker` group. Log out and in once, or re-run the script. |
| Health check fails / browser can't connect | Port **8080** must be open in the security group. Use `http://`, not `https://`. |
| Trivy gate fails | A fixable CRITICAL CVE was found. Read the table, then update the base image or package versions. |

**Security notes:** every third-party action is pinned to a full commit SHA (the version is in a comment next to it), so a moved tag can't change what runs. In March 2026 attackers rewrote most `aquasecurity/trivy-action` tags (CVE-2026-33634); SHA pinning protects against exactly that. Use Dependabot to update the pins.
