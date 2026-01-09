#!/usr/bin/env python3
"""
Generate bulk migration CSV from ghorg directory structure with optional topics.

This script scans a ghorg directory (GitLab organization clone) and generates:
- CSV file with columns: gitlab_path,github_path,topics

Usage:
    python3 generate_migration_csv.py
    python3 generate_migration_csv.py --ghorg-path ~/ghorg/my-instance --github-org my-org
    python3 generate_migration_csv.py --ghorg-path ~/ghorg/my-instance --github-org my-org --output migration.csv
"""

import os
import csv
import argparse
from pathlib import Path
from collections import defaultdict


def find_repositories(ghorg_path):
    """Find all git repositories in ghorg directory."""
    repos = []
    for git_dir in ghorg_path.rglob(".git"):
        if git_dir.is_dir():
            repo_path = git_dir.parent
            rel_path = repo_path.relative_to(ghorg_path)
            parts = list(rel_path.parts)

            # Skip if too shallow (no hierarchy)
            if len(parts) < 2:
                continue

            # Skip the domain (first part) for gitlab_path
            # e.g., example.com/ocean/... -> ocean/...
            gitlab_parts = parts[1:] if len(parts) > 1 else parts

            repos.append({
                'full_path': str(repo_path),
                'rel_path': gitlab_parts,
                'gitlab_path': '/'.join(gitlab_parts),
                'repo_name': parts[-1]
            })

    return repos


def identify_conflicts(repos):
    """Identify repositories with duplicate names in different paths."""
    name_counts = defaultdict(list)
    for repo in repos:
        name_counts[repo['repo_name']].append(repo)

    return {name: items for name, items in name_counts.items() if len(items) > 1}


def generate_migration_data(repos, github_org, conflicts):
    """Generate CSV entries with minimal unique GitHub paths."""
    csv_rows = []

    for repo in sorted(repos, key=lambda x: x['gitlab_path']):
        hierarchy = repo['rel_path']

        # Find minimum suffix depth that makes this repo unique
        github_path = None
        for depth in range(1, len(hierarchy) + 1):
            candidate = '-'.join(hierarchy[-depth:])

            # Check if any other repo would have the same suffix at this depth
            has_collision = False
            for other_repo in repos:
                if other_repo is repo:
                    continue

                other_hierarchy = other_repo['rel_path']
                # Get the same depth suffix from the other repo
                if len(other_hierarchy) >= depth:
                    other_candidate = '-'.join(other_hierarchy[-depth:])
                    if candidate == other_candidate:
                        has_collision = True
                        break

            if not has_collision:
                github_path = candidate
                break

        # Fallback (should rarely happen)
        if github_path is None:
            github_path = '-'.join(hierarchy)

        # Topics from hierarchy, skipping last part (repo name)
        # Domain is already stripped, so for ocean/applications-mobiles/I4M
        # We want: ocean|applications-mobiles (skip repo name only)
        topics = list(hierarchy[:-1]) if len(hierarchy) > 1 else []

        # CSV row
        csv_rows.append({
            'gitlab_path': repo['gitlab_path'],
            'github_path': f"{github_org}/{github_path}",
            'topics': '|'.join(topics) if topics else ''
        })

    return csv_rows


def print_summary(repos, csv_rows, conflicts):
    """Print summary statistics."""
    all_topics = set()
    conflict_repos = 0
    total_topics_assigned = 0

    for row in csv_rows:
        if row['topics']:
            all_topics.update(row['topics'].split(','))
            total_topics_assigned += 1
        for repo in [r for r in repos if r['gitlab_path'] == row['gitlab_path']]:
            if repo['repo_name'] in conflicts:
                conflict_repos += 1
                break

    print(f"\n{'='*60}")
    print(f"MIGRATION CSV GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total repositories found:          {len(repos)}")
    print(f"Total unique naming conflicts:     {len(conflicts)}")
    print(f"Repositories with conflicts:       {conflict_repos}")
    print(f"Repositories with topics:          {total_topics_assigned}")
    print(f"Unique topics generated:           {len(all_topics)}")
    print(f"CSV rows generated:                {len(csv_rows)}")
    print(f"{'='*60}\n")

    if conflicts:
        print("Naming Conflicts:")
        for name, items in sorted(conflicts.items()):
            print(f"  • {name}: {len(items)} repos")
            for item in items:
                print(f"      - {item['gitlab_path']}")
        print()

    if all_topics:
        print(f"Topics ({len(all_topics)}):")
        topics_list = sorted(all_topics)
        for i in range(0, len(topics_list), 5):
            chunk = topics_list[i:i+5]
            print(f"  • {', '.join(chunk)}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Generate migration CSV with topics from ghorg structure'
    )
    parser.add_argument(
        '--ghorg-path',
        type=str,
        default=os.path.expanduser('~/ghorg/my-gitlab-instance'),
        help='Path to ghorg directory (default: ~/ghorg/my-gitlab-instance)'
    )
    parser.add_argument(
        '--github-org',
        type=str,
        default='my-github-org',
        help='GitHub organization name (default: my-github-org)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='migration.csv',
        help='Output CSV file path (default: migration.csv)'
    )

    args = parser.parse_args()

    ghorg_path = Path(args.ghorg_path).expanduser()
    output_file = Path(args.output).expanduser()

    if not ghorg_path.exists():
        print(f"Error: ghorg path does not exist: {ghorg_path}")
        exit(1)

    print(f"Scanning repositories in: {ghorg_path}")
    repos = find_repositories(ghorg_path)

    if not repos:
        print("Error: No repositories found")
        exit(1)

    print(f"Found {len(repos)} repositories")
    print(f"Identifying naming conflicts...")
    conflicts = identify_conflicts(repos)

    print(f"Generating migration data...")
    csv_rows = generate_migration_data(repos, args.github_org, conflicts)

    # Write CSV
    print(f"Writing CSV to: {output_file}")
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['gitlab_path', 'github_path', 'topics'])
        writer.writeheader()
        writer.writerows(csv_rows)

    # Print summary
    print_summary(repos, csv_rows, conflicts)

    print(f"✅ Generated: {output_file}")


if __name__ == '__main__':
    main()
