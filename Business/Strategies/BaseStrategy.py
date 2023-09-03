import backtrader as bt

class BaseStrategy(bt.Strategy):
    best_results = {}
    buy_commision = 0.01
    sell_commision = 0.01
    slippage = 0.01
    last_buy_execution_price = 0
    last_buy_quantity = 0
    last_buy_commission = 0

    params = (
        ("ticker_name", None),
        ("excel_writer", None),
        ("initial_date", None),
    )

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
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

        pass

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