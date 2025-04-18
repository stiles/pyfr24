# Version Change Checklist

This checklist helps ensure all necessary steps are completed when making version changes, adding features, or fixing issues.

## Pre-Release Checklist

### Code Changes
- [ ] Implement new feature or fix
- [ ] Add/update tests
- [ ] Run test suite locally
- [ ] Update type hints if applicable
- [ ] Check for deprecated code that can be removed
- [ ] Review error messages and logging

### Documentation Updates
- [ ] Update relevant documentation files in `docs/`
- [ ] Add/update docstrings for new/modified functions
- [ ] Update CLI documentation if commands changed
- [ ] Add new examples if applicable
- [ ] Check all documentation links are working
- [ ] Review and update README.md if needed

### Changelog Updates
- [ ] Add entry to CHANGELOG.md in project root
  - [ ] Use correct version number
  - [ ] Add under correct section (Added/Changed/Fixed)
  - [ ] Include PR/Issue numbers if applicable
- [ ] Update docs/changelog/index.md to match
- [ ] Ensure changelog formatting is consistent

### Version Updates
- [ ] Update version number in `__init__.py`
- [ ] Update version in setup.py/pyproject.toml
- [ ] Update any version-dependent documentation
- [ ] Check requirements.txt for any version updates

### Release Process
- [ ] Create and push version tag
- [ ] Create GitHub release
  - [ ] Include changelog entries
  - [ ] Add any additional release notes
- [ ] Check Read the Docs build succeeds
- [ ] Verify documentation is updated on Read the Docs

## Post-Release Checklist

### Verification
- [ ] Install package from PyPI in clean environment
- [ ] Test basic functionality
- [ ] Verify documentation is accessible
- [ ] Check all new features/fixes work as expected

### Communication
- [ ] Update release notes if needed
- [ ] Notify users of breaking changes
- [ ] Update issue/PR status if applicable

### Cleanup
- [ ] Close related issues
- [ ] Update project board
- [ ] Archive completed project tasks
- [ ] Remove any temporary files/branches

## Notes

- Always create a new branch for version changes
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Test documentation builds locally before pushing
- Keep changelog entries clear and concise
- Include migration guides for breaking changes 