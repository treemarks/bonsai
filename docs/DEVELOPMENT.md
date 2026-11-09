# Development

[Home](../README.md) · [Setup](../SETUP.md) · [Usage](USAGE.md) · [Accounts & data](ACCOUNTS.md)

```bash
/usr/bin/python3 -m unittest discover -s tests                        # stock macOS python, no network, no real logins
/usr/bin/python3 -m unittest discover -s review -p test_astra_regressions.py   # the adversarial review's acceptance tests
BONSAI_POOLS_HOME=/tmp/fakehome BONSAI_STATE=/tmp/bonsai-state ./bonsai gauge --once --no-color
```

`BONSAI_POOLS_HOME` points discovery at another home (the tests use a synthetic one);
`BONSAI_STATE` and `BONSAI_CONFIG` move the cache and config. Standard library only; one file.

The `bonsai` file is generated from the Treemarks pool gauge's shared core, and shares its
provider-reading library with the fleet: a fix lands there and is published here, so a pull
request on this file is read as a report, not merged as code. The docs' pictures (the `images`
folder beside these pages) are kept in this repository itself.
Bonsai is MIT-licensed. It began as a handoff for someone with one Mac, one personal plan and an
institution's seats, who wanted the Treemarks pool gauge in miniature.
