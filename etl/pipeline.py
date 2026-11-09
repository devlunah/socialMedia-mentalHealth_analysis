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
        print(f"  {len(df)} linhas lidas")

        print("Transformando...")
        df = self.transformer.transform(df)
        print(f"  {len(df)} linhas após tratamento")

        print("Carregando...")
        self.loader.load(df)
        print("Concluído.")
        
        return df