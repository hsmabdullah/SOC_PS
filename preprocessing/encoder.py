import pandas as pd
from sklearn.preprocessing import LabelEncoder


class Encoder:
    """
    Handles categorical encoding strategies.
    """

    def label_encode(self, df: pd.DataFrame, columns):
        df = df.copy()
        le = LabelEncoder()

        for col in columns:
            df[col] = le.fit_transform(df[col].astype(str))

        return df

    def one_hot_encode(self, df: pd.DataFrame, columns):
        return pd.get_dummies(df, columns=columns)

    def frequency_encode(self, df: pd.DataFrame, column):
        freq = df[column].value_counts(normalize=True)
        df[column] = df[column].map(freq)
        return df