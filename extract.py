import pandas as pd
import re

from pathlib import Path

from base import Extractor

class ExtractCSV(Extractor):
    def __init__(self, caminho: str, **kwargs):
        self.caminho = caminho
        self.kwargs = kwargs

    def extract(self) -> pd.DataFrame:
        if not Path(self.caminho).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.caminho}")
        
        return pd.read_csv(self.caminho, **self.kwargs)

    '''
    O pd.read_csv tem dezenas de opções (sep, encoding, header, skiprows, dtype, usecols...). 
    Em vez de declarar uma por uma no CSVExtractor, usamos **kwargs para repassar tudo direto ao pandas
    '''


# extrator = ExtractCSV(
#     "social_media_screentime_mental_health_2026_v2.csv",
#     encoding="utf-8-sig",
#     dtype="string",
#     na_filter=False,
#     skip_blank_lines=False,
# )

# df_bruto = extrator.extract()

# colunas = [
#     re.sub(r"\s+", "_", nome.strip().casefold())
#     for nome in df_bruto.columns
# ]

# if len(colunas) != len(set(colunas)):
#     raise ValueError("Há cabeçalhos duplicados após a padronização.")

# faltantes = sorted(set(COLUNAS_ESPERADAS) - set(colunas))
# extras = sorted(set(colunas) - set(COLUNAS_ESPERADAS))

# if faltantes or extras:
#     raise ValueError(
#         f"Cabeçalho incompatível. Faltantes: {faltantes}. Extras: {extras}."
#     )

# df_bruto.columns = colunas
# df_bruto.insert(0, "_source_record", range(1, len(df_bruto) + 1))