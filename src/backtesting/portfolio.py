class Portfolio:
    def __init__(self, initial_capital=10000):
        self.cash = initial_capital
        self.position = 0

    def buy(self, price):
        if self.cash > price:
            self.position += 1
            self.cash -= price

    def sell(self, price):
        if self.position > 0:
            self.position -= 1
            self.cash += price

    def value(self, price):
        return self.cash + self.position * price
