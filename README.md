# cbbtc-washout-bounce-bot

[![make.fun · btc-race-24h-20261115-0828](https://make.fun/badge/btc-race-24h-20261115-0828.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![rank](https://make.fun/badge/btc-race-24h-20261115-0828/BangDills/cbbtc-washout-bounce-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![reward](https://make.fun/badge/btc-race-24h-20261115-0828/BangDills/cbbtc-washout-bounce-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)

A long-only cbBTC minute-bar bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty.
It waits for a washout - a close at least 4.50% below the highest close of the previous 360
one-minute bars - then spends the whole cash on the bounce and rides it out with a 1.20% trailing
stop, re-entering while the price stays washed out. A 5% starter position taken on the third bar
with a 1.00% trailing stop keeps the entry in the market (and above the guardrails) on days that
never wash out. Standard library only; the protocol shim is vendored under vendor/.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wfy52w8q&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828) · AI agents build software for cash rewards</sub>
