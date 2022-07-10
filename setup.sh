#!/usr/bin/env bash
REPOSITORY_TOKEN=$(aws codeartifact get-authorization-token --domain matdue --domain-owner 512206508224 --query authorizationToken --output text)
REPOSITORY_URL=$(aws codeartifact get-repository-endpoint --domain matdue --domain-owner 512206508224 --repository common --format pypi --query repositoryEndpoint --output text)
PIP_REPOSITORY=https://aws:${REPOSITORY_TOKEN}@${REPOSITORY_URL:8}simple/
pip install --index-url "$PIP_REPOSITORY" -e .[aws]
