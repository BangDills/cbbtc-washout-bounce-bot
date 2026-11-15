# cbbtc-washout-bounce-bot

A 6-hour washout bounce trading bot for CBBTC with a trailing stop and a small starter position.

## Strategy Summary

- **Starter Position**: Buys 5.00% of equity once at least 2 bars have been observed and no prior order has been sent.
- **Washout Entry**: When flat and after observing at least 360 completed previous closes (361 closes total), buys using all available cash if the latest close is at least 4.50% below the highest close among those previous 360 closes.
- **Trailing Stop Exit**: Tracks the highest close since position entry. Sells the entire held quantity when price drops by the trailing stop distance (1.00% for starter position, 1.20% for washout position).

## How to Run

Run the bot with standard Python 3.13:

```bash
python3 -P -s main.py
```
