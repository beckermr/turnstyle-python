# turnstyle-python

[![test](https://github.com/beckermr/turnstyle-python/actions/workflows/tests.yml/badge.svg)](https://github.com/beckermr/turnstyle-python/actions/workflows/tests.yml)

a python implementation of [softprops/turnstyle](https://github.com/softprops/turnstyle)

See their documentation. This action works the same except that the branch input parameter is not supported and the github token 
should be passed as an input via `github-token`.

Here is an example

```yaml
name: test
on:
  push:
    branches:
      - main
  pull_request: null

jobs:
  test:
    runs-on: ubuntu-latest
    name: test
    steps:
      - name: run
        id: turnstyle
        uses: beckermr/turnstyle-python@v1
        with:
          poll-interval-seconds: 5    # checks the status of any previous runs at this interval
          continue-after-seconds: 10  # continue after 10 seconds
          # abort-after-seconds: 10   # use this to abort instead of continue 
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: run
        run: |
          echo "worked!"
          echo "force-continue: '${FC}'"
        env:
          FC: ${{ steps.turnstyle.outputs.force_continued }}
```
