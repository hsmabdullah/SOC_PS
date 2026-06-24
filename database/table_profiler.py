import pandas as pd

class TableProfiler:
    """
    Generates statistical profiling of database tables.
    """

    def __init__(self, connector):
        self.connector = connector

    def profile_table(self, table_name: str):
        conn = self.connector.get_connection()
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

        profile = {
            "shape": df.shape,
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicates": df.duplicated().sum(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "cardinality": df.nunique().to_dict()
        }

        return profile