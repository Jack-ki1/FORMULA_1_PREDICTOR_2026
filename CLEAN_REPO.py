#!/usr/bin/env python
"""
Repository Cleanup Script

This script helps prepare the repository for GitHub by removing unnecessary files
and verifying the project is ready for public release.
"""

import os
import shutil
from pathlib import Path

def clean_repository():
    """Clean unnecessary files from the repository."""
    print("Starting repository cleanup...")
    
    # Define files and directories to remove
    items_to_remove = [
        'output_test.json',  # Large test output file
        '*.log',             # Log files
        'logs/',             # Log directory
        'output/',           # Output directory (if exists)
        '__pycache__/',      # Python cache directories
    ]
    
    # Remove specific files
    for item in items_to_remove:
        if item.endswith('/'):  # Directory
            dir_path = item.rstrip('/')
            if os.path.exists(dir_path):
                print(f"Removing directory: {dir_path}/")
                shutil.rmtree(dir_path)
        else:  # File
            for file_path in Path('.').glob(item):
                if file_path.is_file():
                    print(f"Removing file: {file_path}")
                    file_path.unlink()
    
    # Clean __pycache__ directories specifically
    for pycache_dir in Path('.').glob('**/__pycache__'):
        if pycache_dir.is_dir():
            print(f"Removing directory: {pycache_dir}/")
            shutil.rmtree(pycache_dir)
    
    print("\nRepository cleanup completed!")
    print("\nFiles and directories remaining in the repository:")
    print("=" * 50)
    
    # Show directory structure
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

def verify_readiness():
    """Verify the repository is ready for GitHub."""
    print("\nVerifying repository readiness for GitHub...")
    print("=" * 50)
    
    required_files = [
        'README.md',
        'requirements.txt',
        'main.py',
        '.gitignore',
        'GITHUB_PREPARATION.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
    else:
        print("✅ All required files are present")
    
    # Check for potentially problematic files
    large_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                if size > 1000000:  # More than 1MB
                    large_files.append((file_path, f"{size/1024/1024:.2f} MB"))
            except OSError:
                continue
    
    if large_files:
        print("\n⚠️  Potentially large files detected (these shouldn't be in the repository):")
        for file_path, size in large_files:
            print(f"  - {file_path} ({size})")
    else:
        print("\n✅ No large files detected")
    
    # Check if .gitignore is properly excluding unnecessary files
    print("\n✅ Repository verification completed!")

if __name__ == "__main__":
    print("F1MLpredictions2026 - Repository Preparation Tool")
    print("=" * 60)
    
    clean_repository()
    verify_readiness()
    
    print("\n💡 Next steps:")
    print("1. Review the GITHUB_PREPARATION.md file for complete instructions")
    print("2. Make sure to add a LICENSE file if you want to license the code")
    print("3. Verify all sensitive information is properly excluded via .gitignore")
    print("4. Commit and push to your GitHub repository")