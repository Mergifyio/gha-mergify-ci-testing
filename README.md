# gha-mergify-merge-queue-checking-base-sha

A GitHub Action that retrieves the correct base SHA for CI when using Mergify merge queue.

## Problem

When using Mergify's merge queue, the merge queue creates temporary pull requests with branches named `mergify/merge-queue/*`. These temporary PRs have a different base than the original PR, which causes issues with change detection tools like [`dorny/paths-filter`](https://github.com/dorny/paths-filter).

Without this action, CI workflows that rely on detecting changed files will compare against the wrong base commit, potentially:
- Running unnecessary tests on unchanged code
- Missing changes that should trigger specific CI steps
- Causing inconsistent CI behavior between regular PRs and merge queue PRs

## Solution

This action extracts the original base SHA from the merge queue metadata embedded in the temporary PR's description. The extracted SHA can then be used by change detection tools to properly identify which files have changed.

## Usage

```yaml
name: Continuous Integration
on:
  pull_request_target:
    types:
      - opened

jobs:
  test:
    runs-on: ubuntu-22.04
    outputs:
      docker: ${{ steps.changes.outputs.docker }}
    steps:
      - uses: actions/checkout@v5

      - name: Get base SHA for change detection
        id: mergify-checking-base
        uses: Mergifyio/gha-mergify-merge-queue-checking-base-sha

      - name: Detect changes
        uses: dorny/paths-filter@v3
        id: changes
        with:
          base: ${{ steps.mergify-checking-base.outputs.checking_base_sha }}
          filters: |
            docker:
              - dockerfiles/**
              - datadog/**
              - datadog-wrapper.sh
              - onpremise/**
              - fake.env
              - .github/workflows/docker-*.yaml
```

## How it works

1. The action only runs when the PR branch starts with `mergify/merge-queue/`
2. It uses GitHub CLI to fetch the merge queue PR's description
3. It extracts the YAML metadata block containing the original `checking_base_sha`
4. It outputs this SHA for use by subsequent workflow steps

## Outputs

- `checking_base_sha`: The base SHA that CI should use to detect changed files

## Requirements

This action requires the following tools to be available in the runner:
- GitHub CLI (`gh`)
- `yq` (YAML processor)
