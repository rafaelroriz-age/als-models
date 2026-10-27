"""Acesso somente leitura ao LakehouseOel, local (SQL endpoint via pyodbc) ou dentro do Fabric (Spark).

As consultas devem usar o subconjunto de SQL comum a T-SQL e Spark SQL:
YEAR/MONTH, CASE, COALESCE, TRIM, CAST, COUNT(DISTINCT), MIN/MAX. Sem TOP, LIMIT, DATEDIFF ou DATEFROMPARTS.
"""
from __future__ import annotations

import json
import os
import struct
from pathlib import Path

import pandas as pd

SQL_ENDPOINT = "j2qfysdun5iebf3ezw2l7ke4eu-vpyatc664ptezeejap7oap22qu.datawarehouse.fabric.microsoft.com"
DATABASE = "LakehouseOel"
_SCOPE = "https://database.windows.net/.default"
_AUTH_RECORD = Path.home() / ".als_oilmodel" / "auth_record.json"


def em_fabric() -> bool:
    try:
        import notebookutils  # noqa: F401
        return True
    except ImportError:
        return False


def _credencial():
    from azure.identity import (AuthenticationRecord, InteractiveBrowserCredential,
                                TokenCachePersistenceOptions)

    cache = TokenCachePersistenceOptions(name="als_oilmodel")
    if _AUTH_RECORD.exists():
        record = AuthenticationRecord.deserialize(_AUTH_RECORD.read_text(encoding="utf-8"))
        return InteractiveBrowserCredential(cache_persistence_options=cache, authentication_record=record)
    cred = InteractiveBrowserCredential(cache_persistence_options=cache)
    record = cred.authenticate(scopes=[_SCOPE])
    _AUTH_RECORD.parent.mkdir(parents=True, exist_ok=True)
    _AUTH_RECORD.write_text(record.serialize(), encoding="utf-8")
    return cred


class Fabric:
    """`with Fabric() as fb: df = fb.query(sql)`."""

    def __init__(self, database: str = DATABASE):
        self.database = database
        self._conn = None
        self._spark = None

    def __enter__(self):
        if em_fabric():
            from pyspark.sql import SparkSession
            self._spark = SparkSession.builder.getOrCreate()
        else:
            import pyodbc
            token = _credencial().get_token(_SCOPE).token.encode("utf-16-le")
            conn_str = (
                "Driver={ODBC Driver 18 for SQL Server};"
                f"Server={SQL_ENDPOINT};Database={self.database};"
                "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
            )
            self._conn = pyodbc.connect(
                conn_str,
                attrs_before={1256: struct.pack(f"<I{len(token)}s", len(token), token)},
                readonly=True,
            )
            self._conn.timeout = int(os.environ.get("ALS_QUERY_TIMEOUT", "600"))
        return self

    def __exit__(self, *exc):
        if self._conn is not None:
            self._conn.close()

    def query(self, sql: str) -> pd.DataFrame:
        if self._spark is not None:
            return self._spark.sql(sql).toPandas()
        cur = self._conn.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        return pd.DataFrame.from_records([tuple(r) for r in cur.fetchall()], columns=cols)

    def colunas(self, schema: str, tabela: str) -> pd.DataFrame:
        if self._spark is not None:
            d = self._spark.sql(f"DESCRIBE {schema}.{tabela}").toPandas()
            d = d[d["col_name"].str.strip().ne("") & ~d["col_name"].str.startswith("#")].drop_duplicates("col_name")
            return d.rename(columns={"col_name": "COLUMN_NAME", "data_type": "DATA_TYPE"})[["COLUMN_NAME", "DATA_TYPE"]]
        return self.query(
            "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{tabela}' ORDER BY ORDINAL_POSITION"
        )


def pasta_dados(raiz_local: Path) -> Path:
    """Fabric: Files do lakehouse padrão do notebook. Local: data/ do repositório (fora do git)."""
    if em_fabric():
        return Path(os.environ.get("ALS_PASTA_DADOS", "/lakehouse/default/Files/als_oilmodel"))
    return Path(os.environ.get("ALS_PASTA_DADOS", raiz_local / "data"))


def salvar_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
