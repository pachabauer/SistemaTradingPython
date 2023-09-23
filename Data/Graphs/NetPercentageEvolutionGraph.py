import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


class NetPercentageEvolutionGraph:
    def __init__(self, data, ticker):
        self.data = data
        self.ticker = ticker

    def generate_graph(self):
        # ... (código para generar el gráfico NetPercentageEvolution usando el parámetro 'data')
        # Gráfico para net_percentage_evolution
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")

        # Convertimos los valores a porcentaje
        percentage_df = pd.DataFrame(self.data)
        percentage_df['net_percentage'] = (percentage_df['net_percentage'] * 100).round(2)

        # Calcular los límites para el eje x
        x_min = int(percentage_df['net_percentage'].min()) - 5  # Dando un margen adicional de 5%
        x_max = int(percentage_df['net_percentage'].max()) + 5  # Dando un margen adicional de 5%

        # Crear bins de 5%
        bins = range(int(x_min), int(x_max) + 5, 5)

        # Crear histograma usando numpy para que podamos colorear condicionalmente después
        hist_data, edges = np.histogram(percentage_df['net_percentage'], bins=bins)

        # Determinar colores basados en el punto medio de cada bin
        bin_mids = [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]

        # Crear una lista de colores condicionales
        colors = []
        for x in bin_mids:
            if x < 0:
                colors.append(plt.cm.Reds(np.interp(-x, [0, abs(x_min)], [0.5, 1])))
            else:
                colors.append(plt.cm.Greens(np.interp(x, [0, x_max], [0.5, 1])))

        # Dibujar las barras manualmente con los colores condicionales
        for i in range(len(hist_data)):
            plt.bar(bin_mids[i], hist_data[i], width=5, color=colors[i], edgecolor='black')

        plt.title(f'DISTRIBUCIÓN DE NET PERCENTAGE PARA {self.ticker}', fontsize=16, fontweight='bold')
        plt.xlabel('Rendimiento (%)', fontsize=12)
        plt.ylabel('Cantidad de trades', fontsize=12)

        # Configurando las etiquetas para el eje x con incrementos de 5%
        plt.xticks(range(x_min, x_max, 5))

        # Configurando los límites para el eje x
        plt.xlim(x_min, x_max)

        plt.tight_layout()
        plt.savefig(f'{self.ticker}_best_net_percentage_evolution.png')
        plt.show(block=False)
        plt.close()
