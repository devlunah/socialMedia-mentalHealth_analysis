import pandas as pd

class Explorer:
    """Gera um resumo dos dados. Só lê, nunca altera."""

    @staticmethod
    def _norm(nome) -> str:
        return str(nome).strip().lower().replace(" ", "_")

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
        """Verifica duplicados no dado bruto e depois de limpar espaços dos textos."""
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)

        # Resolve o nome real do id (tolera cabeçalho sujo)
        real_id = None
        if coluna_id:
            real_id = {self._norm(c): c for c in df.columns}.get(self._norm(coluna_id))
            if real_id is None:
                print(f"Aviso: coluna '{coluna_id}' não encontrada; verificando só linhas inteiras.\n")

        # Linhas totalmente vazias são contadas à parte (senão contam como "duplicadas")
        vazias = df.isna().all(axis=1)
        base = df[~vazias]
        print(f"Total de linhas: {len(df)}  |  totalmente vazias: {vazias.sum()} (fora da contagem abaixo)\n")

        # Versão com espaços das pontas removidos nos textos
        limpo = base.apply(lambda s: s.map(lambda x: x.strip() if isinstance(x, str) else x))

        print(f"1) Linhas idênticas (dado bruto):                    {base.duplicated().sum()}")
        print(f"2) Linhas idênticas após remover espaços dos textos: {limpo.duplicated().sum()}")

        chave = list(limpo.columns)
        if real_id:
            chave = [c for c in limpo.columns if c != real_id]
            sem_id = limpo.duplicated(subset=chave).sum()
            ids_rep = limpo[real_id].duplicated().sum()
            print(f"3) Linhas idênticas ignorando '{real_id}':  {sem_id}")
            print(f"4) Valores repetidos em '{real_id}':        {ids_rep}")
            conflito = ids_rep - limpo.duplicated().sum()
            print(f"5) Ids repetidos com valores diferentes (conflito): {conflito}")

        ocultos = limpo.duplicated().sum() - base.duplicated().sum()
        if ocultos:
            print(f"\nAtenção: {ocultos} duplicados só aparecem depois de limpar espaços nos textos.")

        if real_id:
            casos = limpo[limpo.duplicated(subset=[real_id], keep=False)].sort_values(real_id)
            if not casos.empty:
                print(f"\nAmostra de ids repetidos (agrupados):")
                print(casos.head(amostra * 2).T)
        elif limpo.duplicated().any():
            print("\nAmostra de linhas duplicadas:")
            print(limpo[limpo.duplicated(keep=False)].sort_values(chave).head(amostra * 2).T)
        else:
            print("\nNenhum registro duplicado encontrado.")

    def conferir_faixas(self, df: pd.DataFrame, regras: dict,
                        coluna_id: str | None = "participant_id", amostra: int = 5) -> None:
        """Confere faixas esperadas, tolerando nomes de coluna sujos e texto em colunas numéricas.

        regras: {coluna: (minimo, maximo)}. Use None para um lado sem limite.
        """
        mapa = {self._norm(c): c for c in df.columns}
        real_id = mapa.get(self._norm(coluna_id)) if coluna_id else None

        print(f"{'coluna':38s}{'min':>8}{'max':>8}{'esperado':>14}{'fora':>7}{'texto':>7}")
        print("-" * 82)

        problemas, textos, renomeadas = {}, {}, []

        for col, (minimo, maximo) in regras.items():
            real = mapa.get(self._norm(col))
            if real is None:
                print(f"{col:38s} coluna não encontrada")
                continue
            if real != col:
                renomeadas.append((col, real))

            original = df[real]
            serie = pd.to_numeric(original, errors="coerce")
            nao_numerico = original.notna() & serie.isna()

            fora = pd.Series(False, index=df.index)
            if minimo is not None:
                fora |= serie < minimo
            if maximo is not None:
                fora |= serie > maximo

            esperado = f"{minimo if minimo is not None else '-'} a {maximo if maximo is not None else '-'}"
            print(f"{col:38s}{serie.min():>8}{serie.max():>8}{esperado:>14}{fora.sum():>7}{nao_numerico.sum():>7}")

            if fora.any():
                problemas[real] = fora
            if nao_numerico.any():
                textos[real] = original[nao_numerico]

        if renomeadas:
            print("\nColunas encontradas com nome diferente do esperado (padronize os nomes):")
            for esperado_, real in renomeadas:
                print(f"  esperado '{esperado_}'  ->  no arquivo '{real}'")

        if textos:
            print("\nValores de TEXTO em colunas que deveriam ser numéricas (mais frequentes):")
            for real, valores in textos.items():
                print(f"\n  {real}: {len(valores)} valores")
                print(valores.value_counts().head(amostra).to_string())

        if problemas:
            for real, mascara in problemas.items():
                print(f"\nValores fora da faixa em '{real}' (amostra):")
                cols = [real_id, real] if real_id else [real]
                print(df.loc[mascara, cols].head(amostra))
        elif not textos:
            print("\nTodos os valores dentro das faixas esperadas.")


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
    from v1.etl.extracao import ExtractCSV

    df = ExtractCSV("social_media_screentime_mental_health_2026_v2.csv").extract()
    Explorer().conferir_faixas(df, FAIXAS)
    Explorer().resumo_geral(df)
    Explorer().resumo_nulos(df)
    Explorer().resumo_duplicados(df, coluna_id="participant_id")