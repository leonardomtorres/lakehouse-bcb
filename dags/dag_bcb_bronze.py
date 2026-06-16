from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, date
import sys

sys.path.insert(0, "/opt/airflow/ingestion")

from bcb_client import buscar_serie, SERIES
from bronze_writer import gravar_bronze, get_cliente_s3, BRONZE_BUCKET
from raw_loader import carregar_raw

DATA_INICIO = "01/01/2020"

def ingerir_series(**context):
    data_execucao = context["logical_date"].date()
    data_fim = data_execucao.strftime("%d/%m/%Y")

    for serie_key in SERIES:
        print(f"Buscando série: {serie_key}")
        df = buscar_serie(serie_key, DATA_INICIO, data_fim)
        gravar_bronze(df, serie_key, data_execucao)
        print(f"Serie {serie_key} gravada com {len(df)} registros")

def validar_arquivos(**context):
    data_execucao = context["logical_date"].date()
    ano = data_execucao.year
    mes = f"{data_execucao.month:02d}"
    dia = f"{data_execucao.day:02d}"

    cliente = get_cliente_s3()

    for serie_key in SERIES:
        s3_key = f"bcb/{serie_key}/ano={ano}/mes={mes}/data={dia}.parquet"
        resposta = cliente.list_objects_v2(Bucket=BRONZE_BUCKET, Prefix=s3_key)
        arquivos = resposta.get("Contents", [])
        if not arquivos:
            raise ValueError(f"Arquivo não encontrado: {s3_key}")
        print(f"Validado: {s3_key} ({arquivos[0]['Size']} bytes)")

def carregar_postgres(**context):
    data_execucao = context["logical_date"].date()

    for serie_key in SERIES:
        carregar_raw(serie_key, data_execucao)

with DAG(
    dag_id="dag_bcb_bronze",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["bcb", "bronze"],
) as dag:

    task_ingerir = PythonOperator(
        task_id="ingerir_series",
        python_callable=ingerir_series,
    )

    task_validar = PythonOperator(
        task_id="validar_arquivos",
        python_callable=validar_arquivos,
    )

    task_carregar_postgres = PythonOperator(
        task_id="carregar_postgres",
        python_callable=carregar_postgres,
    )

    task_ingerir >> task_validar >> task_carregar_postgres