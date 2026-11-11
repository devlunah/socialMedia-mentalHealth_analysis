import pandas as pd

from schema import (ALIASES_CATEGORIAS, COLUNAS_ESPERADAS, FAIXAS, IDADES_POR_EXTENSO, MAPA_BOOLEANOS, MARCADORES_DE_AUSENCIA, TIPOS_FINAIS)


COLUNAS_CATEGORICAS = (
    "gender",
    "occupation",
    "region",
    "most_used_platform",
    "night_time_use",
    "primary_purpose",
    "attempted_digital_detox",
    "seeks_mental_health_support",
    "wellbeing_band",
)


def remover_vazios_e_duplicatas(
    df_bruto: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dados_origem = df_bruto[COLUNAS_ESPERADAS]

    # A linha é vazia se todos os campos estiverem nulos,
    # em branco ou preenchidos apenas com espaços.
    campos_vazios = dados_origem.apply(
        lambda coluna: coluna.str.strip().fillna("").eq("")
    )
    linhas_vazias = campos_vazios.all(axis=1)

    sem_vazios = df_bruto.loc[~linhas_vazias]
    duplicatas = sem_vazios.duplicated(
        subset=COLUNAS_ESPERADAS,
        keep="first",
    )

    descartes = pd.concat(
        [
            df_bruto.loc[linhas_vazias].assign(motivo="linha_vazia"),
            sem_vazios.loc[duplicatas].assign(motivo="duplicata_exata"),
        ]
    ).sort_values("_source_record")

    dados = sem_vazios.loc[~duplicatas].copy()
    return dados, descartes

def padronizar_categorias(df: pd.DataFrame) -> pd.DataFrame:
    dados = df.copy()

    ids = dados["participant_id"].str.strip()
    dados["participant_id"] = ids.mask(ids.eq(""))

    for coluna in COLUNAS_CATEGORICAS:
        valores = dados[coluna].str.strip().str.casefold()

        marcadores = MARCADORES_DE_AUSENCIA.get(coluna, set())
        ausentes = valores.eq("") | valores.isin(marcadores)
        valores = valores.mask(ausentes)

        aliases = ALIASES_CATEGORIAS.get(coluna, {})
        dados[coluna] = valores.replace(aliases)

    return dados

def converter_numeros_e_booleanos(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dados = df.copy()
    ocorrencias = []

    def registrar(coluna: str, mascara: pd.Series, motivo: str) -> None:
        for indice, registro in dados.loc[mascara, "_source_record"].items():
            ocorrencias.append({
                "_source_record": registro,
                "coluna": coluna,
                "valor_bruto": df.at[indice, coluna],
                "motivo": motivo,
            })

    for coluna, (minimo, maximo) in FAIXAS.items():
        texto = dados[coluna].str.strip().str.casefold()
        marcadores = MARCADORES_DE_AUSENCIA.get(coluna, set())
        texto = texto.mask(texto.eq("") | texto.isin(marcadores))

        if coluna == "age":
            idades = {chave: str(valor) for chave, valor in IDADES_POR_EXTENSO.items()}
            texto = texto.replace(idades).str.replace(r"\s+years?$", "", regex=True)

        if coluna in {"daily_screen_hours", "avg_sleep_hours"}:
            texto = texto.str.replace(r"\s*(?:hours?|h)$", "", regex=True)

        texto = texto.str.replace(",", ".", regex=False)
        numeros = pd.to_numeric(texto, errors="coerce")

        formato_invalido = texto.notna() & (
            numeros.isna() | numeros.isin([float("inf"), float("-inf")])
        )
        registrar(coluna, formato_invalido, "numero_invalido")
        numeros = numeros.mask(formato_invalido)

        tipo = TIPOS_FINAIS[coluna]
        if tipo == "Int64":
            fracionarios = numeros.mod(1).ne(0).fillna(False)
            registrar(coluna, fracionarios, "esperado_inteiro")
            numeros = numeros.mask(fracionarios)

        fora_da_faixa = numeros.lt(minimo)
        if maximo is not None:
            fora_da_faixa = fora_da_faixa | numeros.gt(maximo)

        fora_da_faixa = fora_da_faixa.fillna(False)
        registrar(coluna, fora_da_faixa, "fora_da_faixa")
        dados[coluna] = numeros.mask(fora_da_faixa).astype(tipo)

    coluna = "uses_screen_time_limits"
    texto = dados[coluna].str.strip().str.casefold()
    texto = texto.mask(texto.eq(""))
    booleanos = texto.map(MAPA_BOOLEANOS)

    registrar(coluna, texto.notna() & booleanos.isna(), "booleano_invalido")
    dados[coluna] = booleanos.astype("boolean")

    auditoria = pd.DataFrame(
        ocorrencias,
        columns=["_source_record", "coluna", "valor_bruto", "motivo"],
    )
    return dados, auditoria

def resolver_ids_repetidos(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dados = df.sort_values("_source_record")

    sem_id = dados["participant_id"].isna()
    com_id = dados.loc[~sem_id]

    equivalentes = com_id.duplicated(
        subset=COLUNAS_ESPERADAS,
        keep="first",
    )
    versoes_distintas = com_id.loc[~equivalentes]

    conflitos = versoes_distintas["participant_id"].duplicated(keep=False)
    ids_em_conflito = versoes_distintas.loc[conflitos, "participant_id"]

    # Inclui todas as linhas de um ID conflitante na revisão.
    em_conflito = com_id["participant_id"].isin(ids_em_conflito)

    revisao = pd.concat([
        dados.loc[sem_id].assign(motivo="id_ausente"),
        com_id.loc[em_conflito].assign(motivo="conflito_por_id"),
        com_id.loc[equivalentes & ~em_conflito].assign(
            motivo="duplicata_apos_padronizacao"
        ),
    ]).sort_values("_source_record")

    dados_unicos = com_id.loc[~equivalentes & ~em_conflito].copy()
    return dados_unicos, revisao

def comparar_ids_com_referencia(
    df: pd.DataFrame,
    referencia: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ids_referencia = referencia["participant_id"].astype("string").str.strip()
    ids_referencia = ids_referencia.mask(ids_referencia.eq(""))

    if ids_referencia.isna().any() or not ids_referencia.is_unique:
        raise ValueError("A referência deve ter IDs preenchidos e únicos.")

    pertence_a_referencia = df["participant_id"].isin(ids_referencia)

    dados_analiticos = df.loc[pertence_a_referencia].copy()
    ids_extras = df.loc[~pertence_a_referencia].assign(
        motivo="id_fora_da_referencia"
    )

    presentes_na_saida = ids_referencia.isin(dados_analiticos["participant_id"])
    ids_originais_ausentes = (
        ids_referencia.loc[~presentes_na_saida]
        .sort_values()
        .to_frame()
        .reset_index(drop=True)
    )

    return dados_analiticos, ids_extras, ids_originais_ausentes