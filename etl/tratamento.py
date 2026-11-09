import pandas as pd

class Transform:
    def __init__(self, colunas_obrigatorias: list[str] | None = None, remover_duplicados: bool = False, tipos: dict[str, str] | None = None):
        self.colunas_obrigatorias = colunas_obrigatorias or []
        self.remover_duplicados = remover_duplicados
        self.tipos = tipos or {}

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
            raise ValueError(f"Colunas ausentes: {faltando}")

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

        df = self.converter_tipos(df)
        df = self.tratar_duplicados(df)

        return df