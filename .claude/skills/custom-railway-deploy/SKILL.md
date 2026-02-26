---
name: custom-railway-deploy
description: "Manages Railway platform deployments for Python/FastAPI backend services. Use when deploying to Railway, managing environment variables, viewing deployment logs, configuring nixpacks.toml, setting up domains, or troubleshooting Railway build and deployment failures."
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Railway Deployment Skill

Comprehensive guide for deploying and managing services on Railway platform using the Railway CLI. Focused on Python/FastAPI backend deployments with nixpacks build system.

## Quick Reference

### CLI Installation and Authentication

Install Railway CLI on macOS:

```bash
brew install railway
```

Alternative install methods:

```bash
# npm
npm install -g @railway/cli

# shell script
bash <(curl -fsSL cli.new)
```

Authentication:

```bash
# Interactive login (opens browser)
railway login

# Browserless login (for SSH/headless)
railway login --browserless

# CI/CD: set RAILWAY_TOKEN env var instead of login
export RAILWAY_TOKEN="your-project-token"
```

### Essential Commands Cheat Sheet

Project setup:

```bash
railway link                          # Link local directory to Railway project/service
railway service                       # Link to a specific service (interactive)
railway environment                   # Switch environment (production/staging)
```

Deployment:

```bash
railway up                            # Deploy current directory
railway up --detach                   # Deploy without blocking (streams logs)
railway up -s backend                 # Deploy specific service
```

Environment variables:

```bash
railway variables list                # List all variables
railway variables set KEY=value       # Set a variable
railway variables set K1=v1 K2=v2     # Set multiple variables
railway variables delete KEY          # Delete a variable
```

Logs and debugging:

```bash
railway logs                          # Stream deployment logs
railway logs --build                  # View build logs
railway logs -n 100                   # Show last 100 lines
```

Local development:

```bash
railway run python main.py            # Run with Railway env vars injected
railway shell                         # Open shell with Railway env vars
```

Domain management:

```bash
railway domain                        # Generate a Railway subdomain
railway domain example.com            # Add custom domain
```

### Global CLI Flags

These flags work with most commands:

- `-s, --service <name>` - Target a specific service
- `-e, --environment <name>` - Target a specific environment
- `--json` - Output in JSON format
- `-y, --yes` - Skip confirmation prompts

---

## Implementation Guide

### Project Linking for Monorepo

This project is a monorepo with separate frontend and backend directories. Each service must be linked individually.

Step 1 - Link the backend service:

```bash
cd backend
railway link
# Select the project, then select the backend service
```

Step 2 - Set root directory in Railway Dashboard:

Navigate to the service Settings and set Root Directory to `/backend`. This ensures Railway only pulls files from the backend directory during builds.

Step 3 - Verify the link:

```bash
railway status
```

Important: The railway.toml config file path is absolute from the repo root, not relative to the root directory setting. Place it at `/backend/railway.toml`, not at the repo root.

### Deployment Workflow

Standard deployment from the backend directory:

```bash
railway up
```

This triggers the following pipeline:
1. Railway detects the root directory setting (`/backend`)
2. Nixpacks reads `nixpacks.toml` for build configuration
3. Build phase installs dependencies per nixpacks phases
4. Start phase executes the command from nixpacks.toml or Procfile
5. Railway provisions a container and routes traffic

Deploy with service targeting (from any directory):

```bash
railway up -s backend-service-name
```

Deploy from GitHub (recommended for production):

Push to the connected GitHub branch. Railway auto-deploys on push when GitHub integration is configured. This is preferred over `railway up` for production because it provides reproducible builds from version-controlled code.

### nixpacks.toml Configuration

The project uses nixpacks.toml for build configuration. This file lives in the service root directory (`/backend/nixpacks.toml`).

Current project configuration:

```toml
[phases.setup]
nixPkgs = ["python313"]

[phases.install]
cmds = ["pip install --upgrade pip", "pip install ."]

[start]
cmd = "uvicorn tutor.main:app --host 0.0.0.0 --port $PORT --workers 1"
```

Key sections explained:

**phases.setup** - System-level packages. Use `nixPkgs` to specify the Python version or add system dependencies like `ffmpeg`, `libpq`, or `gcc`.

**phases.install** - Dependency installation commands. The `pip install .` command installs from `pyproject.toml`. Alternative: `pip install -r requirements.txt`.

