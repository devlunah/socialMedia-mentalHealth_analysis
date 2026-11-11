import pandas as pd

class Transform:
    def __init__(self, colunas_obrigatorias: list[str] | None = None, remover_duplicados: bool = False, tipos: dict[str, str] | None = None, faixas=None, acao_faixas="nulo"):
        self.colunas_obrigatorias = colunas_obrigatorias or []
        self.remover_duplicados = remover_duplicados
        self.tipos = tipos or {}
        self.faixas = faixas or {}
        self.acao_faixas = acao_faixas

    def padronizar_colunas(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        df.columns = (df.columns.str.strip().str.lower().str.replace(" ", "_"))

        # df.copy(): cria uma cópia, para não alterar o DataFrame original.
        # .str.strip(): remove espaços do começo e do fim do nome.
        # .str.lower(): converte para minúsculas.
        # .str.replace(" ", "_"): troca espaços no meio por underline.

        return df

    def limpar_textos(self, df):
        df = df.copy()

        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].str.strip()

        return df

    def validar(self, df):
        faltando = set(self.colunas_obrigatorias) - set(df.columns)

        if faltando:
            raise ValueError(f"Colunas ausentes: {faltando}\n"
                             f"Colunas encontradas: {list(df.columns)}")

    def tratar_faixas(self, df: pd.DataFrame) -> pd.DataFrame:
        acoes_validas = {"nulo", "limitar", "remover", "sinalizar"}
        if self.acao_faixas not in acoes_validas:
            raise ValueError(f"acao_faixas deve ser uma de: {acoes_validas}")

        df = df.copy()
        for col, (minimo, maximo) in self.faixas.items():
            fora = pd.Series(False, index=df.index)
            if minimo is not None:
                fora |= df[col] < minimo
            if maximo is not None:
                fora |= df[col] > maximo

            qtd = int(fora.sum())
            if qtd == 0:
                continue

            print(f"Faixa: {qtd} valores fora em '{col}' -> ação: {self.acao_faixas}")

            if self.acao_faixas == "nulo":
                df[col] = df[col].mask(fora)
            elif self.acao_faixas == "limitar":
                df[col] = df[col].clip(lower=minimo, upper=maximo)
            elif self.acao_faixas == "remover":
                df = df[~fora]
            elif self.acao_faixas == "sinalizar":
                df[f"{col}_fora_faixa"] = fora

        return df

    def converter_tipos(self, df):
        if not self.tipos:
            return df
        
        return df.astype(self.tipos)

    def tratar_duplicados(self, df):
        if self.remover_duplicados:
            return df.drop_duplicates()
        
        return df

    def transform(self, df):
        df = self.padronizar_colunas(df)
        df = self.limpar_textos(df)

        self.validar(df)

        df = self.tratar_faixas(df)  
        df = self.converter_tipos(df)
        df = self.tratar_duplicados(df)

        return df


class SocialMediaTransform(Transform):
    """Regras específicas da base de redes sociais e saúde mental.."""

    COLUNAS_OBRIGATORIAS = [
        "age", "gender", "most_used_platform", "daily_screen_hours",
        "night_time_use", "minutes_to_first_check_after_waking", "avg_sleep_hours",
        "anxiety_score_0to27", "low_mood_score_0to27", "life_satisfaction_1to10",
        "loneliness_1to10", "self_esteem_1to10", "fomo_1to10",
        "social_comparison_1to10", "physical_activity_days_per_week",
        "uses_screen_time_limits", "seeks_mental_health_support",
    ]

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

    def __init__(self, **kwargs):
        kwargs.setdefault("colunas_obrigatorias", self.COLUNAS_OBRIGATORIAS)
        kwargs.setdefault("faixas", self.FAIXAS)
        super().__init__(**kwargs)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = super().transform(df)   # tratamento geral + faixas

        # gender: 70 nulos unificados à categoria já existente (1% dos dados).
        df["gender"] = df["gender"].fillna("Prefer not to say")

        # avg_sleep_hours: 105 nulos mantidos de propósito 
        # (O que eu fiz:	    Média de sono:	Relação entre sono e ansiedade
        # Deixei em branco	    6,965 horas	    -0,257
        # Preenchi com a média	6,965 horas	    -0,255
        # resultados muito parecidos para fazer alguma alteração nos valores nulos...)
        
        return df