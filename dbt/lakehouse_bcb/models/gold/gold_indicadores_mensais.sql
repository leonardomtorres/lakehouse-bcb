with silver as (

    select * from {{ ref('silver_bcb_series') }}

),

mensal as (

    select
        date_trunc('month', data_referencia)::date as mes_referencia,
        serie,
        avg(valor) as valor_medio
    from silver
    group by 1, 2

)

select
    mes_referencia,
    max(case when serie = 'ipca_mensal' then valor_medio end) as ipca_mensal,
    max(case when serie = 'selic_meta' then valor_medio end) as selic_meta,
    max(case when serie = 'dolar_ptax' then valor_medio end) as dolar_ptax
from mensal
group by mes_referencia
order by mes_referencia
