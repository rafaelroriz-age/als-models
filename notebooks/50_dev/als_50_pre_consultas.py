"""T30: pré-consultas `v_als_*` em temp views e saídas do contrato (T28) em Files/als_oilmodel/saida/.

Roda só no Fabric (Spark). Lê o lakehouse do parâmetro `lakehouse` (padrão LakehouseOel; local/env: ALS_LAKEHOUSE)
somente com SELECT e monta:
  v_als_src_*            projeção das tabelas de origem (S360 em bronze_s360, Zoho em silver_zoho)
  v_als_amostras_mes     amostras por cliente S360 × equipamento × mês, sem avulsas (regras da T14)
  v_als_forecast_consumo, v_als_pct_achieved, v_als_alertas   saídas no contrato (src/serving/contrato.py)
Grava no Files do lakehouse padrão do notebook (o anexado no deploy): forecast_consumo.parquet, pct_achieved.parquet,
alertas.parquet (só as aprovadas no G4) e relatorio_dev.json. Nenhuma tabela permanente, nenhuma escrita na área de tabelas.
Forecast = baseline ingênuo sazonal (src/pipeline/dev.py); o modelo escolhido entra na T15.
Publicar/rodar: python scripts/fabric_deploy.py [--aplicar] e python scripts/fabric_run.py als_50_pre_consultas.
"""
# %% [parameters]
import os

lakehouse = os.environ.get("ALS_LAKEHOUSE", "LakehouseOel")
data_corte = os.environ.get("ALS_DATA_CORTE", "")      # vazio = 1º dia do mês corrente
horizonte = int(os.environ.get("ALS_HORIZONTE", "12"))
meses_historico = int(os.environ.get("ALS_MESES_HISTORICO", "36"))
base_alerta = os.environ.get("ALS_BASE_ALERTA", "ano_anterior")

# %%
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

from pyspark.sql import SparkSession  # noqa: E402

from src.pipeline import dev  # noqa: E402
from src.pipeline.fabric import pasta_dados  # noqa: E402
from src.serving.contrato import CONTRATOS  # noqa: E402

PASTA_FABRIC = "saida"  # subpasta de Files/als_oilmodel/ que scripts/fabric_run.py baixa
spark = SparkSession.builder.getOrCreate()
LH = dev.resolver_lakehouse(lakehouse)
H = int(horizonte)  # parâmetro injetado pelo job chega como texto
DESDE, CORTE = dev.janela(data_corte or None, int(meses_historico))
print(f"lakehouse={LH} corte={CORTE.date()} histórico desde {DESDE.date()} h={H}")

# %%
# pré-consultas: temp views (só na sessão), leitura somente SELECT no lakehouse de origem
for nome, sql in dev.sql_fontes(LH).items():
    spark.sql(sql).createOrReplaceTempView(nome)
spark.sql(dev.sql_amostras_mes(DESDE, CORTE)).createOrReplaceTempView("v_als_amostras_mes")

amostras = spark.sql("SELECT * FROM v_als_amostras_mes").toPandas()
clientes = spark.sql("SELECT * FROM v_als_src_cliente").toPandas()
accounts = spark.sql("SELECT * FROM v_als_src_zoho_accounts").toPandas()
print(f"amostras_mes: {len(amostras)} linhas, {int(amostras['amostras'].sum())} amostras")

# %%
serie = dev.series_mensais(amostras, clientes, accounts, DESDE, CORTE)
saidas = dev.gerar(serie, CORTE, H, base_alerta)
for nome, df in saidas.items():
    if len(df):
        spark.createDataFrame(df).createOrReplaceTempView(CONTRATOS[nome].pre_consulta)

rel = dev.gravar(saidas, pasta_dados(RAIZ) / PASTA_FABRIC)
rel_resumo = {"lakehouse": LH, "data_corte": str(CORTE.date()), "gravadas": rel["gravadas"],
              "reprovadas": rel["reprovadas"],
              "falhas_g4": [g for g in rel["gates"] if not g["ok"]]}
print(rel_resumo)
if rel["reprovadas"]:
    raise RuntimeError(f"saídas reprovadas no G4: {rel['reprovadas']} (ver relatorio_dev.json)")
