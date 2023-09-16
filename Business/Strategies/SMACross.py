import backtrader as bt
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter
from Business.Exceptions.InsufficientCapitalException import InsufficientCapitalException
from Business.Strategies.BaseStrategy import BaseStrategy
from Data.Exporters.ExcelExporter import ExcelExporter

best_results = {}


class SMACross(BaseStrategy):
    params = (
        ("fast_length", 0),
        ("slow_length", 0),
    )

    best_pnl_evolution = []
    best_net_percentage_evolution = []

    def __init__(self):
        super().__init__()
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.fast_length)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.slow_length)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.net_pnl_evolution = []
        self.net_percentage_evolution = []


    def next(self):
        current_date = self.data.datetime.date(0)
        slippage_value = self.data.open[0] * self.slippage

        if self.pending_order:
            if self.pending_order == "BUY":
                execution_price = self.data.open[0] + slippage_value
                quantity = round(self.current_pnl / execution_price)
                if quantity == 0:
                    raise InsufficientCapitalException()

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
                self.net_pnl_evolution.append({'current_date': current_date, 'net_pnl': self.net_pnl})
                self.net_percentage_evolution.append({'current_date': current_date, 'net_percentage': net_percentage})

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
                'avg_trade_Q_days': avg_trade_duration,
                'best_pnl_evolution': self.net_pnl_evolution,
                'best_net_percentage_evolution': self.net_percentage_evolution
            }

        excel_exporter = ExcelExporter(self)
        excel_exporter.export(self.results, best_results, main_extra_columns=[],
                              summary_extra_columns=['fast_length', 'slow_length'])

    def show_best_graphs(ticker):
        best_pnl_data = best_results[ticker].get('best_pnl_evolution', [])
        best_net_percentage_data = best_results[ticker].get('best_net_percentage_evolution', [])

        if not best_pnl_data or not best_net_percentage_data:
            print(f"No best results found for {ticker}")
            return

        pnl_df = pd.DataFrame(best_pnl_data)
        percentage_df = pd.DataFrame(best_net_percentage_data)

        # Gráfico para pnl_evolution
        plt.figure(1, figsize=(10, 6))
        sns.set_style("whitegrid")

        # Convertimos los valores a millones y ajustamos la precisión a 2 decimales
        pnl_df['net_pnl'] = (pnl_df['net_pnl'] / 1000000).round(2)

        sns.lineplot(x='current_date', y='net_pnl', data=pnl_df, linewidth=2.5, color='b')
        plt.title(f'EVOLUCIÓN DE NET PNL PARA {ticker}', fontsize=16, fontweight='bold')
        plt.ylabel('Net PNL (en millones)', fontsize=12)
        plt.xlabel('Fecha', fontsize=12)

        # Configuración de las etiquetas del eje x para que aparezcan cada 3 meses
        ax = plt.gca()
        ax.xaxis.set_major_locator(MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))

        # Rotar las etiquetas del eje x para una mejor visibilidad
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig(f'{ticker}_best_pnl_evolution.png')
        plt.show(block=False)

        # Gráfico para net_percentage_evolution
        plt.figure(2, figsize=(10, 6))
        sns.set_style("whitegrid")

        # Convertimos los valores a porcentaje
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

        plt.title(f'DISTRIBUCIÓN DE NET PERCENTAGE PARA {ticker}', fontsize=16, fontweight='bold')
        plt.xlabel('Rendimiento (%)', fontsize=12)
        plt.ylabel('Cantidad de trades', fontsize=12)

        # Configurando las etiquetas para el eje x con incrementos de 5%
        plt.xticks(range(x_min, x_max, 5))

        # Configurando los límites para el eje x
        plt.xlim(x_min, x_max)

        plt.tight_layout()
        plt.savefig(f'{ticker}_best_net_percentage_evolution.png')
        plt.show(block=False)

