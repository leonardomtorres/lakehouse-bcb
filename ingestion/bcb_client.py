import requests
import pandas as pd
from datetime import datetime

SERIES = {
    "selic_meta": 432,
    "ipca_mensal": 433,
    "dolar_ptax": 1,
}

BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

def buscar_serie(serie_key, data_inicio, data_fim):
    codigo = SERIES[serie_key]
    url = BCB_URL.format(codigo=codigo)
    
    params = {
        "formato": "json",
        "dataInicial": data_inicio,
        "dataFinal": data_fim,
    }

    resposta = requests.get(url, params=params)
    resposta.raise_for_status()

    dados = resposta.json()
    df = pd.DataFrame(dados)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["serie"] = serie_key
    df["ingestao_ts"] = datetime.utcnow().isoformat()
    return df





