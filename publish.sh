#!/bin/bash

# A script to automate the publishing of the pyfr24 package to PyPI.
# It handles version bumping, git operations, PyPI publishing, and documentation updates.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting the pyfr24 publishing process..."
echo "========================================="

# --- 1. Version Management ---
echo "--- Version Management ---"

# The version is defined once, in pyfr24/__init__.py, and setup.py parses it
# from there. Keeping a second literal in setup.py is what shipped 0.2.0
# reporting itself as 1.0.0.
CURRENT_VERSION=$(grep "^__version__" pyfr24/__init__.py | sed 's/.*= *//' | tr -d "\"'" | xargs)

if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Could not find __version__ in pyfr24/__init__.py"
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

if [ "$NEW_VERSION" != "$CURRENT_VERSION" ] && git rev-parse "v$NEW_VERSION" >/dev/null 2>&1; then
    echo "Error: tag v$NEW_VERSION already exists. Pick another version."
    exit 1
fi

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
    
    # Rewrite the line outright rather than matching on the old version, so a
    # file that has somehow drifted still lands on the right number.
    sed -i.bak "s/^__version__ = .*/__version__ = \"$NEW_VERSION\"/" pyfr24/__init__.py
    
    # Update CHANGELOG.md - move [Unreleased] to new version
    if [ -f "CHANGELOG.md" ]; then
        if grep -q "^## \[$NEW_VERSION\]" CHANGELOG.md; then
            echo "Note: CHANGELOG.md already has a [$NEW_VERSION] heading; leaving it as is."
        else
            TODAY=$(date +%Y-%m-%d)
            sed -i.bak "s/## \[Unreleased\]/## [Unreleased]\n\n## [$NEW_VERSION] - $TODAY/" CHANGELOG.md
        fi
    fi
    
    # Remove backup files
    rm -f pyfr24/__init__.py.bak CHANGELOG.md.bak
    
    # An empty section here means the GitHub release notes would come out empty.
    if ! awk '/^## \['"$NEW_VERSION"'\]/{flag=1; next} /^## \[/{flag=0} flag' CHANGELOG.md | grep -q '[^[:space:]]'; then
        echo "Warning: no release notes found under [$NEW_VERSION] in CHANGELOG.md."
        echo "The GitHub release would fall back to a generic description."
    fi
    
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
echo "  - Create a GitHub release, which triggers the PyPI upload"
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
HAS_GH=$(command -v gh >/dev/null 2>&1 && echo "true" || echo "false")
echo "✅ Required tools found."

# --- 7. Git Operations ---
echo "--- Git Operations ---"

# Commit version changes if any
if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    git add pyfr24/__init__.py CHANGELOG.md
    git commit -m "chore(release): v$NEW_VERSION"
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

# --- 9. GitHub Release ---
# Publishing to PyPI belongs to .github/workflows/publish.yml, which runs on
# release. Uploading from here as well left every Publish run failing with
# "400 File already exists" after the package had already gone out.
echo "--- GitHub Release ---"
echo "Creating the release triggers the PyPI upload. Skip it and nothing publishes."
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
echo "Docs: https://pyfr24.readthedocs.io/"
echo
echo "Next steps:"
echo "- Watch the PyPI upload: gh run watch \$(gh run list --workflow='Publish to PyPI' --limit 1 --json databaseId -q '.[0].databaseId')"
echo "- Once it's green: pip install --no-cache-dir --upgrade pyfr24"
echo "- Monitor ReadTheDocs build status"
echo "========================================="