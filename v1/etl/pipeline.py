import pandas as pd

from .base import Extractor, Loader
from .tratamento import Transform


class Pipeline:
    def __init__(self, extractor: Extractor, transformer: Transform, loader: Loader):
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader

    def run(self) -> pd.DataFrame:
        print("Extraindo...")
        df = self.extractor.extract()
        print(f"  {df.shape[0]} linhas, {df.shape[1]} colunas lidas")

        print("Transformando...")
        df = self.transformer.transform(df)
        print(f"  {df.shape[0]} linhas, {df.shape[1]} colunas após tratamento")

        print("Carregando...")
        self.loader.load(df)
        print("Concluído.")
        
        return df