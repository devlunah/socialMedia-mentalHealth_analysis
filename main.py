import re

import pandas as pd

from extract import ExtractCSV
from load import carregar_participantes, exportar_participantes
from pathlib import Path
from schema import COLUNAS_ESPERADAS
from transform import comparar_ids_com_referencia, converter_numeros_e_booleanos, padronizar_categorias, remover_vazios_e_duplicatas,  resolver_ids_repetidos 


CATEGORIAS_ACEITAS = {
    "gender": {"female", "male", "non-binary", "prefer not to say"},
    "occupation": {
        "full-time employed", "part-time employed", "retired",
        "self-employed", "student", "unemployed",
    },
    "region": {
        "africa", "asia", "europe", "latin america", "north america", "oceania",
    },
    "most_used_platform": {
        "facebook", "instagram", "linkedin", "reddit",
        "snapchat", "tiktok", "x/twitter", "youtube",
    },
    "night_time_use": {"never", "sometimes", "often", "every night"},
    "primary_purpose": {
        "connection with friends", "content creation", "entertainment",
        "news/information", "passing time/boredom", "work/career",
    },
    "attempted_digital_detox": {"no", "yes, failed", "yes, succeeded"},
    "seeks_mental_health_support": {"no", "considering it", "yes"},
    "wellbeing_band": {"good", "moderate", "at-risk"},
}

def preparar_entrada(df: pd.DataFrame) -> pd.DataFrame:
    colunas = [
        re.sub(r"\s+", "_", coluna.strip().casefold())
        for coluna in df.columns
    ]

    if len(colunas) != len(set(colunas)):
        raise ValueError("Há cabeçalhos duplicados após a normalização.")

    esperadas = set(COLUNAS_ESPERADAS)
    recebidas = set(colunas)
    faltantes = sorted(esperadas - recebidas)
    extras = sorted(recebidas - esperadas)

    if faltantes or extras:
        raise ValueError(
            f"Cabeçalho incompatível. Faltantes: {faltantes}. Extras: {extras}."
        )

    dados = df.set_axis(colunas, axis="columns")
    dados.insert(0, "_source_record", range(1, len(dados) + 1))
    return dados


