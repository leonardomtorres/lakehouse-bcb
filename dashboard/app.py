import pandas as pd
import plotly.express as px
import sqlalchemy
import streamlit as st
import os

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_URL = f"postgresql+psycopg2://lakehouse:lakehouse@{POSTGRES_HOST}:5432/lakehouse"


@st.cache_data(ttl=300)
def carregar_dados():
    engine = sqlalchemy.create_engine(POSTGRES_URL)
    df = pd.read_sql("SELECT * FROM gold_indicadores_mensais ORDER BY mes_referencia", engine)
    df["mes_referencia"] = pd.to_datetime(df["mes_referencia"])
    return df


st.set_page_config(page_title="Indicadores BCB", layout="wide")
st.title("Indicadores Macroeconômicos — Banco Central do Brasil")
st.caption("Dados públicos do BCB, processados via pipeline Bronze → Silver → Gold (MinIO, Postgres, Airflow, dbt).")

df = carregar_dados()

data_min = df["mes_referencia"].min()
data_max = df["mes_referencia"].max()
periodo = st.slider(
    "Período",
    min_value=data_min.to_pydatetime(),
    max_value=data_max.to_pydatetime(),
    value=(data_min.to_pydatetime(), data_max.to_pydatetime()),
    format="DD/MM/YYYY",
)

df_filtrado = df[(df["mes_referencia"] >= periodo[0]) & (df["mes_referencia"] <= periodo[1])]

col1, col2, col3 = st.columns(3)
col1.metric("Selic atual", f"{df_filtrado['selic_meta'].iloc[-1]:.2f}%")
col2.metric("IPCA mensal atual", f"{df_filtrado['ipca_mensal'].iloc[-1]:.2f}%")
col3.metric("Dólar PTAX atual", f"R$ {df_filtrado['dolar_ptax'].iloc[-1]:.2f}")

fig_selic = px.line(df_filtrado, x="mes_referencia", y="selic_meta", title="Meta Selic (% a.a.)")
fig_selic.update_xaxes(tickformat="%d/%m/%Y")
st.plotly_chart(fig_selic, use_container_width=True)

fig_ipca = px.line(df_filtrado, x="mes_referencia", y="ipca_mensal", title="IPCA mensal (%)")
fig_ipca.update_xaxes(tickformat="%d/%m/%Y")
st.plotly_chart(fig_ipca, use_container_width=True)

fig_dolar = px.line(df_filtrado, x="mes_referencia", y="dolar_ptax", title="Dólar PTAX (R$)")
fig_dolar.update_xaxes(tickformat="%d/%m/%Y")
st.plotly_chart(fig_dolar, use_container_width=True)

st.subheader("Tabela completa")
st.dataframe(
    df_filtrado,
    use_container_width=True,
    column_config={
        "mes_referencia": st.column_config.DateColumn("Mês de referência", format="DD/MM/YYYY"),
    },
)
