#!/usr/bin/env python3
"""
Script to update the version number in setup.py.
Usage: python update_version.py <new_version>
Example: python update_version.py 0.1.1
"""

import re
import sys

def update_version(new_version):
    """Update the version number in setup.py."""
    with open('setup.py', 'r') as f:
        content = f.read()
    
    # Update version in setup.py
    new_content = re.sub(
        r"version=['\"][^'\"]*['\"]",
        f"version='{new_version}'",
        content
    )
    
    with open('setup.py', 'w') as f:
        f.write(new_content)
    
    print(f"Updated version to {new_version} in setup.py")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        print("Example: python update_version.py 0.1.1")
        sys.exit(1)
    
    new_version = sys.argv[1]
    update_version(new_version) 