**phases.build** - Optional build step for compilation or asset generation:

```toml
[phases.build]
cmds = ["python -m compileall ."]
```

**start** - The command that launches the application. Must bind to `0.0.0.0` and use `$PORT`.

Common nixpacks.toml patterns for Python:

```toml
# Add system packages (e.g., for Pillow, psycopg2)
[phases.setup]
nixPkgs = ["python313", "gcc", "libffi", "openssl"]
aptPkgs = ["libpq-dev"]

# Install from requirements.txt
[phases.install]
cmds = ["pip install -r requirements.txt"]

# Install from pyproject.toml with extras
[phases.install]
cmds = ["pip install --upgrade pip", "pip install '.[dev]'"]

# Custom start with gunicorn
[start]
cmd = "gunicorn tutor.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"
```

### Procfile as Alternative

The project also has a Procfile (`/backend/Procfile`):

```
web: uvicorn tutor.main:app --host 0.0.0.0 --port $PORT --workers 1
```

Nixpacks.toml `[start].cmd` takes precedence over Procfile when both exist. Remove one to avoid confusion.

### Environment Variables Management

Setting variables for the backend service:

```bash
# Set API keys and secrets
railway variables set OPENAI_API_KEY=sk-xxx
railway variables set DATABASE_URL=postgresql://user:pass@host:5432/db

# Set multiple at once
railway variables set \
  ENVIRONMENT=production \
  LOG_LEVEL=info \
  CORS_ORIGINS="https://myapp.com"
```

Railway-provided variables (automatically available):

- `PORT` - The port your app must listen on (Railway assigns this)
- `RAILWAY_PUBLIC_DOMAIN` - Public domain of your service
- `RAILWAY_PRIVATE_DOMAIN` - Internal domain for service-to-service communication
- `RAILWAY_ENVIRONMENT_NAME` - Current environment name
- `RAILWAY_SERVICE_NAME` - Current service name

Reference variables syntax (in Railway Dashboard):

- `${{ shared.VARIABLE_KEY }}` - Reference shared project variable
- `${{ SERVICE_NAME.VAR }}` - Reference another service's variable
- `${{ VARIABLE_NAME }}` - Reference same-service variable

Importing from .env file:

Use the RAW Editor in the Railway Dashboard Variables tab to paste the contents of a `.env` file directly.

### Port and Domain Configuration

Critical rule: Your application MUST bind to `0.0.0.0:$PORT`. Railway injects the `PORT` environment variable automatically.

For uvicorn (current project):

```bash
uvicorn tutor.main:app --host 0.0.0.0 --port $PORT
```

Do NOT hardcode ports. Do NOT bind to `127.0.0.1` or `localhost`.

Setting up a public domain:

```bash
# Generate Railway subdomain (*.up.railway.app)
railway domain

# Add custom domain
railway domain api.example.com
```

After adding a custom domain, configure DNS:
- Add a CNAME record pointing to your Railway domain
- Railway handles SSL certificate provisioning automatically

### railway.toml Service Configuration

Create `/backend/railway.toml` for declarative service configuration:

```toml
[build]
builder = "NIXPACKS"
nixpacksConfigPath = "nixpacks.toml"
watchPatterns = ["backend/**"]

[deploy]
startCommand = "uvicorn tutor.main:app --host 0.0.0.0 --port $PORT --workers 1"
healthcheckPath = "/health"
healthcheckTimeout = 120
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
```

Available build settings:

- `builder` - Build system: `RAILPACK` (default), `NIXPACKS`, or `DOCKERFILE`
- `buildCommand` - Custom build command
- `watchPatterns` - File patterns that trigger rebuilds (useful for monorepos)
- `dockerfilePath` - Path to Dockerfile when using DOCKERFILE builder
- `nixpacksConfigPath` - Path to nixpacks.toml

Available deploy settings:

- `startCommand` - Container startup command
- `healthcheckPath` - Health check endpoint
- `healthcheckTimeout` - Seconds to wait for health check
- `restartPolicyType` - `ON_FAILURE`, `ALWAYS`, or `NEVER`
- `restartPolicyMaxRetries` - Max restart attempts
- `cronSchedule` - Cron expression for scheduled services

Environment-specific overrides:

