# Task: Fix PyZipper Test Recursion Error in CI

- **ID**: 2025-05-05_fix-pyzipper-tests-recursion
- **Title**: Fix recursion error in PyZipper tests on CI
- **Status**: Proposed
- **Priority**: High
- **Created**: 2025-05-05
- **Last Updated**: 2025-05-05
- **Owner**: Unassigned
- **GitHub Issue**: N/A
- **Dependencies**: tests/test_archive.py

## Description

The GitHub Actions CI build is failing with recursion errors in PyZipper-related tests. Two tests in `tests/test_archive.py` are causing maximum recursion depth errors:

1. `test_create_password_protected_zip_real_mode`
2. `test_create_password_protected_zip_without_pyzipper`

The issue appears to be in how these tests are patching the `__import__` function, causing infinite recursion when running in the CI environment. The local tests may work because the local environment has different patching behavior or Python version.

## Acceptance Criteria

- [ ] Fix the recursion error in `test_create_password_protected_zip_real_mode`
- [ ] Fix the recursion error in `test_create_password_protected_zip_without_pyzipper`
- [ ] Ensure the tests pass in the CI environment
- [ ] Update the test mocking approach to be more robust
- [ ] Verify tests pass with and without pyzipper installed

## Implementation Notes

The problem is likely in the implementation of the mocking for `builtins.__import__`. Instead of directly mocking the import function with a side_effect lambda, we should:

1. Use `patch.dict()` to modify `sys.modules` directly for pyzipper
2. Or use `patch.object()` with a simpler approach for the import mock
3. Alternatively, refactor the code to make it more testable without complex import mocking

The fix should also ensure we don't have nested patch decorators that might cause recursion issues.

## Related

- CIP: 0003
- Tasks: 2025-05-05_github-actions-encryption-testing
- PRs: None yet

## Progress Updates

### 2025-05-05

Task created with Proposed status based on CI failure. This is a blocker for CIP-0003 implementation. 