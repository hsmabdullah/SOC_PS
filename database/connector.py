import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnector:
    """
    Secure SQL Server connection using SQLAlchemy + pyodbc.
    Read-only enforced for SOC safety.
    """

    def __init__(self):
        self.server = os.getenv("DB_SERVER")
        self.database = os.getenv("DB_DATABASE")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")

        self.engine = self._create_engine()

    def _create_engine(self):
        conn_str = (
            "mssql+pyodbc://{user}:{pwd}@{server}/{db}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ).format(
            user=self.username,
            pwd=self.password,
            server=self.server,
            db=self.database
        )

        engine = create_engine(
            conn_str,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            fast_executemany=True
        )

        return engine

    def get_connection(self):
        return self.engine.connect()