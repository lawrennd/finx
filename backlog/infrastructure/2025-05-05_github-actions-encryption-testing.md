# Task: Add GitHub Actions Matrix for Encryption Testing

- **ID**: 2025-05-05_github-actions-encryption-testing
- **Title**: Configure GitHub Actions to test with and without encryption support
- **Status**: Proposed
- **Priority**: Medium
- **Created**: 2025-05-05
- **Last Updated**: 2025-05-05
- **Owner**: Unassigned
- **GitHub Issue**: N/A
- **Dependencies**: pyzipper library, GitHub Actions

## Description

The current GitHub Actions workflow doesn't specifically handle testing the optional encryption functionality. This task involves enhancing the CI pipeline to:

1. Create a matrix build that tests both with and without the encryption extras
2. Ensure test coverage is maintained for encryption functionality
3. Verify that code gracefully handles missing pyzipper dependency
4. Add badges to the README showing encryption test status

## Acceptance Criteria

- [ ] Update `.github/workflows/tests.yml` to include a matrix for encryption testing
- [ ] Create separate test runs with and without pyzipper installed
- [ ] Add environment variables to control encryption testing behavior
- [ ] Ensure tests pass in both scenarios (with and without encryption support)
- [ ] Add status badges to README for encryption test status
- [ ] Maintain test coverage for encryption-related code

## Implementation Notes

The implementation should:
- Modify the GitHub Actions workflow to include an encryption matrix parameter
- Add a step to conditionally install pyzipper based on the matrix parameter
- Update test running commands to reflect encryption status
- Add environment variables to control test behavior with/without encryption
- Configure proper test reporting for both scenarios
- Consider adding explicit test skipping for encryption tests when pyzipper is not available

## Related

- CIP: 0003
- Tasks: 2025-05-05_encryption-integration-tests
- PRs: None yet

## Progress Updates

### 2025-05-05

Task created with Proposed status as part of CIP-0003 implementation. 