import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter

class PNLEvolutionGraph:

    def __init__(self, data, ticker):
        self.data = data
        self.ticker = ticker

    def generate_graph(self):
        try:
            # ... (código para generar el gráfico PNLEvolution usando el parámetro 'data')

            # Gráfico para pnl_evolution
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")

            # Convertimos los valores a millones y ajustamos la precisión a 2 decimales
            pnl_df = pd.DataFrame(self.data)
            pnl_df['net_pnl'] = (pnl_df['net_pnl'] / 1000000).round(2)

            sns.lineplot(x='current_date', y='net_pnl', data=pnl_df, linewidth=2.5, color='b')
            plt.title(f'EVOLUCIÓN DE NET PNL PARA {self.ticker}', fontsize=16, fontweight='bold')
            plt.ylabel('Net PNL (en millones)', fontsize=12)
            plt.xlabel('Fecha', fontsize=12)

            # Configuración de las etiquetas del eje x para que aparezcan cada 3 meses
            ax = plt.gca()
            ax.xaxis.set_major_locator(MonthLocator(interval=3))
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))

            # Rotar las etiquetas del eje x para una mejor visibilidad
            plt.xticks(rotation=45)

            plt.tight_layout()
            plt.savefig(f'{self.ticker}_best_pnl_evolution.png')
            plt.show(block=False)
            plt.close()
        except:
            pass