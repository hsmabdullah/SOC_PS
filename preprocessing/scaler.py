import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler


class Scaler:
    """
    Feature scaling utilities.
    """

    def scale(self, df: pd.DataFrame, method="standard"):
        df = df.copy()
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns

        if method == "standard":
            scaler = StandardScaler()
        elif method == "minmax":
            scaler = MinMaxScaler()
        else:
            scaler = RobustScaler()

        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        return df