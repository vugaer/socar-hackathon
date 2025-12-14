#!/usr/bin/env python3
"""
Deploy README files to Drillica repository and push to Git
Team Drillica - SOCAR Hackathon 2024
"""

import os
from pathlib import Path
import subprocess
import sys
import json

def run_command(cmd, cwd=None):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def create_readme_file(filepath, content):
    """Create README file with content"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Created: {filepath}")

def main():
    print("="*70)
    print("DRILLICA README DEPLOYMENT SCRIPT")
    print("Team Drillica - SOCAR Hackathon 2024")
    print("="*70)
    print()

    # Load README content from JSON
    print("Loading README content from all_readme_files.csv...")

    import pandas as pd
    df = pd.read_csv('all_readme_files.csv')

    readme_files = dict(zip(df['path'], df['content']))

    print(f"Loaded {len(readme_files)} README files")
    print()

    # Create all README files
    print("Creating README files...")
    for path, content in readme_files.items():
        create_readme_file(path, content)

    print()
    print("="*70)
    print("GIT OPERATIONS")
    print("="*70)
    print()

    # Check if we're in a git repository
    if not Path('.git').exists():
        print("⚠ Not a git repository. Initializing...")
        run_command('git init')

    # Add README files to git
    print("Adding README files to git...")
    for path in readme_files.keys():
        run_command(f'git add {path}')

    # Check git status
    print("\nGit status:")
    status = run_command('git status --short')
    if status:
        print(status)

    # Commit
    commit_msg = "docs: Add comprehensive README documentation for all components\n\n- Root README with platform architecture\n- CaspianPetro library documentation\n- Data Vault 2.0 implementation guide\n- Apache Airflow ETL pipeline docs\n- Dimensional model and analytics docs\n- Dashboard and time travel features\n\nTeam Drillica - SOCAR Hackathon 2024"

    print("\nCommitting changes...")
    commit_result = run_command(f'git commit -m "{commit_msg}"')

    if commit_result:
        print("✓ Commit successful")
    else:
        print("⚠ Nothing to commit or commit failed")

    # Ask user about pushing
    print("\n" + "="*70)
    push_confirm = input("Do you want to push to remote? (yes/no): ").lower()

    if push_confirm in ['yes', 'y']:
        # Check if remote exists
        remote_check = run_command('git remote -v')

        if not remote_check:
            print("\n⚠ No remote repository configured.")
            remote_url = input("Enter remote repository URL (or 'skip' to skip push): ")

            if remote_url.lower() != 'skip':
                run_command(f'git remote add origin {remote_url}')
                print(f"✓ Added remote: {remote_url}")

        # Get current branch
        branch = run_command('git branch --show-current')
        if branch:
            branch = branch.strip()
        else:
            branch = 'main'

        print(f"\nPushing to remote (branch: {branch})...")
        push_result = run_command(f'git push -u origin {branch}')

        if push_result is not None:
            print("✓ Push successful!")
        else:
            print("⚠ Push failed. You may need to pull first or resolve conflicts.")
            print("   Run manually: git pull origin {branch} --rebase")
            print("   Then: git push origin {branch}")
    else:
        print("\nSkipping push. You can push later with:")
        print("  git push origin main")

    print("\n" + "="*70)
    print("DEPLOYMENT COMPLETE")
    print("="*70)
    print()
    print("Summary:")
    print(f"  - Created {len(readme_files)} README files")
    print("  - Files committed to git")
    print("  - Ready for collaboration")
    print()
    print("Next steps:")
    print("  1. Review the README files")
    print("  2. Test the documentation links")
    print("  3. Share with your team!")
    print()

if __name__ == '__main__':
    main()