```toml
[environments.production.deploy]
startCommand = "gunicorn tutor.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"

[environments.staging.deploy]
startCommand = "uvicorn tutor.main:app --host 0.0.0.0 --port $PORT --reload"
```

### Viewing and Managing Logs

Real-time log streaming:

```bash
# Stream deployment logs
railway logs

# View build logs (useful for debugging build failures)
railway logs --build

# Show last N lines
railway logs -n 200

# Target specific service
railway logs -s backend-service-name
```

---

## Advanced Patterns

### CI/CD Deployment with RAILWAY_TOKEN

For automated deployments in GitHub Actions or other CI systems:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway
on:
  push:
    branches: [main]
    paths: ['backend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      - name: Deploy
        run: railway up --service backend-service-name
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

Generate a project token: Railway Dashboard > Project Settings > Tokens > Create Token.

### Health Check Configuration

Add a health check endpoint to your FastAPI app:

```python
@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

Then configure in railway.toml:

```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 120
```

Railway uses the health check to verify deployment success before routing traffic. If the health check fails within the timeout, the deployment is rolled back.

### Multi-Region Deployment

Configure in railway.toml for geographic distribution:

```toml
[deploy.multiRegion]
us-west1 = { replicas = 2 }
us-east4 = { replicas = 1 }
europe-west4 = { replicas = 1 }
```

### Pre-Deploy Commands

Run database migrations or setup tasks before the main service starts:

```toml
[deploy]
preDeployCommand = "python -m alembic upgrade head"
startCommand = "uvicorn tutor.main:app --host 0.0.0.0 --port $PORT"
```

The pre-deploy command runs in a separate container before the new deployment goes live.

### Troubleshooting Common Errors

**"Application failed to respond" (502 Bad Gateway)**

Cause: App not binding to `0.0.0.0:$PORT`.

Fix: Ensure your start command uses `--host 0.0.0.0 --port $PORT`. Never hardcode a port number. Check that `PORT` is not overridden in your variables.

Verify: Check the Metrics tab for vCPU usage spikes. If the app is under heavy load, consider adding replicas.

**"Nixpacks was unable to generate a build plan"**

Cause: Nixpacks cannot detect the project type.

Fix options:
1. Ensure `requirements.txt`, `pyproject.toml`, or `Pipfile` exists in the root directory
2. Set the root directory correctly for monorepo projects
3. Create a `nixpacks.toml` with explicit provider: add `providers = ["python"]` at the top
4. Switch to Railpack builder (newer, better detection)

**Build failure: "ModuleNotFoundError"**

Cause: Missing dependency in requirements or incorrect install command.

Fix: Verify all dependencies are listed in `pyproject.toml` or `requirements.txt`. Check that the install command in nixpacks.toml matches your dependency file format.

**Build failure: System package missing**

Cause: Python packages needing C libraries (Pillow, psycopg2, cryptography).

Fix: Add system packages to nixpacks.toml:

```toml
[phases.setup]
nixPkgs = ["python313", "gcc", "libffi", "openssl", "zlib"]
```

**Deploy succeeds but app crashes immediately**

Cause: Missing environment variables or incorrect start command.

Fix:
1. Check `railway logs` for the error message
2. Verify all required env vars are set: `railway variables list`
3. Test locally: `railway run uvicorn tutor.main:app --host 0.0.0.0 --port 8000`

**Slow deployments**

Cause: Large dependencies or no build cache.

Fix: Use `railway up --detach` to avoid blocking. Consider using Railpack builder for faster builds. Minimize unnecessary system packages.

### Railpack Migration

Railway is transitioning from Nixpacks to Railpack as the default builder. To switch:

```toml
# railway.toml
[build]
builder = "RAILPACK"
```

Railpack offers smaller image sizes and improved build performance. If your nixpacks.toml works well, no immediate migration is required.

### Watch Patterns for Monorepo

Prevent unnecessary rebuilds by limiting which file changes trigger deployment:

```toml
[build]
watchPatterns = ["backend/**"]
```

This ensures only changes to the `backend/` directory trigger rebuilds, not frontend changes.

---

## Works Well With

- moai-platform-deployment: General deployment patterns and strategies
- expert-devops: Infrastructure and CI/CD pipeline configuration
- expert-backend: FastAPI application development and optimization
- moai-lang-python: Python-specific build and runtime patterns
