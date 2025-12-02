#!/bin/bash
#
# Comprehensive Test Script for GitDoctor
# Tests all major functionality and error cases
#

set -e

echo "🧪 GitDoctor Comprehensive Test Suite"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

test_case() {
    local name="$1"
    local command="$2"
    local expected_exit="${3:-0}"
    
    echo -n "Testing: $name... "
    
    if eval "$command" > /tmp/gitdoctor_test.log 2>&1; then
        EXIT_CODE=0
    else
        EXIT_CODE=$?
    fi
    
    if [ "$EXIT_CODE" -eq "$expected_exit" ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC} (expected exit $expected_exit, got $EXIT_CODE)"
        echo "   Command: $command"
        echo "   Output:"
        cat /tmp/gitdoctor_test.log | sed 's/^/   /'
        ((FAILED++))
    fi
}

# Test 1: Help command
test_case "Help command" "gitdoctor --help" 0

# Test 2: Delta command missing required args
test_case "Delta missing --after" "gitdoctor delta --base TAG1 --target TAG2" 2

# Test 3: Delta command with invalid date format
test_case "Delta invalid date format" "gitdoctor delta --base TAG1 --target TAG2 --after 2025/09/01 --before 2025-11-01" 1

# Test 4: Delta command with date range > 2 months
test_case "Delta date range > 2 months" "gitdoctor delta --base TAG1 --target TAG2 --after 2025-01-01 --before 2025-06-01" 1

# Test 5: Delta command with valid date range (should fail on API but pass validation)
test_case "Delta valid date range validation" "gitdoctor delta --base TAG1 --target TAG2 --after 2025-09-01 --before 2025-11-01 --projects nonexistent" 1

# Test 6: Secret scanner
test_case "Secret scanner runs" "python scripts/check_secrets.py --path scripts/check_secrets.py" 0

# Test 7: Linter check
test_case "Linter on cli.py" "python -m py_compile gitdoctor/cli.py" 0

echo ""
echo "======================================"
echo "Test Results:"
echo "  ${GREEN}Passed: $PASSED${NC}"
echo "  ${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

