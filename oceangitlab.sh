#!/bin/bash

export GITLAB_TOKEN=$(cat $HOME/Private/.oraaccountgitlab-token)
#export GITHUB_TOKEN=$(cat $HOME/Private/.shiftmoverootgithub-token)
export GITHUB_TOKEN=$(cat $HOME/Private/.shiftmoverootgithub-token_personal)
export LOG_LEVEL='TRACE'

# Pour ocean-front
./gitlab-migrator -github-user=github@ocean.fr  -gitlab-project=ocean/webapp/ocean-front  -github-repo=ocean-shiftmove/ocean-front-test -gitlab-domain=sourcehub.orange-business.com   -migrate-pull-requests -skip-invalid-merge-requests --max-concurrency 1


# Pour ocean-postgres 
#./gitlab-migrator -github-user=github@ocean.fr  -gitlab-project=ocean/devops-tools/docker-images/ocean-postgres  -github-repo=ocean-shiftmove/ocean-postgres-test -gitlab-domain=sourcehub.orange-business.com  -migrate-pull-requests -skip-invalid-merge-requests -max-concurrency 1

