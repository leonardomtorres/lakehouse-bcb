import io
import boto3
import pandas as pd
from datetime import date

MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BRONZE_BUCKET = "bronze"

def get_cliente_s3():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )

def gravar_bronze(df, serie, data_execucao):
    ano = data_execucao.year
    mes = f"{data_execucao.month:02d}"
    dia = f"{data_execucao.day:02d}"

    s3_key = f"bcb/{serie}/ano={ano}/mes={mes}/data={dia}.parquet"
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow", compression="snappy")
    buffer.seek(0)

    cliente = get_cliente_s3()
    cliente.put_object(
        Bucket=BRONZE_BUCKET,
        Key=s3_key,
        Body=buffer.getvalue(),
    )

    print(f"Gravado: s3://{BRONZE_BUCKET}/{s3_key}")
    return s3_key