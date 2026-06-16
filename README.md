# lakehouse-bcb

Pipeline de dados usando as séries públicas do Banco Central (Selic, IPCA e Dólar PTAX). Comecei esse projeto pra praticar arquitetura medallion (Bronze/Silver/Gold) numa stack parecida com o que se usa de verdade no mercado, mas tudo rodando local via Docker.

## Stack

- **Python** — extração via API do BCB
- **MinIO** — simula S3 localmente, guarda os Parquet brutos (Bronze)
- **Postgres** — onde o dado vira tabela relacional e onde o dbt trabalha
- **Airflow** — orquestra a ingestão (Bronze → Postgres raw)
- **dbt** — transforma raw → Silver (limpeza) → Gold (agregação mensal)
- **Streamlit + Plotly** — dashboard final

## Como subir

```bash
docker-compose up -d
```

Sobe MinIO, Postgres, Airflow e dbt. Espera um pouco o Airflow inicializar (pode demorar uns 20-30s na primeira vez).

Acessos:
- Airflow: http://localhost:8080 (admin/admin)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Dashboard: http://localhost:8501

## Fluxo

```
API BCB → Python (ingestion/) → MinIO (Bronze, Parquet)
                                      ↓
                          Airflow lê e insere no Postgres
                                      ↓
                          raw_bcb_series (Postgres, dado bruto)
                                      ↓
                          dbt: silver_bcb_series (view, limpo)
                                      ↓
                          dbt: gold_indicadores_mensais (table, agregado por mês)
                                      ↓
                          Streamlit lê a Gold e mostra os gráficos
```

A DAG do Airflow (`dag_bcb_bronze`) roda diário e faz 3 coisas: busca a série na API, valida se o arquivo foi gravado no MinIO, e carrega no Postgres.

O dbt fica num container separado (`lakehouse_dbt`) que só fica dormindo (`sleep infinity`) esperando receber comando via `docker exec`. Pra rodar os models:

```bash
docker exec lakehouse_dbt dbt run --project-dir //usr/app --profiles-dir //root/.dbt
```

(os `//` antes do caminho são por causa de um bug de tradução de path do Git Bash no Windows, sem isso ele tenta converter pra path do Windows e quebra)

## Dashboard

Roda num container próprio (build local, não tem imagem pronta pra isso). Conecta no Postgres usando `POSTGRES_HOST=postgres` (nome do serviço no compose, não localhost — dentro de container, localhost é o próprio container).

```bash
docker-compose up -d --build dashboard
```

O `app.py` é montado como volume, então depois do primeiro build dá pra editar e só atualizar a página, sem rebuild.

## Por que rodar o dbt e o dashboard em Docker e não local

Tive um problema chato com `psycopg2` no Windows — um `UnicodeDecodeError` toda vez que tentava conectar no Postgres direto do host. Depois de muito investigar (cheguei a achar uma variável PATH corrompida, resolvi, e ainda assim continuou acontecendo) percebi que era ligado a configuração regional do Windows interferindo em como o libpq monta mensagens de erro. Resolver isso "de raiz" no Windows ia ser mais trabalho que valia a pena, então decidi rodar tudo que conecta no Postgres dentro de containers Linux, onde esse problema simplesmente não existe.

## Estrutura

```
dags/           DAGs do Airflow
ingestion/      scripts Python (busca API, grava bronze, carrega postgres)
dbt/lakehouse_bcb/models/
  silver/       limpeza e dedup
  gold/         agregação mensal
dashboard/      app Streamlit
docker-compose.yml
```

## Idéias futuras

- forecast com Prophet pra Selic/IPCA
- talvez migrar o MinIO pra um bucket S3 real
- mais séries do BCB (hoje só tem 3)
