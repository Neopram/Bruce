def simulate_strategy(price_series: list, strategy: str, capital: float = 10000.0, risk: float = 0.01):
    trades = []
    balance = capital
    win_count = 0
    loss_count = 0

    for i in range(1, len(price_series) - 1):
        entry_price = price_series[i]
        if strategy == "mean_reversion" and price_series[i] < price_series[i - 1]:
            exit_price = price_series[i + 1]
        elif strategy == "breakout" and price_series[i] > price_series[i - 1]:
            exit_price = price_series[i + 1]
        else:
            continue

        size = balance * risk / entry_price
        pnl = (exit_price - entry_price) * size
        balance += pnl

        trades.append({
            "entry": entry_price,
            "exit": exit_price,
            "pnl": round(pnl, 2)
        })

        if pnl >= 0:
            win_count += 1
        else:
            loss_count += 1

    roi = ((balance - capital) / capital) * 100
    winrate = win_count / max((win_count + loss_count), 1)

    return {
        "initial_capital": capital,
        "final_balance": round(balance, 2),
        "roi_percent": round(roi, 2),
        "winrate": round(winrate, 2),
        "trades": trades
    }