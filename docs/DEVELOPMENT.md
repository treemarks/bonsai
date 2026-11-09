# Development

[Home](../README.md) · [Setup](../SETUP.md) · [Usage](USAGE.md) · [Accounts & data](ACCOUNTS.md)

```bash
/usr/bin/python3 -m unittest discover -s tests                        # stock macOS python, no network, no real logins
/usr/bin/python3 -m unittest review/test_astra_regressions.py         # the adversarial review's 51 acceptance tests
BONSAI_POOLS_HOME=/tmp/fakehome BONSAI_STATE=/tmp/bonsai-state ./bonsai gauge --once --no-color
```

`BONSAI_POOLS_HOME` points discovery at another home (the tests use a synthetic one);
`BONSAI_STATE` and `BONSAI_CONFIG` move the cache and config. Standard library only; one file.
`review/` holds the terms digest, the briefs of the five adversarial passes this release was
checked against, and the tests they produced. Bonsai is MIT-licensed. It began as a handoff for
someone with one Mac, one personal plan and an institution's seats, who wanted the Treemarks
pool gauge in miniature.