def validar_categorias(
    df: pd.DataFrame,
    df_bruto: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dados = df.copy()
    bruto_por_registro = df_bruto.set_index("_source_record")
    ocorrencias = []

    for coluna, aceitas in CATEGORIAS_ACEITAS.items():
        valores = dados[coluna]
        invalidos = valores.notna() & ~valores.isin(aceitas)
        registros = dados.loc[invalidos, "_source_record"]

        for registro in registros:
            ocorrencias.append({
                "_source_record": registro,
                "coluna": coluna,
                "valor_bruto": bruto_por_registro.at[registro, coluna],
                "motivo": "categoria_desconhecida",
            })

        dados.loc[invalidos, coluna] = pd.NA

    auditoria = pd.DataFrame(
        ocorrencias,
        columns=["_source_record", "coluna", "valor_bruto", "motivo"],
    )
    return dados, auditoria


def auditar_divergencias(
    tratado: pd.DataFrame,
    original: pd.DataFrame,
) -> pd.DataFrame:
    colunas_comparaveis = [
        coluna for coluna in COLUNAS_ESPERADAS
        if coluna != "participant_id"
    ]

    tratado_por_id = tratado.set_index("participant_id")[colunas_comparaveis]
    original_por_id = original.set_index("participant_id").loc[
        tratado_por_id.index, colunas_comparaveis
    ]

    partes = []

    for coluna in colunas_comparaveis:
        valor_tratado = tratado_por_id[coluna]
        valor_original = original_por_id[coluna]

        iguais = (
            valor_tratado.eq(valor_original).fillna(False)
            | (valor_tratado.isna() & valor_original.isna())
        )

        diferencas = pd.DataFrame({
            "valor_original": valor_original.loc[~iguais],
            "valor_tratado": valor_tratado.loc[~iguais],
        })
        diferencas["coluna"] = coluna
        diferencas["tipo"] = "valor_alterado"
        diferencas.loc[
            diferencas["valor_tratado"].isna(), "tipo"
        ] = "ausente_na_saida"
        diferencas.loc[
            diferencas["valor_original"].isna(), "tipo"
        ] = "preenchido_na_saida"

        partes.append(diferencas.reset_index())

    auditoria = pd.concat(partes, ignore_index=True)
    return auditoria[
        ["participant_id", "coluna", "valor_original", "valor_tratado", "tipo"]
    ]


def main() -> None:
    extrator = ExtractCSV(
        "social_media_screentime_mental_health_2026_v2.csv",
        encoding="utf-8-sig",
        dtype="string",
        na_filter=False,
        skip_blank_lines=False,
    )
    df_bruto = preparar_entrada(extrator.extract())

    df_sem_duplicatas, descartes = remover_vazios_e_duplicatas(df_bruto)
    df_padronizado = padronizar_categorias(df_sem_duplicatas)
    df_convertido, erros_conversao = converter_numeros_e_booleanos(
        df_padronizado
    )
    df_ids_unicos, revisao_ids = resolver_ids_repetidos(df_convertido)

    ids = df_ids_unicos["participant_id"]
    if ids.isna().any() or not ids.is_unique:
        raise ValueError("A saída deve ter IDs preenchidos e únicos.")

    if len(df_ids_unicos) + len(revisao_ids) != len(df_convertido):
        raise ValueError("A contagem não fechou após a resolução de IDs.")

    extrator_referencia = ExtractCSV(
        "social_media_screentime_mental_health_2026.csv",
        encoding="utf-8-sig",
        dtype="string",
        na_filter=False,
    )
    referencia = preparar_entrada(extrator_referencia.extract())

    df_analitico, ids_extras, ids_originais_ausentes = comparar_ids_com_referencia(
        df_ids_unicos,
        referencia,
    )

    if len(df_analitico) + len(ids_extras) != len(df_ids_unicos):
        raise ValueError("A contagem dos IDs tratados não fechou.")

    if len(df_analitico) + len(ids_originais_ausentes) != len(referencia):
        raise ValueError("A contagem dos IDs da referência não fechou.")

    ids_em_conflito = revisao_ids.loc[
        revisao_ids["motivo"].eq("conflito_por_id"),
        "participant_id",
    ]
    ausentes_em_conflito = ids_originais_ausentes["participant_id"].isin(
        ids_em_conflito
    )

    df_analitico, erros_categorias = validar_categorias(df_analitico, df_bruto)

    referencia_padronizada = padronizar_categorias(referencia)
    referencia_convertida, erros_referencia = converter_numeros_e_booleanos(
        referencia_padronizada
    )
    auditoria_divergencias = auditar_divergencias(
        df_analitico, referencia_convertida
    )

    print(f"Registros de entrada: {len(df_bruto)}")
    print(
        "Após remover linhas vazias e duplicatas exatas:",
        len(df_sem_duplicatas),
    )
    print(descartes["motivo"].value_counts().to_string())

    print(f"\nOcorrências de conversão: {len(erros_conversao)}")
    if not erros_conversao.empty:
        print(erros_conversao["motivo"].value_counts().to_string())

    print(f"\nRegistros após resolver IDs: {len(df_ids_unicos)}")
    if not revisao_ids.empty:
        print(revisao_ids["motivo"].value_counts().to_string())

    print(f"\nParticipantes na saída analítica: {len(df_analitico)}")
    print(f"IDs fora da referência: {len(ids_extras)}")
    print(f"IDs originais ausentes por conflito: {ausentes_em_conflito.sum()}")
    print(f"IDs originais ausentes a investigar: {(~ausentes_em_conflito).sum()}")
    print(f"Categorias desconhecidas na saída: {len(erros_categorias)}")
    print(f"Ocorrências na conversão do original: {len(erros_referencia)}")

    print(f"\nCampos divergentes: {len(auditoria_divergencias)}")
    print(
        "Participantes com alguma divergência:",
        auditoria_divergencias["participant_id"].nunique(),
    )
    if not auditoria_divergencias.empty:
        print(auditoria_divergencias.head(10).to_string(index=False))

    pasta_saida = Path("saida")
    pasta_saida.mkdir(exist_ok=True)
    caminho_banco = Path("redes_sociais.db")

    total_carregado = carregar_participantes(df_analitico, caminho_banco)
    total_exportado = exportar_participantes(
        caminho_banco,
        pasta_saida / "participantes.csv",
    )

    if total_exportado != total_carregado:
        raise ValueError("A quantidade exportada difere da carga no SQLite.")

    relatorios = {
        "linhas_descartadas": descartes,
        "erros_conversao": erros_conversao,
        "revisao_ids": revisao_ids,
        "ids_extras": ids_extras,
        "ids_originais_ausentes": ids_originais_ausentes,
        "erros_categorias": erros_categorias,
        "divergencias_referencia": auditoria_divergencias,
    }

    for nome, relatorio in relatorios.items():
        relatorio.to_csv(
            pasta_saida / f"{nome}.csv",
            index=False,
            encoding="utf-8-sig",
        )

    print(f"Participantes carregados no SQLite: {total_carregado}")
    print(f"Participantes exportados para o Power BI: {total_exportado}")


if __name__ == "__main__":
    main()