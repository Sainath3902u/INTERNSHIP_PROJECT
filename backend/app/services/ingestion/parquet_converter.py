import pandas as pd


class ParquetConverter:

    REQUIRED_COLUMNS = [
        "time",
        "pkt_len",
        "srcip",
        "dstip",
        "srcport",
        "dstport",
        "proto"
    ]

    @staticmethod
    def csv_to_parquet(
        csv_path: str,
        parquet_path: str
    ):

        df = pd.read_csv(
            csv_path,
            usecols=ParquetConverter.REQUIRED_COLUMNS
        )

        df.to_parquet(
            parquet_path,
            index=False
        )

        return len(df)