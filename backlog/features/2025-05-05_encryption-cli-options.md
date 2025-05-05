# Task: Add Explicit Encryption CLI Options

- **ID**: 2025-05-05_encryption-cli-options
- **Title**: Add explicit encryption options to finx CLI commands
- **Status**: Proposed
- **Priority**: Medium
- **Created**: 2025-05-05
- **Last Updated**: 2025-05-05
- **Owner**: Unassigned
- **GitHub Issue**: N/A
- **Dependencies**: pyzipper library

## Description

Currently, the encryption functionality in the finx CLI is passive - it's used if pyzipper is available and a password is provided, but there's no explicit way to request or require encryption. This task involves adding explicit CLI options to:

1. Enable/disable encryption (`--encrypt`/`--no-encrypt` flags)
2. Require encryption with a failure if not available (`--require-encryption` flag)
3. Add a verification option to check if archives are properly encrypted (`--verify-encryption` flag)
4. Provide helpful error messages when encryption is requested but not available

## Acceptance Criteria

- [ ] Add `--encrypt`/`--no-encrypt` flags to archive commands
- [ ] Add `--require-encryption` flag that fails if pyzipper is not available
- [ ] Add `--verify-encryption` option to verify archives are properly encrypted
- [ ] Update help documentation for these new options
- [ ] Add comprehensive tests for all new CLI options
- [ ] Ensure backward compatibility with existing behavior

## Implementation Notes

The implementation should:
- Update the CLI interface in `finx/cli.py`
- Modify `finx/archive.py` to support explicit encryption requirements
- Add validation functions to verify if archives are properly encrypted
- Provide clear error messages for encryption-related issues
- Update help text with examples of encryption usage

## Related

- CIP: 0003
- Documentation: Update README.md and possibly create encryption.md

## Progress Updates

### 2025-05-05

Task created with Proposed status as part of CIP-0003. 