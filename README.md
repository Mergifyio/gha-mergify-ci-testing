# gha-mergify-merge-queue-checking-base-sha

Retrieve the base sha the CI should used to detect changed files

To use:

```yaml
name: Continous Integration
on:
  pull_request_target:
    types:
      - opened

jobs:
  test
    runs-on: ubuntu-22.04
    steps:
      - name: Checking base sha
        id: mergify-checking-base
        uses: Mergifyio/gha-mergify-merge-queue-checking-base-sha

    outputs:
      docker: ${{ steps.changes.outputs.docker }}
    steps:
      - uses: actions/checkout@v5
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          base: ${{ steps.mergify-checking-base.checking_base_sha }}
          filters: |
            docker:
              - dockerfiles/**
              - datadog/**
              - datadog-wrapper.sh
              - onpremise/**
              - fake.env
              - .github/workflows/docker-*.yaml
```
