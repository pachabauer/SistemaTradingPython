import backtrader as bt
import pandas as pd

class SMACross(bt.Strategy):
    params = (
        ("ticker_name", None),
        ("fast_length", 10),
        ("slow_length", 50),
        ("excel_writer", None),
    )

    buy_commision = 0.01
    sell_commision = 0.01
    slippage = 0.01

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.fast_length)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.slow_length)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.results = []
        self.buy_price = None
        self.current_pnl = 10000

    def next(self):
        current_date = self.data.datetime.date(0)
        if self.crossover > 0 and self.buy_price is None:  # Si la MA rápida cruza por encima de la MA lenta
            self.buy()
            self.buy_price = self.data.close[0] * (1 + self.buy_commision + self.slippage)
            self.results.append([current_date, "Buy", self.data.close[0], self.fast_ma[0], self.slow_ma[0], self.current_pnl, ""])
        elif self.crossover < 0 and self.buy_price:  # Si la MA rápida cruza por debajo de la MA lenta
            sell_price = self.data.close[0] * (1 - self.sell_commision - self.slippage)
            percentage = (sell_price / self.buy_price) - 1
            self.current_pnl *= (1 + percentage)
            self.sell()
            self.results.append([current_date, "Sell", self.data.close[0], self.fast_ma[0], self.slow_ma[0], self.current_pnl, percentage])
            self.buy_price = None

    def stop(self):
        print(
            f"Ticker: {self.params.ticker_name}, Fast Length: {self.params.fast_length}, "
            f"Slow Length: {self.params.slow_length}, Final Portfolio Value: {self.broker.getvalue()}")
        df = pd.DataFrame(self.results, columns=['Date', 'Action', 'Close', 'Fast_MA', 'Slow_MA', 'PNL', 'Percentage'])
        df.set_index('Date', inplace=True)
        # Agregar una fila al comienzo con las comisiones y el deslizamiento
        commission_data = {
            'Date': 'Commissions/Slippage',
            'Action': '',
            'Close': 'Buy Commission: ' + str(self.buy_commision),
            'Fast_MA': 'Sell Commission: ' + str(self.sell_commision),
            'Slow_MA': 'Slippage: ' + str(self.slippage),
            'PNL': '',
            'Percentage': ''
        }
        df = pd.concat([pd.DataFrame([commission_data]).set_index('Date'), df], axis=0)
        sheet_name = f"{self.params.ticker_name} {self.params.fast_length}_{self.params.slow_length}"
        df.to_excel(self.params.excel_writer, sheet_name=sheet_name)

