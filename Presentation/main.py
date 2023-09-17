import backtrader as bt

from Business.Exceptions.InsufficientCapitalException import InsufficientCapitalException
from Business.Strategies.SMACross import SMACross
from Data.Graphs.NetPercentageEvolutionGraph import NetPercentageEvolutionGraph
from Data.Graphs.PNLEvolutionGraph import PNLEvolutionGraph
from Data.Sources.Stock import Stock
import pandas as pd

names = ["M.BA"]
initialDate = "2019-08-13"

stocks = Stock(names, initialDate)
stocks.exportToExcel()

path = "C:/Users/esteb/PycharmProjects/SistemaTrading/Resources/Results.xlsx"
with pd.ExcelWriter(path) as writer:
    for stock_ticker, stock_dataframe in zip(stocks.names, stocks.dataframes):
        data = bt.feeds.PandasData(dataname=stock_dataframe)
        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(1000000)
        cerebro.addsizer(bt.sizers.AllInSizerInt)
        cerebro.adddata(data)

        # Establece las comisiones y slippage
        cerebro.broker.set_slippage_perc(0.01)
        cerebro.broker.setcommission(commission=0.01, commtype=bt.CommInfoBase.COMM_PERC)
        # cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, name='Trades')

        # cerebro.addanalyzer(bt.analyzers.Transactions, name='Transactions')
        cerebro.optstrategy(SMACross, ticker_name=stock_ticker, fast_length=range(5, 8), slow_length=range(15, 18),
                            excel_writer=writer, initial_date=initialDate)
        try:
            cerebro.run(maxcpus=1)  # maxcpus=1 para evitar problemas con multiprocesamiento en algunos entornos
        except InsufficientCapitalException as e:
            print(e)

for ticker in names:
    pnl_data = SMACross.get_best_pnl_data(ticker)
    percentage_data = SMACross.get_best_net_percentage_data(ticker)
    pnl_graph = PNLEvolutionGraph(pnl_data, ticker)
    pnl_graph.generate_graph()
    percentage_graph = NetPercentageEvolutionGraph(percentage_data, ticker)
    percentage_graph.generate_graph()
