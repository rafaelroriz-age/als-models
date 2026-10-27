"""
Discover schemas, tables, and columns from Fabric SQL endpoints.
Uses azure-identity for authentication and pyodbc for SQL queries.
"""

import pyodbc
import json
from pathlib import Path
import struct
from azure.identity import InteractiveBrowserCredential
from typing import Dict, List, Tuple

# Configuration
LAKEHOUSES = {
    "LakehouseOel": "LakehouseOel",
    "Ontology_OeL": "Ontology_OeL_lh_17803110c5844a0cbb9f60e1d2a86ebf",
    "s360": "s360",
}

SQL_ENDPOINT = "j2qfysdun5iebf3ezw2l7ke4eu-vpyatc664ptezeejap7oap22qu.datawarehouse.fabric.microsoft.com"
OUTPUT_DIR = Path(__file__).parent.parent / "docs_fabric"


def get_access_token() -> str:
    """Get access token using DefaultAzureCredential."""
    credential = InteractiveBrowserCredential()
    token = credential.get_token("https://database.windows.net/.default")
    return token.token


def connect_to_lakehouse(lakehouse_name: str, access_token: str) -> pyodbc.Connection:
    """Connect to a Fabric SQL endpoint using access token."""
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={SQL_ENDPOINT};"
        f"Database={lakehouse_name};"
        f"Encrypt=yes;TrustServerCertificate=no;"
    )
    token_bytes = access_token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256
    return pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})


def get_schemas(conn: pyodbc.Connection) -> List[str]:
    """List all schemas in the database."""
    query = """
    SELECT DISTINCT TABLE_SCHEMA
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA
    """
    cursor = conn.cursor()
    cursor.execute(query)
    schemas = [row[0] for row in cursor.fetchall()]
    return schemas


def get_tables(conn: pyodbc.Connection, schema: str) -> List[Tuple[str, str]]:
    """Get tables for a specific schema with row counts."""
    query = """
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = ?
    AND TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
    """
    cursor = conn.cursor()
    cursor.execute(query, schema)
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def get_columns(conn: pyodbc.Connection, schema: str, table: str) -> List[Dict]:
    """Get columns and types for a table."""
    query = """
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = ?
    AND TABLE_NAME = ?
    ORDER BY ORDINAL_POSITION
    """
    cursor = conn.cursor()
    cursor.execute(query, schema, table)
    columns = [
        {
            "name": row[0],
            "type": row[1],
            "nullable": row[2] == "YES"
        }
        for row in cursor.fetchall()
    ]
    return columns


def probe_lakehouse(lakehouse_name: str, lakehouse_label: str, access_token: str) -> Dict:
    """Probe a single lakehouse and return schema information."""
    print(f"\nProbing {lakehouse_label} ({lakehouse_name})...")

    try:
        conn = connect_to_lakehouse(lakehouse_name, access_token)
        schemas = get_schemas(conn)
        print(f"   Found {len(schemas)} schema(s): {', '.join(schemas)}")

        result = {
            "lakehouse": lakehouse_label,
            "endpoint": SQL_ENDPOINT,
            "schemas": {}
        }

        for schema in schemas:
            tables = get_tables(conn, schema)
            print(f"   - {schema}: {len(tables)} table(s)")

            schema_data = {}
            for table in tables:
                columns = get_columns(conn, schema, table)
                schema_data[table] = {
                    "column_count": len(columns),
                    "columns": columns
                }
                print(f"      - {table} ({len(columns)} cols)")

            result["schemas"][schema] = schema_data

        conn.close()
        return result

    except Exception as e:
        print(f"   Error: {e}")
        return {"lakehouse": lakehouse_label, "error": str(e)}


def main():
    """Main probe function."""
    print("Fabric SQL Endpoint Probe")
    print(f"   Endpoint: {SQL_ENDPOINT}")
    print(f"   Lakehouses: {', '.join(LAKEHOUSES.keys())}")

    try:
        # Get access token once
        print("\nAuthenticating with Azure Identity...")
        token = get_access_token()
        print("   Authentication successful")

        # Probe each lakehouse
        results = {}
        for label, name in LAKEHOUSES.items():
            results[label] = probe_lakehouse(name, label, token)

        # Save results to markdown
        output_file = OUTPUT_DIR / "08_dicionario_de_dados_discovery.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Descoberta de Dados do Fabric\n\n")
            f.write(f"**Endpoint**: `{SQL_ENDPOINT}`\n\n")

            for label, data in results.items():
                if "error" in data:
                    f.write(f"## {label}\n\n")
                    f.write(f"Erro: {data['error']}\n\n")
                    continue

                f.write(f"## {label}\n\n")

                for schema, tables in data.get("schemas", {}).items():
                    f.write(f"### Schema: `{schema}`\n\n")

                    for table, table_info in tables.items():
                        f.write(f"#### Tabela: `{table}`\n\n")
                        f.write(f"**Colunas**: {table_info['column_count']}\n\n")
                        f.write("| Coluna | Tipo | Nullable |\n")
                        f.write("|--------|------|----------|\n")

                        for col in table_info["columns"]:
                            nullable = "✓" if col["nullable"] else "✗"
                            f.write(f"| `{col['name']}` | `{col['type']}` | {nullable} |\n")

                        f.write("\n")

        print(f"\nResults saved to: {output_file}")

        # Also save raw JSON
        json_file = OUTPUT_DIR / "fabric_probe_results.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Raw JSON saved to: {json_file}")

    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
