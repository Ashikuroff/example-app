#!/bin/bash
# Script to validate GitOps pattern setup
# Run this to verify all apps are properly configured

set -e

echo "════════════════════════════════════════════════════════════════"
echo "GitOps Pattern Validation Script"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0
PASSED=0

# Check if kustomize is installed
if ! command -v kustomize &> /dev/null; then
    echo -e "${RED}✗ kustomize not found. Install from: https://kustomize.io/${NC}"
    exit 1
fi

echo "kustomize version:"
kustomize version

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Validating app structures..."
echo "════════════════════════════════════════════════════════════════"
echo ""

# Test function
test_app_structure() {
    local app=$1
    echo "Testing: $app"
    
    # Check base directory exists
    if [ ! -d "apps/$app/k8s/base" ]; then
        echo -e "${RED}  ✗ Missing apps/$app/k8s/base${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
    
    # Check overlays exist
    for env in dev staging prod; do
        if [ ! -d "apps/$app/k8s/overlays/$env" ]; then
            echo -e "${RED}  ✗ Missing apps/$app/k8s/overlays/$env${NC}"
            FAILED=$((FAILED + 1))
            return 1
        fi
    done
    
    # Test kustomize build for each environment
    for env in dev staging prod; do
        if ! kustomize build "apps/$app/k8s/overlays/$env" > /dev/null 2>&1; then
            echo -e "${RED}  ✗ Kustomize build failed for $env${NC}"
            kustomize build "apps/$app/k8s/overlays/$env" 2>&1 | head -5
            FAILED=$((FAILED + 1))
            return 1
        fi
        echo -e "${GREEN}  ✓ $env overlay builds successfully${NC}"
    done
    
    # Check source code exists
    if [ ! -f "apps/$app/src/server.py" ]; then
        echo -e "${YELLOW}  ⚠ Warning: Missing apps/$app/src/server.py${NC}"
    else
        echo -e "${GREEN}  ✓ Source code present${NC}"
    fi
    
    # Check tests exist
    if [ ! -f "apps/$app/test/test_server.py" ]; then
        echo -e "${YELLOW}  ⚠ Warning: Missing apps/$app/test/test_server.py${NC}"
    else
        echo -e "${GREEN}  ✓ Tests present${NC}"
    fi
    
    echo -e "${GREEN}  ✓ $app structure valid${NC}"
    PASSED=$((PASSED + 1))
    echo ""
}

# Find all apps
APPS=$(find apps -maxdepth 1 -type d ! -name ".template" ! -name "." | sed 's|apps/||' | grep -v '^$' | sort)

if [ -z "$APPS" ]; then
    echo -e "${YELLOW}No apps found to validate${NC}"
else
    for app in $APPS; do
        test_app_structure "$app" || true
    done
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Checking ArgoCD Applications..."
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ -f "argo/root-app.yaml" ]; then
    echo -e "${GREEN}✓ Found argo/root-app.yaml${NC}"
else
    echo -e "${RED}✗ Missing argo/root-app.yaml${NC}"
    FAILED=$((FAILED + 1))
fi

ARGO_APPS=$(find argo/apps -name "*-dev.yaml" -o -name "*-staging.yaml" -o -name "*-prod.yaml" 2>/dev/null | wc -l)
if [ "$ARGO_APPS" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $ARGO_APPS ArgoCD Application definitions${NC}"
else
    echo -e "${YELLOW}⚠ No environment-specific ArgoCD apps found in argo/apps/${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Checking CI/CD Workflow..."
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ -f ".github/workflows/main.yml" ]; then
    echo -e "${GREEN}✓ Found .github/workflows/main.yml${NC}"
    
    # Check for kustomize commands
    if grep -q "kustomize edit set image" ".github/workflows/main.yml"; then
        echo -e "${GREEN}✓ Workflow contains kustomize image tag updates${NC}"
    else
        echo -e "${RED}✗ Workflow missing kustomize image tag updates${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}✗ Missing .github/workflows/main.yml${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Checking Documentation..."
echo "════════════════════════════════════════════════════════════════"
echo ""

docs=("ONBOARDING.md" "OBSERVABILITY.md" "TROUBLESHOOTING.md" "GITOPS-PATTERN.md")
for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✓ $doc exists${NC}"
    else
        echo -e "${RED}✗ Missing $doc${NC}"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Validation Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "Apps validated: ${GREEN}$PASSED${NC}"
echo -e "Issues found: ${RED}$FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review ONBOARDING.md for adding new apps"
    echo "  2. Check OBSERVABILITY.md for monitoring setup"
    echo "  3. Read GITOPS-PATTERN.md for architecture overview"
    exit 0
else
    echo -e "${RED}✗ Please fix the issues above${NC}"
    exit 1
fi
