#!/bin/bash

# A script to automate the publishing of the pyfr24 package to PyPI.
# It handles version bumping, git operations, PyPI publishing, and documentation updates.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting the pyfr24 publishing process..."
echo "========================================="

# --- 1. Version Management ---
echo "--- Version Management ---"

# Extract current version from setup.py
CURRENT_VERSION=$(grep "version=" setup.py | sed 's/.*version=//' | sed "s/[',]//g" | xargs)

if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Could not find version in setup.py"
    exit 1
fi

echo "Current version: $CURRENT_VERSION"
echo
echo "What type of version bump do you want?"
select bump_type in "patch (0.1.7 → 0.1.8)" "minor (0.1.7 → 0.2.0)" "major (0.1.7 → 1.0.0)" "custom" "no change"; do
    case $bump_type in
        "patch"* )
            NEW_VERSION=$(python3 -c "
import re
v = '$CURRENT_VERSION'
parts = v.split('.')
parts[2] = str(int(parts[2]) + 1)
print('.'.join(parts))
")
            break
            ;;
        "minor"* )
            NEW_VERSION=$(python3 -c "
import re
v = '$CURRENT_VERSION'
parts = v.split('.')
parts[1] = str(int(parts[1]) + 1)
parts[2] = '0'
print('.'.join(parts))
")
            break
            ;;
        "major"* )
            NEW_VERSION=$(python3 -c "
import re
v = '$CURRENT_VERSION'
parts = v.split('.')
parts[0] = str(int(parts[0]) + 1)
parts[1] = '0'
parts[2] = '0'
print('.'.join(parts))
")
            break
            ;;
        "custom" )
            read -p "Enter new version number: " NEW_VERSION
            break
            ;;
        "no change" )
            NEW_VERSION=$CURRENT_VERSION
            break
            ;;
        * )
            echo "Invalid option. Please choose 1-5."
            ;;
    esac
done

echo "Publishing version: $NEW_VERSION"

# --- 2. Git Status Check ---
echo "--- Git Status Check ---"
if ! git diff-index --quiet HEAD --; then
    echo "Warning: Uncommitted changes detected in your working directory."
    git status --porcelain
    echo
    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Publishing cancelled. Please commit your changes."
        exit 1
    fi
fi
echo "✅ Git status checked."

# --- 3. Pre-flight Checklist ---
echo "--- Pre-flight Checklist ---"

# Check if we need to update version files
if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    echo "Updating version in files..."
    
    # Update setup.py
    sed -i.bak "s/version=['\"]$CURRENT_VERSION['\"]/version=\"$NEW_VERSION\"/" setup.py
    
    # Update __init__.py if it exists
    if [ -f "pyfr24/__init__.py" ]; then
        sed -i.bak "s/__version__ = ['\"]$CURRENT_VERSION['\"]/__version__ = \"$NEW_VERSION\"/" pyfr24/__init__.py
    fi
    
    # Update CHANGELOG.md - move [Unreleased] to new version
    if [ -f "CHANGELOG.md" ]; then
        TODAY=$(date +%Y-%m-%d)
        sed -i.bak "s/## \[Unreleased\]/## [Unreleased]\n\n## [$NEW_VERSION] - $TODAY/" CHANGELOG.md
    fi
    
    # Remove backup files
    rm -f setup.py.bak pyfr24/__init__.py.bak CHANGELOG.md.bak
    
    echo "✅ Version files updated to $NEW_VERSION"
fi

read -p "Have you verified the CHANGELOG.md is up to date? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing cancelled. Please update the CHANGELOG.md."
    exit 1
fi

read -p "Have you tested the new features and verified they work? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing cancelled. Please test your changes."
    exit 1
fi

read -p "Are the documentation updates complete and accurate? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing cancelled. Please update documentation."
    exit 1
fi

# --- 4. Final Confirmation ---
echo "--- Final Confirmation ---"
echo "Ready to publish pyfr24 version $NEW_VERSION"
echo "This will:"
echo "  - Commit and push changes to GitHub"
echo "  - Create a git tag v$NEW_VERSION"
echo "  - Build and upload to PyPI"
echo "  - Create a GitHub release"
echo "  - Trigger ReadTheDocs rebuild"
echo

read -p "Proceed with publishing? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing cancelled."
    exit 1
fi

# --- 5. Run Tests ---
echo "--- Running Tests ---"
if [ -f "run_tests.py" ]; then
    if ! python3 run_tests.py; then
        echo "Error: Tests failed. Please fix the tests before publishing."
        exit 1
    fi
elif [ -f "tests/" ]; then
    if ! python3 -m pytest tests/; then
        echo "Error: Pytest tests failed. Please fix the tests before publishing."
        exit 1
    fi
else
    echo "Warning: No test files found. Proceeding without tests."
fi
echo "✅ Tests passed."

# --- 6. Prerequisite Check ---
echo "--- Checking Tools ---"
command -v python3 >/dev/null 2>&1 || { echo >&2 "Error: python3 is not installed. Aborting."; exit 1; }
python3 -m pip show build >/dev/null 2>&1 || { echo >&2 "Error: 'build' is not installed. Run 'pip install build'. Aborting."; exit 1; }
python3 -m pip show twine >/dev/null 2>&1 || { echo >&2 "Error: 'twine' is not installed. Run 'pip install twine'. Aborting."; exit 1; }
HAS_GH=$(command -v gh >/dev/null 2>&1 && echo "true" || echo "false")
echo "✅ Required tools found."

