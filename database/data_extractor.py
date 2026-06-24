import pandas as pd

class DataExtractor:
    """
    Extracts data from SQL Server securely.
    """

    def __init__(self, connector):
        self.connector = connector

    def extract_table(self, table_name: str, limit: int = 10000):
        query = f"SELECT TOP {limit} * FROM {table_name}"
        conn = self.connector.get_connection()
        return pd.read_sql(query, conn)