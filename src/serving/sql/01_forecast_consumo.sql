-- T20 · Consultas T-SQL (SQL analytics endpoint do LakehouseOel) que produzem as tabelas do dashboard.
-- Contrato oficial das saídas (v_als_*, parquet, G4/G5): src/serving/contrato.py e docs_fabric/10 §3.3.
-- Contrato de colunas: src/serving/dashboard.py (COLUNAS_FORECAST, COLUNAS_ALERTAS).
--
-- PROPOSTA, NÃO EXECUTADA: as tabelas de saída abaixo ainda não existem no Fabric. São nomes propostos
-- (prefixo als_) para as saídas dos notebooks de forecast (T15) e potencial (T16), gravadas como Delta
-- pelo pipeline do projeto. Os SELECTs só leem; nada aqui cria, altera ou apaga objeto existente.
--
-- Tabelas de entrada assumidas (uma linha por entidade × período × quantil/valor):
--   als_forecast_saida(nivel, entidade_id, granularidade, periodo, quantil, valor, data_corte, versao_modelo)
--       quantil in ('p10','p50','p90'); só períodos >= data_corte
--   als_amostras_realizado(nivel, entidade_id, granularidade, periodo, amostras)      -- tabela-base da T14
--   als_potencial(nivel, entidade_id, granularidade, periodo, potencial)             -- saída da T16
--   als_dim_entidade(nivel, entidade_id, entidade_nome, cliente_id, segmento)
--   als_amostras_mensal_cliente(cliente_id, periodo, amostras)                        -- tabela-base da T14
--   als_coletas_compartimento(equipamento_id, compartimento, horimetro, intervalo_h)  -- coletas, RN-01
--   als_horimetro_atual(equipamento_id, horimetro_atual)

-- 1) Tabela do dashboard: realizado + previsto (p10/p50/p90) + potencial por entidade e período.
SELECT  d.nivel, d.entidade_id, d.entidade_nome, d.cliente_id, d.segmento,
        p.granularidade, p.periodo,
        r.amostras                                              AS realizado,
        p.prev_p10, p.prev_p50, p.prev_p90,
        pt.potencial,
        p.data_corte, p.versao_modelo
FROM (
    SELECT nivel, entidade_id, granularidade, periodo, data_corte, versao_modelo,
           MAX(CASE WHEN quantil = 'p10' THEN valor END) AS prev_p10,
           MAX(CASE WHEN quantil = 'p50' THEN valor END) AS prev_p50,
           MAX(CASE WHEN quantil = 'p90' THEN valor END) AS prev_p90
    FROM als_forecast_saida
    WHERE data_corte = (SELECT MAX(data_corte) FROM als_forecast_saida)   -- última rodada
    GROUP BY nivel, entidade_id, granularidade, periodo, data_corte, versao_modelo
) AS p
JOIN als_dim_entidade d
  ON d.nivel = p.nivel AND d.entidade_id = p.entidade_id
LEFT JOIN als_amostras_realizado r
  ON r.nivel = p.nivel AND r.entidade_id = p.entidade_id
 AND r.granularidade = p.granularidade AND r.periodo = p.periodo
LEFT JOIN als_potencial pt
  ON pt.nivel = p.nivel AND pt.entidade_id = p.entidade_id
 AND pt.granularidade = p.granularidade AND pt.periodo = p.periodo;
-- Nota: para exibir o histórico (realizado sem previsão) o dashboard usa também os períodos passados;
-- troque o FROM (...) AS p por uma tabela de calendário (als_dim_periodo) com LEFT JOIN ao forecast.
-- O nível 'segmento' vem de als_forecast_saida já reconciliado (src/models/hierarquia.py, T13): somar
-- quantis entre clientes não preserva p10/p90.

-- 2) Alertas de queda (RN-05): mês fechado mais recente contra o mesmo mês do ano anterior (base padrão).
WITH ult AS (SELECT MAX(periodo) AS periodo FROM als_amostras_mensal_cliente)
SELECT  'queda'                                   AS tipo,
        'cliente'                                 AS nivel,
        a.cliente_id                              AS entidade_id,
        d.entidade_nome, a.cliente_id, d.segmento,
        a.periodo,
        a.amostras                                AS valor_atual,
        b.amostras                                AS valor_base,
        1.0 - CAST(a.amostras AS float) / b.amostras AS variacao_pct,
        'base: mesmo mês do ano anterior'         AS detalhe
FROM als_amostras_mensal_cliente a
JOIN ult ON a.periodo = ult.periodo
JOIN als_amostras_mensal_cliente b
  ON b.cliente_id = a.cliente_id AND b.periodo = DATEADD(year, -1, a.periodo)
JOIN als_dim_entidade d ON d.nivel = 'cliente' AND d.entidade_id = a.cliente_id
WHERE b.amostras > 0
  AND 1.0 - CAST(a.amostras AS float) / b.amostras > 0.20;     -- "maior que 20%": 20,0% exatos não alertam

-- 3) Alertas de churn de compartimento (RN-06): horas rodadas desde a última coleta > intervalo esperado.
WITH ultima AS (
    SELECT equipamento_id, compartimento, MAX(horimetro) AS horimetro, MAX(intervalo_h) AS intervalo_h
    FROM als_coletas_compartimento
    GROUP BY equipamento_id, compartimento
)
SELECT  'churn'                                   AS tipo,
        'equipamento'                             AS nivel,
        u.equipamento_id                          AS entidade_id,
        d.entidade_nome, d.cliente_id, d.segmento,
        CAST(GETDATE() AS date)                   AS periodo,
        h.horimetro_atual - u.horimetro           AS valor_atual,     -- horas sem coleta
        u.intervalo_h                             AS valor_base,
        CAST(NULL AS float)                       AS variacao_pct,
        CONCAT('compartimento ', u.compartimento) AS detalhe
FROM ultima u
JOIN als_horimetro_atual h ON h.equipamento_id = u.equipamento_id
JOIN als_dim_entidade d    ON d.nivel = 'equipamento' AND d.entidade_id = u.equipamento_id
WHERE h.horimetro_atual - u.horimetro > 1.0 * u.intervalo_h;       -- fator padrão do projeto = 1,0
