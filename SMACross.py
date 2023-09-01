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
        ("initial_date", None),
    )

    buy_commision = 0.01
    sell_commision = 0.01
    slippage = 0.01

    # Añado atributos adicionales para almacenar valores entre órdenes.
    last_buy_execution_price = 0
    last_buy_quantity = 0
    last_buy_commission = 0

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.fast_length)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.slow_length)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.results = []
        self.buy_price = None
        self.initial_pnl = self.broker.get_cash()
        self.current_pnl = self.initial_pnl
        self.net_pnl = 0
        self.pending_order = None
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_win_profit = 0
        self.total_loss_profit = 0
        self.max_drawdown = 0
        self.max_drawdown_percentage = 0
        self.max_winning_percentage = 0
        self.total_win_percentage = 0
        self.total_loss_percentage = 0
        self.max_winning_trade = 0
        self.current_consecutive_wins = 0
        self.current_consecutive_losses = 0
        self.max_consecutive_wins = 0
        self.max_consecutive_losses = 0
        self.prev_trade_date = None
        self.trade_durations = []

        if self.params.initial_date:
            self.initial_date = self.params.initial_date  # Usa la fecha inicial si se proporciona como parámetro
        else:
            self.initial_date = self.data.datetime.date(0)  # De lo contrario, usa la fecha del primer dato

    def next(self):
        current_date = self.data.datetime.date(0)
        slippage_value = self.data.open[0] * self.slippage

        if self.pending_order:
            if self.pending_order == "BUY":
                execution_price = self.data.open[0] + slippage_value
                quantity = round(self.current_pnl / execution_price)
                buy_commission = execution_price * quantity * self.buy_commision
                gross_pnl = quantity * execution_price
                self.last_buy_execution_price = execution_price
                self.last_buy_quantity = quantity
                self.last_buy_commission = buy_commission

                self.log(f"Buy order executed at: {self.data.open[0]}")

                self.results.append([current_date, "Buy", self.fast_ma[0], self.slow_ma[0], self.data.open[0],
                                     slippage_value, execution_price, quantity, '', gross_pnl, "",
                                     buy_commission, 0, ''])

            elif self.pending_order == "SELL":
                execution_price = self.data.open[0] - slippage_value
                sell_commission = execution_price * self.last_buy_quantity * self.sell_commision
                gross_pnl = self.last_buy_quantity * execution_price
                gross_profit = gross_pnl - (self.last_buy_quantity * self.last_buy_execution_price)
                gross_percentage = (execution_price - self.last_buy_execution_price) / self.last_buy_execution_price
                net_profit = gross_profit - (self.last_buy_commission + sell_commission)
                self.net_pnl = gross_pnl - (self.last_buy_commission + sell_commission)
                net_percentage = net_profit / self.current_pnl

                self.current_pnl += gross_profit
                self.total_trades += 1

                if net_profit > self.max_winning_trade:
                    self.max_winning_trade = net_profit

                if net_profit > 0:  # Si el beneficio neto es positivo
                    self.winning_trades += 1
                    self.total_win_profit += net_profit
                    self.total_win_percentage += net_percentage
                    self.current_consecutive_wins += 1
                    self.current_consecutive_losses = 0
                else:  # Si el beneficio neto es negativo o cero
                    self.losing_trades += 1
                    self.total_loss_profit += net_profit
                    self.total_loss_percentage += net_percentage
                    self.current_consecutive_losses += 1
                    self.current_consecutive_wins = 0

                if net_profit < self.max_drawdown:  # Si la pérdida neta es mayor que el drawdown máximo registrado
                    self.max_drawdown = net_profit
                    self.max_drawdown_percentage = net_percentage

                self.max_consecutive_wins = max(self.max_consecutive_wins, self.current_consecutive_wins)
                self.max_consecutive_losses = max(self.max_consecutive_losses, self.current_consecutive_losses)

                if self.prev_trade_date:
                    duration = (current_date - self.prev_trade_date).days
                    self.trade_durations.append(duration)
                self.prev_trade_date = current_date

                self.log(f"Sell order executed at: {self.data.open[0]}")

                self.results.append([current_date, "Sell", self.fast_ma[0], self.slow_ma[0], self.data.open[0],
                                     slippage_value, execution_price, self.last_buy_quantity, gross_profit, gross_pnl,
                                     gross_percentage, 0, sell_commission, net_profit, self.net_pnl, net_percentage])

                self.buy_price = None
            self.pending_order = None

        if self.crossover > 0 and not self.position:
            self.buy(exectype=bt.Order.Market)
            self.buy_price = self.data.open[0]
            self.pending_order = "BUY"
        elif self.crossover < 0 and self.position:
            self.sell(exectype=bt.Order.Market)
            self.pending_order = "SELL"

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY CONFIRMED, Price: {order.executed.price}, Cost: {order.executed.value}, Commission: {order.executed.comm}")
            elif order.issell():
                self.log(
                    f"SELL CONFIRMED, Price: {order.executed.price}, Cost: {order.executed.value}, Commission: {order.executed.comm}")
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f"OPERATION PROFIT, GROSS: {trade.pnl}, NET: {trade.pnlcomm}")

    def stop(self):
        final_value = self.net_pnl
        ticker = self.params.ticker_name
        print(
            f"Ticker: {ticker}, Fast Length: {self.params.fast_length}, "
            f"Slow Length: {self.params.slow_length}, Final Portfolio Value: {self.net_pnl}")
        finish_date = self.data.datetime.date(-1)
        avg_win_profit = self.total_win_profit / self.winning_trades if self.winning_trades != 0 else 0
        avg_loss_profit = self.total_loss_profit / self.losing_trades if self.losing_trades != 0 else 0
        avg_win_profit_percentage = self.total_win_percentage / self.winning_trades if self.winning_trades != 0 else 0
        avg_loss_profit_percentage = self.total_loss_percentage / self.losing_trades if self.losing_trades != 0 else 0
        avg_trade_duration = sum(self.trade_durations) / len(self.trade_durations) if self.trade_durations else 0

        # Comprueba y actualiza el mejor resultado para este ticker
        if ticker not in best_results or final_value > best_results[ticker]['final_pnl']:
            best_results[ticker] = {
                'initial_pnl': self.initial_pnl,
                'final_pnl': self.net_pnl,
                'fast_length': self.params.fast_length,
                'slow_length': self.params.slow_length,
                'initial_date': self.initial_date,
                'finish_date': finish_date,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                '% winning_trades': self.winning_trades / self.total_trades,
                '% losing_trades': self.losing_trades / self.total_trades,
                'max_drawdown': self.max_drawdown,
                'max_losing_%_PNL': self.max_drawdown_percentage,
                'avg_win_profit': avg_win_profit,
                'avg_win_profit_%': avg_win_profit_percentage,
                'avg_loss_profit': avg_loss_profit,
                'avg_loss_profit_%': avg_loss_profit_percentage,
                'max_winning_trade': self.max_winning_trade,
                '% max_winning_trade': self.max_winning_trade / self.initial_pnl,
                'consecutive_winners': self.max_consecutive_wins,
                'consecutive_lossers': self.max_consecutive_losses,
                'avg_trade_Q_days': avg_trade_duration
            }
        df = pd.DataFrame(self.results, columns=['Date', 'Action', 'Fast_MA', 'Slow_MA', 'Open', 'Slippage',
                                                 'Execution Price', 'Quantity', 'Gross Profit', 'Gross PNL',
                                                 'Gross Percentage', 'Buy Commission', 'Sell Commission', 'Net Profit',
                                                 'Net PNL', 'Net Percentage'])

        numeric_cols = ['Open', 'Fast_MA', 'Slow_MA', 'Slippage', 'Execution Price', 'Buy Commission',
                        'Sell Commission', 'Gross PNL', 'Gross Profit', 'Net Profit', 'Gross Percentage', 'Net PNL',
                        'Net Percentage']

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').round(3)

        commission_row = pd.DataFrame(
            [['', '', '', '', '', '', f'Initial PNL: {self.initial_pnl}', f'Buy Commission: {self.buy_commision}',
              f'Sell Commission: {self.sell_commision}', f'Slippage: {self.slippage}', '', '', '', '', '', '']],
            columns=['Date', 'Action', 'Fast_MA', 'Slow_MA', 'Open', 'Slippage', 'Execution Price',
                     'Quantity', 'Gross Profit', 'Gross PNL', 'Gross Percentage', 'Buy Commission', 'Sell Commission',
                     'Net Profit', 'Net PNL', 'Net Percentage'])
        df = pd.concat([commission_row, df], ignore_index=True)

        df.set_index('Date', inplace=True)
        sheet_name = f"{self.params.ticker_name} {self.params.fast_length}_{self.params.slow_length}"
        df.to_excel(self.params.excel_writer, sheet_name=sheet_name)

        Utils.auto_adjust_columns(self.params.excel_writer, sheet_name, df)

        summary_df = pd.DataFrame.from_dict(best_results, orient='index')
        column_order = ['initial_pnl', 'final_pnl', 'initial_date', 'finish_date', 'fast_length', 'slow_length',
                        'total_trades', 'winning_trades', 'losing_trades', '% winning_trades', '% losing_trades',
                        'max_losing_%_PNL', 'avg_win_profit', 'avg_win_profit_%',
                        'avg_loss_profit', 'avg_loss_profit_%', 'max_drawdown', 'max_winning_trade',
                        '% max_winning_trade', 'consecutive_winners', 'consecutive_lossers',
                        'avg_trade_Q_days']

        numeric_summary_cols = ['% winning_trades', '% losing_trades', 'max_drawdown', 'max_losing_%_PNL',
                                'avg_win_profit', 'avg_win_profit_%', 'avg_loss_profit_%',
                                'avg_loss_profit', 'max_winning_trade']

        for col in numeric_summary_cols:
            summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').round(3)

        summary_df = summary_df[column_order]
        summary_df.to_excel("Summary.xlsx")
