-- T32 · Pré-consultas sobre as temp views v_als_* (contrato T28). GERADO por src/serving/consultas.py — não editar.
-- Dialeto comum a Spark SQL e T-SQL; troque o prefixo com consultas(prefixo=...). Só SELECT.

-- dashboard_forecast
SELECT nivel, entidade_id, entidade_nome, cliente_id, segmento, granularidade, periodo, realizado, prev_p10, prev_p50, prev_p90, potencial, potencial_p10, potencial_p90, data_corte, versao_modelo
FROM v_als_forecast_consumo
WHERE data_corte = (SELECT MAX(data_corte) FROM v_als_forecast_consumo)
ORDER BY nivel, entidade_id, granularidade, periodo;

-- dashboard_alertas
SELECT tipo, nivel, entidade_id, entidade_nome, cliente_id, segmento, periodo, valor_atual, valor_base, variacao_pct, detalhe
FROM v_als_alertas
ORDER BY tipo, entidade_id, periodo;

-- resumo_entidade
SELECT a.nivel, a.entidade_id, a.entidade_nome, a.segmento, a.n_equip,
       a.realizado_12m, a.potencial_12m, a.pct_achieved,
       f.prev_p10_horizonte, f.prev_p50_horizonte, f.prev_p90_horizonte, f.meses_horizonte
FROM v_als_pct_achieved a
LEFT JOIN (
    SELECT nivel, entidade_id,
           SUM(prev_p10) AS prev_p10_horizonte, SUM(prev_p50) AS prev_p50_horizonte,
           SUM(prev_p90) AS prev_p90_horizonte, COUNT(prev_p50) AS meses_horizonte
    FROM v_als_forecast_consumo
    WHERE granularidade = 'mes' AND data_corte = (SELECT MAX(data_corte) FROM v_als_forecast_consumo)
      AND prev_p50 IS NOT NULL
    GROUP BY nivel, entidade_id
) f ON f.nivel = a.nivel AND f.entidade_id = a.entidade_id
ORDER BY a.nivel, a.entidade_id;

-- consumo_segmento_mes
SELECT segmento, periodo, SUM(realizado) AS realizado, SUM(prev_p50) AS prev_p50
FROM v_als_forecast_consumo
WHERE nivel = 'cliente' AND granularidade = 'mes' AND data_corte = (SELECT MAX(data_corte) FROM v_als_forecast_consumo)
GROUP BY segmento, periodo
ORDER BY segmento, periodo;
