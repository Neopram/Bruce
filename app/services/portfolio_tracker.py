# Gestor de portafolio descentralizado
class PortfolioTracker:
    def __init__(self):
        self.user_holdings = {}

    def add_asset(self, user, symbol, amount, price):
        if user not in self.user_holdings:
            self.user_holdings[user] = []
        self.user_holdings[user].append({
            "symbol": symbol,
            "amount": amount,
            "price": price
        })

    def get_portfolio_value(self, user):
        if user not in self.user_holdings:
            return 0.0
        return sum(a["amount"] * a["price"] for a in self.user_holdings[user])
