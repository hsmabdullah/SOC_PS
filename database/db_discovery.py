import pandas as pd

class DBDiscovery:
    """
    Discovers database structure automatically.
    """

    def __init__(self, connector):
        self.connector = connector

    def list_databases(self):
        query = "SELECT name FROM sys.databases"
        return pd.read_sql(query, self.connector.get_connection())

    def list_tables(self):
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"
        return pd.read_sql(query, self.connector.get_connection())