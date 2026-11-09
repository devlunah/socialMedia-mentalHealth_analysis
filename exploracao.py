import pandas as pd

class Explorer:
    """Gera um resumo dos dados. Só lê, nunca altera."""

    def resumo(self, df: pd.DataFrame) -> None:
        print("Estrutura do DF: \n")
        df.info()

        print("\nEstatísticas:")
        print(df.describe(include="all"))

        print("\nNulos por coluna:")
        print(df.isna().sum())

        print(f"\nDuplicadas: {df.duplicated().sum()}")