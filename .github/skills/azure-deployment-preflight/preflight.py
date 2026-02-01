#!/usr/bin/env python3
"""Azure Deployment Preflight diagnostic script.

Usage:
  python preflight.py --root /path/to/repo [--execute] [--output preflight-report.md]

This script detects azd projects and Bicep files, validates tool availability,
builds bicep templates (dry-run), and can optionally run `az deployment .. what-if`
when `--execute` is provided and the environment has `az`/`azd` configured.

It writes a Markdown report (`preflight-report.md` by default) to the specified
output path describing findings and commands used.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from glob import glob
from pathlib import Path


def find_azd_project(root: Path) -> bool:
    return (root / "azure.yaml").exists()


def find_bicep_files(root: Path):
    return [Path(p) for p in glob(str(root / "**" / "*.bicep"), recursive=True)]


def detect_param_files(bicep_path: Path):
    candidates = []
    base = bicep_path.with_suffix("")
    d = bicep_path.parent
    for suffix in (".bicepparam", ".parameters.json"):
        p = base.with_suffix(suffix)
        if p.exists():
            candidates.append(p)
    # common names
    for p in (d / "parameters.json", d / "parameters"):
        if p.exists():
            candidates.append(p)
    return candidates


def get_target_scope(bicep_path: Path):
    try:
        text = bicep_path.read_text()
    except Exception:
        return None
    m = re.search(r"targetScope\s*=\s*['\"](resourceGroup|subscription|managementGroup|tenant)['\"]", text)
    return m.group(1) if m else "resourceGroup"


def check_tools():
    tools = {"az": shutil.which("az"), "azd": shutil.which("azd"), "bicep": shutil.which("bicep")}
    return tools


def run_cmd(cmd, cwd=None, capture=True):
    try:
        if capture:
            r = subprocess.run(cmd, shell=True, cwd=cwd, check=False, capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr
        else:
            r = subprocess.run(cmd, shell=True, cwd=cwd)
            return r.returncode, None
    except Exception as e:
        return 1, str(e)


REPORT_TEMPLATE = """# Azure Deployment Preflight Report

**Generated:** {timestamp}
**Project Root:** {root}

## Summary

- azd project: {azd}
- Bicep files found: {bicep_count}
- Tools: {tools}

## Files

{files_section}

## Commands

{commands}

## Notes

{notes}
"""


def generate_report(root: Path, azd, bicep_files, tools, commands, notes, out_path: Path):
    files_section = """
"""
    for p in bicep_files:
        params = detect_param_files(p)
        scope = get_target_scope(p)
        files_section += f"- {p.relative_to(root)} (scope: {scope})\n"
        if params:
            for pp in params:
                files_section += f"  - params: {pp.relative_to(root)}\n"

    commands_md = "\n".join([f"- `{c}`" for c in commands]) or "- None (dry-run)"
    notes_text = "\n".join(notes) or "No notes"

    content = REPORT_TEMPLATE.format(
        timestamp=datetime.utcnow().isoformat() + "Z",
        root=str(root),
        azd=azd,
        bicep_count=len(bicep_files),
        tools=json.dumps(tools),
        files_section=files_section,
        commands=commands_md,
        notes=notes_text,
    )
    out_path.write_text(content)
    return content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repository root")
    ap.add_argument("--execute", action="store_true", help="Actually execute what-if commands (requires az/azd)")
    ap.add_argument("--output", default="preflight-report.md", help="Report output path")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    azd = find_azd_project(root)
    bicep_files = find_bicep_files(root)
    tools = check_tools()
    notes = []
    commands = []

    if not bicep_files:
        notes.append("No .bicep files found.")

    for b in bicep_files:
        scope = get_target_scope(b)
        if tools.get("bicep"):
            cmd = f"bicep build {b} --stdout"
            commands.append(cmd)
            if args.execute:
                rc, out = run_cmd(cmd)
                if rc != 0:
                    notes.append(f"bicep build failed for {b}: {out[:200]}")
        # what-if command template (not executed unless --execute)
        if scope == "resourceGroup":
            cmd = f"az deployment group what-if --resource-group <rg-name> --template-file {b} --validation-level Provider"
        elif scope == "subscription":
            cmd = f"az deployment sub what-if --location <location> --template-file {b} --validation-level Provider"
        elif scope == "managementGroup":
            cmd = f"az deployment mg what-if --location <location> --management-group-id <mg-id> --template-file {b} --validation-level Provider"
        else:
            cmd = f"az deployment tenant what-if --location <location> --template-file {b} --validation-level Provider"
        commands.append(cmd)

        if args.execute:
            if not tools.get("az"):
                notes.append("Cannot execute az commands: 'az' not found in PATH")
            else:
                rc, out = run_cmd(cmd)
                if rc != 0:
                    # attempt fallback
                    fallback = cmd.replace("Provider", "ProviderNoRbac")
                    notes.append(f"what-if failed for {b} (rc={rc}), trying fallback: ProviderNoRbac")
                    rc2, out2 = run_cmd(fallback)
                    if rc2 != 0:
                        notes.append(f"Fallback also failed for {b}: rc={rc2}")

    report = generate_report(root, azd, bicep_files, tools, commands, notes, Path(args.output))
    print(report)


if __name__ == "__main__":
    main()
