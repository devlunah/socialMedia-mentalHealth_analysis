import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from schema import COLUNAS_ESPERADAS, FAIXAS, TIPOS_FINAIS


TIPOS_SQLITE = {
    "string": "TEXT",
    "Int64": "INTEGER",
    "Float64": "REAL",
    "boolean": "INTEGER",
}


def carregar_participantes(df: pd.DataFrame, caminho: str | Path) -> int:
    dados = df.loc[:, COLUNAS_ESPERADAS]
    definicoes = []

    for coluna in COLUNAS_ESPERADAS:
        tipo = TIPOS_SQLITE[TIPOS_FINAIS[coluna]]
        definicao = f'"{coluna}" {tipo}'

        if coluna == "participant_id":
            definicao += ' PRIMARY KEY NOT NULL CHECK (trim("participant_id") <> \'\')'

        if coluna in FAIXAS:
            minimo, maximo = FAIXAS[coluna]
            definicao += f' CHECK ("{coluna}" >= {minimo})'
            if maximo is not None:
                definicao += f' CHECK ("{coluna}" <= {maximo})'

        if TIPOS_FINAIS[coluna] == "boolean":
            definicao += f' CHECK ("{coluna}" IN (0, 1))'

        definicoes.append(definicao)

    nomes = ", ".join(f'"{coluna}"' for coluna in COLUNAS_ESPERADAS)
    parametros = ", ".join("?" for _ in COLUNAS_ESPERADAS)

    # Converte pd.NA em None para gravar NULL no SQLite.
    dados_sql = dados.astype(object).where(dados.notna(), None)
    registros = dados_sql.itertuples(index=False, name=None)

    with closing(sqlite3.connect(caminho)) as conexao, conexao:
        conexao.execute("BEGIN")
        conexao.execute(
            f"CREATE TABLE IF NOT EXISTS participantes ({', '.join(definicoes)})"
        )
        conexao.execute("DELETE FROM participantes")
        conexao.executemany(
            f"INSERT INTO participantes ({nomes}) VALUES ({parametros})",
            registros,
        )

        total = conexao.execute(
            "SELECT COUNT(*) FROM participantes"
        ).fetchone()[0]

        if total != len(dados):
            raise ValueError("A contagem no SQLite difere da saída analítica.")

    return total


def exportar_participantes(
    caminho_banco: str | Path,
    caminho_csv: str | Path,
) -> int:
    banco = Path(caminho_banco).resolve()

    with closing(sqlite3.connect(f"{banco.as_uri()}?mode=ro", uri=True)) as conexao:
        dados = pd.read_sql_query(
            "SELECT * FROM participantes ORDER BY participant_id",
            conexao,
        )

    # Preserva 0 e 1 como inteiros, mesmo quando há valores ausentes.
    tipos_inteiros = {
        coluna: "Int64"
        for coluna, tipo in TIPOS_FINAIS.items()
        if tipo in {"Int64", "boolean"}
    }
    dados = dados.astype(tipos_inteiros)
    dados.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    return len(dados)