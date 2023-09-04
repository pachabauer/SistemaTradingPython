import pandas as pd
from Infrastructure.Utils.Utils import Utils

class ExcelExporter:
    def __init__(self, strategy_instance):
        self.strategy = strategy_instance
        self.setup_columns_based_on_strategy()

    def setup_columns_based_on_strategy(self):
        """ Configura las columnas basadas en la estrategia """
        # Estas son las columnas comunes a todas las estrategias
        self.base_columns = ['Date', 'Action', 'Open', 'Slippage',
                             'Execution Price', 'Quantity', 'Gross Profit', 'Gross PNL',
                             'Gross Percentage', 'Buy Commission', 'Sell Commission', 'Net Profit',
                             'Net PNL', 'Net Percentage']

        strategy_specific_columns = []

        if isinstance(self.strategy, type(self.strategy)):
            strategy_specific_columns = ['Fast_MA', 'Slow_MA']

        # Inserta las columnas específicas de la estrategia justo después de 'Action'
        for col in reversed(strategy_specific_columns):
            self.base_columns.insert(self.base_columns.index('Action') + 1, col)

        # Aquí se puede agregar más condicionales para otras estrategias y sus respectivas columnas.
        # elif isinstance(self.strategy, OtraEstrategia):
        #     self.base_columns.extend(['OtraColumna1', 'OtraColumna2'])

    def numeric_formatter(self, df, numeric_cols):
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').round(3)
        return df

    def export(self, results, best_results, main_extra_columns=None, summary_extra_columns=None):
        # Agregar columnas adicionales si se especifican
        if main_extra_columns:
            for col in main_extra_columns:
                if col not in self.base_columns:
                    self.base_columns.append(col)

        df = pd.DataFrame(results, columns=self.base_columns)

        numeric_cols = ['Open', 'Fast_MA', 'Slow_MA', 'Slippage', 'Execution Price', 'Buy Commission',
                        'Sell Commission', 'Gross PNL', 'Gross Profit', 'Net Profit', 'Gross Percentage', 'Net PNL',
                        'Net Percentage']
        df = self.numeric_formatter(df, numeric_cols)

        commission_row = pd.DataFrame([['', '', '', '', '', '', f'Initial PNL: {self.strategy.initial_pnl}',
                                        f'Buy Commission: {self.strategy.buy_commision}',
                                        f'Sell Commission: {self.strategy.sell_commision}',
                                        f'Slippage: {self.strategy.slippage}', '', '', '', '', '', '']],
                                      columns=df.columns)

        df = pd.concat([commission_row, df], ignore_index=True)
        df.set_index('Date', inplace=True)
        sheet_name = f"{self.strategy.params.ticker_name} {self.strategy.params.fast_length}_{self.strategy.params.slow_length}"
        df.to_excel(self.strategy.params.excel_writer, sheet_name=sheet_name)

        Utils.auto_adjust_columns(self.strategy.params.excel_writer, sheet_name, df)

        summary_df = pd.DataFrame.from_dict(best_results, orient='index')
        numeric_summary_cols = ['% winning_trades', '% losing_trades', 'max_drawdown', 'max_losing_%_PNL',
                                'avg_win_profit', 'avg_win_profit_%', 'avg_loss_profit_%', 'avg_loss_profit',
                                'max_winning_trade']
        summary_df = self.numeric_formatter(summary_df, numeric_summary_cols)

        # Columnas base para el resumen
        base_summary_columns = ['initial_pnl', 'final_pnl', 'initial_date', 'finish_date', 'total_trades',
                                'winning_trades',
                                'losing_trades', '% winning_trades', '% losing_trades', 'max_losing_%_PNL',
                                'avg_win_profit',
                                'avg_win_profit_%', 'avg_loss_profit', 'avg_loss_profit_%', 'max_drawdown',
                                'max_winning_trade',
                                '% max_winning_trade', 'consecutive_winners', 'consecutive_lossers', 'avg_trade_Q_days']
        if summary_extra_columns:
            for col in summary_extra_columns:
                if col not in base_summary_columns:
                    base_summary_columns.insert(0, col)

        summary_df = summary_df[base_summary_columns]
        summary_df.to_excel("C:/Users/esteb/PycharmProjects/SistemaTrading/Resources/Summary.xlsx")

