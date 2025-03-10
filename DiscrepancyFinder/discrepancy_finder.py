import pandas as pd
import logging


class DiscrepancyFinder:
    """
    A class to find discrepancies in 'MATERIAL' and 'WEIGHT (KG)' columns for rows
    with identical 'UID' values.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        logging.info(f"DiscrepancyFinder initialized with file: {
                     self.file_path}")

    def get_discrepancies(self, sheet_name: str, group_by: str, compare_1: str, compare_2: str):
        """
        Finds discrepancies based on user-specified columns for grouping and comparison.

        :param sheet_name: The name of the Excel sheet to process.
        :param group_by: The column name to group by (e.g., 'UID').
        :param compare_1: The first column to compare for discrepancies.
        :param compare_2: The second column to compare for discrepancies.
        :return: List of tuples representing rows with discrepancies.
        """
        try:
            logging.info(f"Processing sheet '{sheet_name}' with group_by='{
                         group_by}', compare_1='{compare_1}', compare_2='{compare_2}'.")

            # Load Excel sheet
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)

            # Ensure selected columns exist
            required_columns = {group_by, compare_1, compare_2}
            if not required_columns.issubset(df.columns):
                raise ValueError(f"One or more selected columns do not exist in the sheet: {
                                 required_columns}")

            # Select and clean up relevant columns
            df = df[[group_by, compare_1, compare_2]].dropna()
            df = df.astype(str)  # Convert all to strings for uniformity

            # Find discrepancies
            discrepancies = []
            grouped = df.groupby(group_by, dropna=False)

            for key, group in grouped:
                compare_1_values = group[compare_1].unique()
                compare_2_values = group[compare_2].unique()

                if len(compare_1_values) > 1 or len(compare_2_values) > 1:
                    rows = group.index + 2  # Excel rows start at 1
                    discrepancies.extend([(rows[0], row) for row in rows[1:]])

            logging.info(f"Found {len(discrepancies)
                                  } discrepancies in sheet '{sheet_name}'.")
            return discrepancies

        except Exception as e:
            logging.exception("Error in discrepancy finding")
            raise
