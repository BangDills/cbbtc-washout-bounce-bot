"""cbbtc-washout-bounce-bot: a 6-hour washout bounce with a trailing stop and a starter position."""

import collections
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

# Rolling history of CBBTC closes (maxlen 360)
history = collections.deque(maxlen=360)
closes_seen = 0
orders_sent = 0
position_type = None
peak = None
exit_sent = False


def on_batch(state, batch):
    global closes_seen, orders_sent, position_type, peak, exit_sent

    cbbtc_bar = None
    for bar in batch.get("bars", []):
        if bar.get("symbol") == "CBBTC":
            cbbtc_bar = bar
            break

    holding = state.positions.get("CBBTC")
    is_holding = holding is not None and holding.qty > 0

    if not is_holding:
        exit_sent = False

    # The peak must survive batches with no new bar for the symbol
    if cbbtc_bar is None:
        return []

    close = int(cbbtc_bar["c"])
    history.append(close)
    closes_seen += 1

    # Exit path: trailing stop while holding; a sell must never be sent twice for the same position
    if is_holding and not exit_sent:
        if peak is None or close > peak:
            peak = close

        trailing_bps = 100 if position_type == "starter" else 120
        if close * 10000 <= peak * (10000 - trailing_bps):
            qty = holding.qty
            val = state.value("CBBTC", qty, close)
            if val >= 1_000_000:
                orders_sent += 1
                exit_sent = True
                prev_peak = peak
                prev_type = position_type
                peak = None
                position_type = None
                sys.stderr.write(
                    f"[EXIT] seq={batch.get('seq')} type={prev_type} close={close} "
                    f"peak={prev_peak} trailing_bps={trailing_bps} qty={qty}\n"
                )
                sys.stderr.flush()
                return [
                    {
                        "side": "sell",
                        "symbol": "CBBTC",
                        "qty": qty,
                        "max_slippage_bps": 250,
                    }
                ]

    # Entry path: when flat
    if not is_holding and close is not None:
        # Starter position: if no order has ever been sent yet and at least 2 bars seen
        if orders_sent == 0 and closes_seen >= 2:
            notional = state.equity * 500 // 10000
            if notional >= 1_000_000:
                orders_sent += 1
                position_type = "starter"
                peak = close
                sys.stderr.write(
                    f"[ENTRY: starter] seq={batch.get('seq')} close={close} "
                    f"closes_seen={closes_seen} notional={notional}\n"
                )
                sys.stderr.flush()
                return [
                    {
                        "side": "buy",
                        "symbol": "CBBTC",
                        "notional_quote_units": notional,
                        "max_slippage_bps": 60,
                    }
                ]

        # Washout bounce entry: at least 361 closes seen (previous 360 complete), >= 4.50% drop from highest
        if closes_seen >= 361:
            highest = max(history)
            if close * 10000 <= highest * (10000 - 450):
                notional = state.cash
                if notional >= 1_000_000:
                    orders_sent += 1
                    position_type = "washout"
                    peak = close
                    sys.stderr.write(
                        f"[ENTRY: washout] seq={batch.get('seq')} close={close} "
                        f"highest_prev_360={highest} notional={notional}\n"
                    )
                    sys.stderr.flush()
                    return [
                        {
                            "side": "buy",
                            "symbol": "CBBTC",
                            "notional_quote_units": notional,
                            "max_slippage_bps": 60,
                        }
                    ]

    return []


if __name__ == "__main__":
    makefun_bars.run(on_batch)
