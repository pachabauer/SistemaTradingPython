import backtrader as bt
from SMACross import SMACross
from Stock import Stock
import pandas as pd

names = ["GGAL.BA","MORI.BA"]
initialDate = "2019-08-13"

stocks = Stock(names, initialDate)
##Stock.exportToExcel(stocks)

path = "C:/Users/esteb/PycharmProjects/SistemaTrading/Results.xlsx"
with pd.ExcelWriter(path) as writer:
    for stock_ticker, stock_dataframe in zip(stocks.names, stocks.dataframes):
        data = bt.feeds.PandasData(dataname=stock_dataframe)
        cerebro = bt.Cerebro()
        cerebro.adddata(data)

        # Establece la cantidad inicial de dinero
        cerebro.broker.set_cash(10000)

        # Optimización: prueba combinaciones de medias móviles desde 5 hasta 30 para la rápida y desde 40 hasta 100 para la lenta
        cerebro.optstrategy(SMACross, ticker_name = stock_ticker, fast_length=range(5, 7), slow_length=range(10, 12), excel_writer=writer)

        cerebro.run(maxcpus=1)  # maxcpus=1 para evitar problemas con multiprocesamiento en algunos entornos
