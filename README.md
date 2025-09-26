# gha-mergify-ci

A GitHub Action that detects which parts of your monorepo are affected by a pull request, so you can run only the relevant tests.

## The Problem

In monorepos, running all tests for every pull request wastes time and resources. While GitHub Actions offers path filtering:

```yaml
on:
  pull_request:
    paths:
      - 'js/**'
```

This approach has a critical flaw: when a job doesn't run, you can't tell if it was skipped due to the filter or if CI failed to start.
This becomes especially problematic with merge queues, where you don't want to skip tests on the second PR just because the first PR in the queue modified different files.

## The Solution

This action analyzes changed files and returns "scopes" indicating which parts of your codebase are affected. It's merge queue-aware, ignoring changes from PRs ahead in the queue to ensure accurate test selection.

When running in a merge queue context, the action automatically adds a `merge-queue` scope for integration tests.

## Usage

The example bellow demonstrate how to setup a monorepo containing a Python and a Javascript project.

The Python jobs will ran only if `*.py` are modified, same the Javascript jobs and `*.js` files.

An additional job called `integration` will run only when on Mergify merge-queue branches.

### 1. Configure Scopes

Create a `.mergify.yml` file in your repository root:

```yaml
scopes:
  source:
    files:
      python:
        includes:
          - **/*.py
      js:
        includes:
          - **/*.js

queue_rules:
    - name: default
      autoqueue: true
      queue_conditions:
        - check-success: alls-green
      merge_conditions:
        - check-success: alls-green
```

### 2. Set Up Your Workflow

```yaml
name: Continuous Integration
on:
  pull_request_target:
    types:
      - opened

jobs:
  scopes:
    runs-on: ubuntu-22.04
    outputs:
      js: ${{ fromJSON(steps.scopes.outputs.scopes).js }}
      python: ${{ fromJSON(steps.scopes.outputs.scopes).python }}
      merge-queue: ${{ fromJSON(steps.scopes.outputs.scopes).merge-queue }}
    steps:
      - uses: actions/checkout@v5
      - name: Get PR scopes
        id: scopes
        uses: Mergifyio/gha-mergify-ci
        with:
          action: scopes
          token: ${{ secrets.MERGIFY_TOKEN }}


  python:
    if: ${{ needs.scopes.outputs.python == 'true' }}
    needs: scopes
    uses: ./.github/workflows/python.yaml
    secrets: inherit

  js:
    if: ${{ needs.scopes.outputs.js == 'true' }}
    needs: scopes
    uses: ./.github/workflows/js.yaml
    secrets: inherit

  integration:
    if: ${{ needs.scopes.outputs.merge-queue == 'true' }}
    needs: scopes
    uses: ./.github/workflows/integration.yaml
    secrets: inherit

  alls-green:
    if: ${{ !cancelled() }}
    needs:
      - python
      - js
      - integration
    runs-on: ubuntu-latest
    steps:
      - name: Verify all jobs succeeded
        uses: re-actors/alls-green@release/v1
        with:
          allowed-skips: ${{ toJSON(needs) }}
          jobs: ${{ toJSON(needs) }}
```

## Outputs

Each scope defined in `.mergify.yml` becomes an output:
- `scopes.<scope-name>`: Returns `true` if the scope is affected, `false` otherwise
- `scopes.merge-queue`: Automatically set to `true` when running in a merge queue

## Requirements

- Python >= 3.10 (available in the runner environment)
