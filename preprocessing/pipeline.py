import pandas as pd
import numpy as np
from sklearn.preprocessing import PowerTransformer


class Transformer:
    """
    Data transformation engine.
    """

    def log_transform(self, df: pd.DataFrame, columns):
        df = df.copy()
        for col in columns:
            df[col] = np.log1p(df[col])
        return df

    def boxcox_transform(self, df: pd.DataFrame, column):
        df = df.copy()
        pt = PowerTransformer(method="box-cox", standardize=True)
        df[column] = pt.fit_transform(df[[column]])
        return df

    def yeo_johnson_transform(self, df: pd.DataFrame, column):
        df = df.copy()
        pt = PowerTransformer(method="yeo-johnson", standardize=True)
        df[column] = pt.fit_transform(df[[column]])
        return df