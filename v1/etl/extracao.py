import pandas as pd

from pathlib import Path

from .base import Extractor

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