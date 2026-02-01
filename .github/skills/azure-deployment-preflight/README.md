# Azure Deployment Preflight Script

This folder contains `preflight.py`, a lightweight diagnostic script to help validate
Bicep deployments before applying them to Azure.

Features:
- Detects whether the repository is an `azd` project (presence of `azure.yaml`).
- Finds `.bicep` files and parameter files.
- Checks availability of `az`, `azd`, and `bicep` CLIs.
- Generates a Markdown report `preflight-report.md` describing findings and commands.
- Optionally executes `bicep build` and `az ... what-if` commands when `--execute` is provided.

Usage:

```bash
python .github/skills/azure-deployment-preflight/preflight.py --root . --output preflight-report.md

# To actually run bicep/az commands (requires CLI tools & auth):
python .github/skills/azure-deployment-preflight/preflight.py --root . --execute --output preflight-report.md
```

Notes:
- The script intentionally requires `--execute` to run any `az` or `bicep` commands.
- Replace placeholder `--resource-group <rg-name>` / `--location` values in the generated
  commands before executing them in production.
