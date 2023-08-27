import backtrader as bt
from SMACross import SMACross
from Stock import Stock
import pandas as pd

names = ["GGAL.BA", "MORI.BA", "EDN.BA", "YPFD.BA"]
initialDate = "2019-08-13"

stocks = Stock(names, initialDate)

path = "C:/Users/esteb/PycharmProjects/SistemaTrading/Results.xlsx"
with pd.ExcelWriter(path) as writer:
    for stock_ticker, stock_dataframe in zip(stocks.names, stocks.dataframes):
        data = bt.feeds.PandasData(dataname=stock_dataframe)
        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(10000)
        cerebro.addsizer(bt.sizers.AllInSizerInt)
        cerebro.adddata(data)

        # Establece las comisiones y slippage
        cerebro.broker.set_slippage_perc(0.01)
        cerebro.broker.setcommission(commission=0.01, commtype=bt.CommInfoBase.COMM_PERC)
        #cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, name='Trades')

        #cerebro.addanalyzer(bt.analyzers.Transactions, name='Transactions')
        cerebro.optstrategy(SMACross, ticker_name = stock_ticker, fast_length=range(5, 8), slow_length=range(10, 13), excel_writer=writer)
        cerebro.run(maxcpus=1)  # maxcpus=1 para evitar problemas con multiprocesamiento en algunos entornos
