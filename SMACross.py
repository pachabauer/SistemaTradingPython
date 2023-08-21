import backtrader as bt
import pandas as pd
from Utils import Utils

best_results = {}

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
        final_value = self.broker.getvalue()
        ticker = self.params.ticker_name
        print(
            f"Ticker: {ticker}, Fast Length: {self.params.fast_length}, "
            f"Slow Length: {self.params.slow_length}, Final Portfolio Value: {self.broker.getvalue()}")

        # Comprueba y actualiza el mejor resultado para este ticker
        if ticker not in best_results or final_value > best_results[ticker]['value']:
            best_results[ticker] = {
                'value': final_value,
                'fast_length': self.params.fast_length,
                'slow_length': self.params.slow_length,
            }
        df = pd.DataFrame(self.results, columns=['Date', 'Action', 'Close', 'Fast_MA', 'Slow_MA', 'PNL', 'Percentage'])

        # Redondeo a 2 decimales
        numeric_cols = ['Close', 'Fast_MA', 'Slow_MA', 'PNL', 'Percentage']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').round(2)

        # Agregar las comisiones y slippage como columnas adicionales en una fila vacía
        commission_row = pd.DataFrame([['', '', '', '', '', '', '', f'Buy Commission: {self.buy_commision}',
                                        f'Sell Commission: {self.sell_commision}', f'Slippage: {self.slippage}']],
                                      columns=['Date', 'Action', 'Close', 'Fast_MA', 'Slow_MA', 'PNL', 'Percentage',
                                               'Buy Commission', 'Sell Commission', 'Slippage'])
        df = pd.concat([commission_row, df], ignore_index=True)

        df.set_index('Date', inplace=True)
        sheet_name = f"{self.params.ticker_name} {self.params.fast_length}_{self.params.slow_length}"
        df.to_excel(self.params.excel_writer, sheet_name=sheet_name)
        # Utilizo esta función para ajustar el ancho de las columnas automaticamente de Excel.
        Utils.auto_adjust_columns(self.params.excel_writer, sheet_name, df)

        summary_df = pd.DataFrame.from_dict(best_results, orient='index')
        summary_df.to_excel("Summary.xlsx")

