import pandas as pd

class Explorer:
    """Gera um resumo dos dados. Só lê, nunca altera."""

    def resumo_geral(self, df: pd.DataFrame) -> None:
        print("Estrutura do DF: \n")
        df.info()

        print("\nEstatísticas:")
        print(df.describe(include="all"))

        print("\nNulos por coluna:")
        print(df.isna().sum())

        print(f"\nDuplicadas: {df.duplicated().sum()}")

    def resumo_nulos(self, df: pd.DataFrame, amostra: int = 5) -> None:
        """Para cada coluna com nulos, mostra o que ela guarda e como as linhas nulas se comparam às demais."""
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)

        nulos = df.isna().sum()
        nulos = nulos[nulos > 0]

        if nulos.empty:
            print("Nenhuma coluna com nulos.")
            return

        for col in nulos.index:
            serie = df[col]
            qtd = nulos[col]

            print("=" * 60)
            print(f"COLUNA: {col}  |  tipo: {serie.dtype}")
            print(f"Nulos: {qtd} de {len(df)} ({qtd / len(df):.1%})")
            print(f"Valores distintos (sem nulos): {serie.nunique()}")

            # 1) O que a coluna guarda
            if pd.api.types.is_numeric_dtype(serie):
                print("\nResumo numérico:")
                print(serie.describe().round(2))

                print("\nValores mais frequentes:")
                print(serie.value_counts().head(10))

                print("\nDistribuição por faixas:")
                print(serie.value_counts(bins=6, sort=False))
            else:
                print("\nValores existentes:")
                print(serie.value_counts(dropna=False))

            # 2) Como são as linhas com nulo
            print(f"\nAmostra de linhas com nulo em '{col}':")
            print(df[serie.isna()].head(amostra).T)

            # 3) Elas são diferentes das demais?
            colunas_num = df.select_dtypes(include="number").columns.drop(col, errors="ignore")
            comparacao = df.groupby(serie.isna())[colunas_num].mean().round(2).T
            comparacao.columns = ["Com valor", "Nulo"]
            print("\nMédia das outras colunas numéricas (linhas com valor × linhas nulas):")
            print(comparacao)

    def resumo_duplicados(self, df: pd.DataFrame, coluna_id: str | None = None, amostra: int = 5) -> None:
        """Verifica linhas duplicadas de três formas e mostra os casos encontrados."""
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)

        print(f"Total de linhas: {len(df)}\n")

        # 1) Linhas totalmente idênticas
        identicas = df.duplicated().sum()
        print(f"1) Linhas totalmente idênticas: {identicas}")

        chave = list(df.columns)

        if coluna_id:
            # 2) Idênticas ignorando o id
            chave = [c for c in df.columns if c != coluna_id]
            sem_id = df.duplicated(subset=chave).sum()
            print(f"2) Linhas idênticas ignorando '{coluna_id}': {sem_id}")

            # 3) IDs repetidos
            ids_repetidos = df[coluna_id].duplicated().sum()
            print(f"3) Valores repetidos em '{coluna_id}': {ids_repetidos}")

        # Mostrar os casos (keep=False traz TODAS as linhas do grupo, não só as repetições)
        casos = df[df.duplicated(subset=chave, keep=False)]
        if casos.empty:
            print("\nNenhum registro duplicado encontrado.")
        else:
            print(f"\nAmostra dos registros duplicados (agrupados):")
            print(casos.sort_values(chave).head(amostra * 2).T)

    def conferir_faixas(self, df: pd.DataFrame, regras: dict, amostra: int = 5) -> None:
        """Confere se os valores numéricos estão dentro das faixas esperadas.

        regras: {coluna: (minimo, maximo)}. Use None para um lado sem limite.
        """
        print(f"{'coluna':38s}{'min':>8}{'max':>8}{'esperado':>14}{'fora':>7}")
        print("-" * 75)
        problemas = {}

        for col, (minimo, maximo) in regras.items():
            if col not in df.columns:
                print(f"{col:38s} coluna não encontrada")
                continue

            serie = df[col]
            fora = pd.Series(False, index=df.index)
            if minimo is not None:
                fora |= serie < minimo
            if maximo is not None:
                fora |= serie > maximo

            esperado = f"{minimo if minimo is not None else '-'} a {maximo if maximo is not None else '-'}"
            print(f"{col:38s}{serie.min():>8}{serie.max():>8}{esperado:>14}{fora.sum():>7}")

            if fora.any():
                problemas[col] = fora

        if not problemas:
            print("\nTodos os valores dentro das faixas esperadas.")
            return

        for col, mascara in problemas.items():
            print(f"\nValores fora da faixa em '{col}' (amostra):")
            print(df.loc[mascara, ["participant_id", col]].head(amostra))


FAIXAS = {
    "age": (0, 120),
    "daily_screen_hours": (0, 24),
    "daily_notifications": (0, None),
    "minutes_to_first_check_after_waking": (0, None),
    "avg_sleep_hours": (0, 24),
    "anxiety_score_0to27": (0, 27),
    "life_satisfaction_1to10": (1, 10),
    "loneliness_1to10": (1, 10),
    "self_esteem_1to10": (1, 10),
    "fomo_1to10": (1, 10),
    "social_comparison_1to10": (1, 10),
    "physical_activity_days_per_week": (0, 7),
    "platforms_used_count": (1, None),
}

if __name__ == "__main__":
    from etl.extracao import ExtractCSV

    df = ExtractCSV("social_media_screentime_mental_health_2026.csv").extract()
    Explorer().conferir_faixas(df, FAIXAS)
    Explorer().resumo_geral(df)
    Explorer().resumo_nulos(df)
    Explorer().resumo_duplicados(df, coluna_id="participant_id")