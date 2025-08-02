# Publishing Guide

This document describes the process for publishing new versions of pyfr24 to PyPI and creating releases.

## Quick Start

Use the automated publish script:

```bash
./publish.sh
```

This script handles the entire publishing workflow from version bumping to PyPI upload and GitHub releases.

## Manual Process

If you prefer to do things manually, follow these steps:

### 1. Pre-publication Checklist

- [ ] All tests pass (`python run_tests.py`)
- [ ] CHANGELOG.md is updated with new features
- [ ] Documentation is up to date
- [ ] Version number is correct in `setup.py`
- [ ] Git working directory is clean

### 2. Version Management

Update the version in these locations:
- `setup.py` (required)
- `pyfr24/__init__.py` (if exists)
- `CHANGELOG.md` (move [Unreleased] to new version)

### 3. Git Operations

```bash
# Commit version changes
git add setup.py CHANGELOG.md pyfr24/__init__.py
git commit -m "Bump version to X.Y.Z"

# Push to main branch
git push origin main

# Create and push tag
git tag vX.Y.Z
git push origin vX.Y.Z
```

### 4. Build and Test

```bash
# Clean previous builds
rm -rf build dist pyfr24.egg-info

# Build package
python -m build

# Test the build
python -m twine check dist/*
```

### 5. Publish to PyPI

#### Test on TestPyPI first (recommended)

```bash
# Upload to TestPyPI
python -m twine upload --repository-url https://test.pypi.org/legacy/ -u __token__ -p $PYPI_TEST dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple pyfr24==X.Y.Z
```

#### Publish to Official PyPI

```bash
# Upload to PyPI
python -m twine upload -u __token__ -p $PYPI dist/*
```

### 6. Create GitHub Release

```bash
# Using GitHub CLI
gh release create vX.Y.Z dist/* --title "Release vX.Y.Z" --notes-file RELEASE_NOTES.md

# Or create manually at: https://github.com/stiles/pyfr24/releases/new
```

## Environment Variables

Set these environment variables for automated publishing:

```bash
# PyPI API tokens
export PYPI="pypi-your-api-token-here"          # Official PyPI
export PYPI_TEST="pypi-your-test-token-here"    # TestPyPI
```

### Getting API Tokens

1. **PyPI**: Go to https://pypi.org/manage/account/token/
2. **TestPyPI**: Go to https://test.pypi.org/manage/account/token/

Create tokens with "Entire account" scope or limit to the pyfr24 project.

## Prerequisites

Install required tools:

```bash
pip install build twine
```

Optional but recommended:
```bash
# GitHub CLI for automated releases
brew install gh  # macOS
# or visit: https://cli.github.com/
```

## Version Numbering

Follow semantic versioning (semver):

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backward compatible  
- **Patch** (0.0.1): Bug fixes, backward compatible

## Release Notes

For each release, include:

- **New features** with examples
- **Bug fixes** and improvements
- **Breaking changes** (if any)
- **Migration notes** (if needed)

## Post-Release Checklist

After publishing:

- [ ] Verify package installs correctly: `pip install pyfr24==X.Y.Z`
- [ ] Check PyPI page: https://pypi.org/project/pyfr24/
- [ ] Monitor ReadTheDocs build: https://readthedocs.org/projects/pyfr24/builds/
- [ ] Test key functionality with new version
- [ ] Announce release (if significant)

## Troubleshooting

### Common Issues

**Build fails:**
- Check `setup.py` syntax
- Ensure all dependencies are listed
- Verify version format

**Upload fails:**
- Check API token permissions
- Verify package name availability
- Ensure version doesn't already exist

**ReadTheDocs doesn't rebuild:**
- Check webhook configuration
- Manually trigger build if needed
- Verify `.readthedocs.yaml` configuration

### Rolling Back

If you need to remove a bad release:

```bash
# Remove git tag
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# Remove GitHub release
gh release delete vX.Y.Z
```

Note: You cannot delete packages from PyPI, only "yank" them:
```bash
# Mark as yanked (discourages installation)
python -m twine upload --repository pypi --skip-existing --repository-url https://upload.pypi.org/legacy/ dist/*
```

## Automation Notes

The `publish.sh` script automates this entire process and includes:

- Interactive version bumping
- Comprehensive pre-flight checks
- Git operations with safety checks
- Automated testing
- PyPI publishing with confirmation prompts
- GitHub release creation
- Documentation update triggers

For production releases, always use the script to ensure consistency and reduce human error.