"""test_bot.py: Standard-library test harness for cbbtc-washout-bounce-bot."""

import json
import subprocess
import sys


def main():
    cmd = [sys.executable, "-P", "-s", "main.py"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    quote_units = 100_000_000  # 100 USDC initial capital
    cash = quote_units
    positions = []

    # Hello message
    hello = {
        "type": "hello",
        "protocol": "agent-fun/bars-replay/v1",
        "seed": "0",
        "warmup_bars": 0,
        "caps": {
            "max_orders_per_bar": 16,
            "max_weight_bps": 10000,
            "max_open_positions": 1,
        },
        "capital": {
            "quote_units": str(cash),
            "quote_scale": 6,
        },
        "symbols": [
            {
                "symbol": "CBBTC",
                "qty_scale": 8,
                "price_scale": 6,
            }
        ],
    }

    proc.stdin.write(json.dumps(hello) + "\n")
    proc.stdin.flush()

    # Build price series:
    # 0: 100m
    # 1: 100m -> Starter buy (5% of equity)
    # 2: 98.9m -> Starter exit (1.10% drop > 1.00% trailing stop)
    # 3..359: 100m -> History accumulation (reaches 360 bars)
    # 360: 95m -> Washout entry (5.00% drop > 4.50% from 100m high)
    # 361: 96m -> Recovery, peak updates to 96m
    # 362: None -> No bar for CBBTC while holding (peak 96m must survive)
    # 363: 94.5m -> Washout exit (drop from surviving 96m peak to 94.5m is > 1.20% trailing stop)
    # 364: 95m -> Flat
    prices = {}
    prices[0] = 100_000_000
    prices[1] = 100_000_000
    prices[2] = 98_900_000
    for i in range(3, 360):
        prices[i] = 100_000_000
    prices[360] = 95_000_000
    prices[361] = 96_000_000
    prices[362] = None  # No bar in this batch while holding
    prices[363] = 94_500_000
    prices[364] = 100_000_000

    total_batches = 365
    replies = []
    order_replies = []

    for seq in range(total_batches):
        p = prices.get(seq, 100_000_000)
        bars = []
        if p is not None:
            bars.append(
                {
                    "symbol": "CBBTC",
                    "o": str(p),
                    "h": str(p),
                    "l": str(p),
                    "c": str(p),
                    "o_depth": ["500000000000"],
                    "c_depth": ["500000000000"],
                }
            )

        # Equity calculation
        pos_val = 0
        if positions:
            pos_qty = int(positions[0]["qty"])
            cur_price = p if p is not None else 100_000_000
            pos_val = pos_qty * cur_price // (10**8)
        equity = cash + pos_val

        batch = {
            "type": "batch",
            "seq": seq,
            "t": seq * 60,
            "bars": bars,
            "account": {
                "cash_quote_units": str(cash),
                "positions": positions,
                "equity_quote_units": str(equity),
            },
            "fills": [],
        }

        proc.stdin.write(json.dumps(batch) + "\n")
        proc.stdin.flush()

        reply_line = proc.stdout.readline()
        if not reply_line:
            break
        reply = json.loads(reply_line.strip())
        replies.append(reply_line.strip())
        print(reply_line.strip())

        orders = reply.get("orders", [])
        if orders:
            order_replies.append((seq, orders))
            # Simulate fill at next open
            for order in orders:
                if order["side"] == "buy":
                    notional = int(order["notional_quote_units"])
                    fill_price = p if p is not None else 100_000_000
                    fill_qty = notional * (10**8) // fill_price
                    cash -= notional
                    positions = [
                        {
                            "symbol": "CBBTC",
                            "qty": str(fill_qty),
                            "cost_quote_units": str(notional),
                        }
                    ]
                elif order["side"] == "sell":
                    sell_qty = int(order["qty"])
                    fill_price = p if p is not None else 100_000_000
                    proceeds = sell_qty * fill_price // (10**8)
                    cash += proceeds
                    positions = []

    # Done message
    done = {
        "type": "done",
        "seq": total_batches,
        "account": {
            "cash_quote_units": str(cash),
            "positions": positions,
            "equity_quote_units": str(cash),
        },
    }
    proc.stdin.write(json.dumps(done) + "\n")
    proc.stdin.flush()

    proc.stdin.close()
    proc.wait()
    stderr_output = proc.stderr.read()
    if stderr_output:
        sys.stderr.write(stderr_output)

    print(f"\n--- Summary: Total batches answered: {len(replies)} ---")
    print(f"Total order replies: {len(order_replies)}")
    for seq, orders in order_replies:
        print(f"  Batch {seq}: {orders}")


if __name__ == "__main__":
    main()
