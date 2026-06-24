import pandas as pd

class SchemaInspector:
    """
    Inspects database schema, tables, and columns.
    """

    def __init__(self, connector):
        self.connector = connector

    def get_tables(self):
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"
        return pd.read_sql(query, self.connector.get_connection())

    def get_columns(self, table_name: str):
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        """
        return pd.read_sql(query, self.connector.get_connection())

    def get_primary_keys(self, table_name: str):
        query = f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_NAME = '{table_name}'
        """
        return pd.read_sql(query, self.connector.get_connection())