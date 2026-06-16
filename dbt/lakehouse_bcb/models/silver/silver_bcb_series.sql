with raw as (

    select
        serie,
        data::date as data_referencia,
        valor,
        ingestao_ts
    from {{ source('raw', 'raw_bcb_series') }}

),

deduplicado as (

    select
        *,
        row_number() over (
            partition by serie, data_referencia
            order by ingestao_ts desc
        ) as rn
    from raw

)

select
    serie,
    data_referencia,
    valor
from deduplicado
where rn = 1
  and valor is not null
