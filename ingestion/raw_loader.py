import io
import os
import pandas as pd
import sqlalchemy
from bronze_writer import get_cliente_s3, BRONZE_BUCKET

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_URL = f"postgresql+psycopg2://lakehouse:lakehouse@{POSTGRES_HOST}:5432/lakehouse"


def get_engine():
    return sqlalchemy.create_engine(POSTGRES_URL)


def carregar_raw(serie, data_execucao):
    ano = data_execucao.year
    mes = f"{data_execucao.month:02d}"
    dia = f"{data_execucao.day:02d}"

    s3_key = f"bcb/{serie}/ano={ano}/mes={mes}/data={dia}.parquet"
    cliente = get_cliente_s3()

    resposta = cliente.get_object(Bucket=BRONZE_BUCKET, Key=s3_key)
    buffer = io.BytesIO(resposta["Body"].read())
    df = pd.read_parquet(buffer)

    engine = get_engine()
    df.to_sql("raw_bcb_series", engine, schema="public", if_exists="append", index=False)

    print(f"Carregado no Postgres: {len(df)} linhas da serie {serie}")
    return len(df)
