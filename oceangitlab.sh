#!/bin/bash

export GITLAB_TOKEN=$(cat $HOME/Private/secret/gitlab-token)
export GITHUB_TOKEN=$(cat $HOME/Private/secret/github-token)
export LOG_LEVEL='TRACE'

# Example usage (to be reactivated as still in progress)
./gitlab-migrator -github-user=github@example.com  -gitlab-project=ocean/webapp/ocean-front  -github-repo=my-org/ocean-front-test -gitlab-domain=gitlab.example.com   -migrate-pull-requests -skip-invalid-merge-requests --max-concurrency 2

#./gitlab-migrator -github-user=github@example.com  -gitlab-project=ocean/documentation  -github-repo=my-org/documentation -gitlab-domain=gitlab.example.com   -migrate-pull-requests -skip-invalid-merge-requests --max-concurrency 4


# Example usage for database
#./gitlab-migrator -github-user=github@example.com  -gitlab-project=ocean/devops-tools/docker-images/ocean-postgres  -github-repo=my-org/ocean-postgres-test -gitlab-domain=gitlab.example.com  -migrate-pull-requests -skip-invalid-merge-requests -max-concurrency 1