# --- 7. Git Operations ---
echo "--- Git Operations ---"

# Commit version changes if any
if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    git add setup.py CHANGELOG.md
    if [ -f "pyfr24/__init__.py" ]; then
        git add pyfr24/__init__.py
    fi
    git commit -m "Bump version to $NEW_VERSION"
    echo "✅ Version bump committed."
fi

# Push to GitHub
echo "Pushing to GitHub..."
git push origin main
echo "✅ Pushed to GitHub."

# Create and push tag
TAG="v$NEW_VERSION"
echo "Creating tag $TAG..."
git tag "$TAG"
git push origin "$TAG"
echo "✅ Tag created and pushed."

# --- 8. Build Package ---
echo "--- Building Package ---"
echo "Cleaning up previous builds..."
rm -rf build dist pyfr24.egg-info
echo "Building the package..."
python3 -m build
echo "✅ Build complete. Files created:"
ls -la dist/

# --- 9. Publish to PyPI ---
echo "--- Publishing to PyPI ---"
echo
echo "Where would you like to publish?"
select choice in "TestPyPI (for testing)" "PyPI (Official - Live)" "Skip publishing"; do
    case $choice in
        "TestPyPI"* )
            echo "Uploading to TestPyPI..."
            if [ -z "$PYPI_TEST" ]; then
                echo "Error: PYPI_TEST environment variable is not set."
                echo "Please set it with your TestPyPI API token."
                exit 1
            fi
            python3 -m twine upload --repository-url https://test.pypi.org/legacy/ -u __token__ -p "$PYPI_TEST" dist/*
            echo
            echo "✅ Successfully published to TestPyPI!"
            echo "View at: https://test.pypi.org/project/pyfr24/$NEW_VERSION/"
            echo "Install with: pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple pyfr24==$NEW_VERSION"
            break
            ;;
        "PyPI"* )
            read -p "⚠️  Publishing to OFFICIAL PyPI. This is permanent. Continue? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                if [ -z "$PYPI" ]; then
                    echo "Error: PYPI environment variable is not set."
                    echo "Please set it with your PyPI API token."
                    exit 1
                fi
                echo "Uploading to PyPI..."
                python3 -m twine upload -u __token__ -p "$PYPI" dist/*
                echo
                echo "✅ Successfully published to PyPI!"
                echo "Package is live at: https://pypi.org/project/pyfr24/$NEW_VERSION/"
                echo "Install with: pip install pyfr24==$NEW_VERSION"
            else
                echo "PyPI publishing cancelled."
            fi
            break
            ;;
        "Skip"* )
            echo "Skipping PyPI publishing."
            break
            ;;
        * )
            echo "Invalid option. Please choose 1, 2, or 3."
            ;;
    esac
done

# --- 10. GitHub Release ---
echo "--- GitHub Release ---"
read -p "Create a GitHub release for v$NEW_VERSION? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ "$HAS_GH" = "false" ]; then
        echo "Warning: GitHub CLI ('gh') not found."
        echo "Please create the release manually: https://github.com/stiles/pyfr24/releases/new"
    else
        echo "Creating GitHub release..."
        
        # Extract release notes from CHANGELOG.md
        NOTES=$(awk '/^## \['"$NEW_VERSION"'\]/{flag=1; next} /^## \[/{flag=0} flag' CHANGELOG.md)
        
        if [ -z "$NOTES" ]; then
            echo "Warning: Could not extract release notes from CHANGELOG.md."
            NOTES="Release version $NEW_VERSION with enhanced visualizations, timezone conversion, and professional chart design."
        fi
        
        echo "Creating release with these notes:"
        echo "$NOTES"
        echo
        
        gh release create "$TAG" dist/* \
            --title "Release $TAG" \
            --notes "$NOTES"
        
        echo "✅ GitHub release created successfully!"
        echo "View at: https://github.com/stiles/pyfr24/releases/tag/$TAG"
    fi
fi

# --- 11. Documentation ---
echo "--- Documentation ---"
echo "ReadTheDocs will automatically rebuild from the new tag."
echo "Monitor the build at: https://readthedocs.org/projects/pyfr24/builds/"

# --- 12. Summary ---
echo
echo "========================================="
echo "🎉 Publishing process completed!"
echo "========================================="
echo "Version: $NEW_VERSION"
echo "Tag: $TAG"
echo "GitHub: https://github.com/stiles/pyfr24/releases/tag/$TAG"
if [[ $choice == "PyPI"* ]]; then
    echo "PyPI: https://pypi.org/project/pyfr24/$NEW_VERSION/"
fi
echo "Docs: https://pyfr24.readthedocs.io/"
echo
echo "Next steps:"
echo "- Monitor ReadTheDocs build status"
echo "- Test installation: pip install pyfr24==$NEW_VERSION"
echo "- Announce the release!"
echo "========================================="