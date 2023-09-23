import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class CorrelationGraph:

    def __init__(self, stocks):
        self.stocks = stocks

    def generate_graph(self):
        # Construir un dataframe consolidado
        consolidated_df = pd.DataFrame()

        for ticker, df in zip(self.stocks.names, self.stocks.dataframes):
            consolidated_df[ticker] = df['Close']

        # Calcular la matriz de correlación
        correlation_matrix = consolidated_df.corr()

        # Graficar el heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0, linewidths=.5, cbar_kws={"shrink": 0.75})
        plt.title('Correlación entre tickers', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png')
        plt.show(block=False)

