from openpyxl.utils import get_column_letter

class Utils:
    @staticmethod
    def auto_adjust_columns(writer, sheet_name, df):
        worksheet = writer.sheets[sheet_name]
        for idx, column in enumerate(df.columns, 1):
            column_letter = get_column_letter(idx)
            max_len = max(
                worksheet.column_dimensions[column_letter].width if column_letter in worksheet.column_dimensions else 0,
                max((len(str(cell.value)) for cell in worksheet[column_letter])),
                12
            )
            worksheet.column_dimensions[column_letter].width = max_len

