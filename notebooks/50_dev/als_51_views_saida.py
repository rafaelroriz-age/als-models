"""T30: recarrega as saídas de Files/als_oilmodel/saida/ como temp views `v_als_*` e revalida o contrato (G4/G5).

Para consultar as saídas em SQL numa sessão nova (temp view só vive na sessão que a criou), sem tabela permanente.
Lê só do Files do lakehouse padrão do notebook; grava apenas saida/relatorio_views.json.
"""
# %% [parameters]
import os

pasta = os.environ.get("ALS_PASTA_SAIDA", "")    # vazio = <Files do lakehouse padrão>/als_oilmodel/saida

# %%
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402
from pyspark.sql import SparkSession  # noqa: E402

from src.pipeline.fabric import pasta_dados  # noqa: E402
from src.serving.contrato import CONTRATOS, aprovado, validar_todas  # noqa: E402

PASTA_FABRIC = "saida"
spark = SparkSession.builder.getOrCreate()
SAIDA = Path(pasta) if pasta else pasta_dados(RAIZ) / PASTA_FABRIC

saidas = {}
for k in CONTRATOS.values():
    arq = SAIDA / k.arquivo
    if arq.exists():
        saidas[k.nome] = pd.read_parquet(arq)
        spark.createDataFrame(saidas[k.nome]).createOrReplaceTempView(k.pre_consulta)
        print(f"{k.pre_consulta}: {len(saidas[k.nome])} linhas")

res = validar_todas(saidas)
(SAIDA / "relatorio_views.json").write_text(json.dumps(
    {"views": [CONTRATOS[n].pre_consulta for n in saidas], "g4_aprovado": aprovado(res),
     "falhas": [r for r in res if not r["ok"]]}, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print(f"G4 aprovado (todas as saídas): {aprovado(res)}; falhas: {sum(not r['ok'] for r in res)}")
