import pandas as pd
import yfinance as yf


## Al no poder hacer sobrecarga de constructores , se usa el truco de *args para pasar distinta cantidda de parámetros
class Stock:
    def __init__(self, *args):
        self.dataframes = []
        if isinstance(args[0], list) and all(isinstance(name, str) for name in args[0]):
            self.names = args[0]
            initialDate = args[1] if len(args) > 1 else None
            finishDate = args[2] if len(args) > 2 else None

            for name in self.names:
                df = self.processStock(name, initialDate, finishDate)
                self.dataframes.append(df)
        else:
            try:
                self.names = [args[0]]
                df = self.processStock(*args)
                self.dataframes.append(df)
            except:
                print("Debe informar una acción")

    def processStock(self, name, initialDate=None, finishDate=None):
        if initialDate is None and finishDate is None:
            stock = yf.download(name).dropna(inplace=False)
        elif finishDate is None:
            stock = yf.download(name, initialDate).dropna(inplace=False)
        else:
            stock = yf.download(name, initialDate, finishDate).dropna(inplace=False)
        return stock

    def exportToExcel(self, path="C:/Users/esteb/PycharmProjects/SistemaTrading/Resources/Stocks.xlsx"):
        with pd.ExcelWriter(path) as writer:
            for df, name in zip(self.dataframes, self.names):
                df.to_excel(writer, sheet_name=name)
