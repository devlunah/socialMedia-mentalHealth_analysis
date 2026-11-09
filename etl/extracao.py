import pandas as pd

from .base import Extractor

class ExtractCSV(Extractor):
    def __init__(self, caminho: str, **kwargs):
        self.caminho = caminho
        self.kwargs = kwargs

    def extract(self) -> pd.DataFrame:
        return pd.read_csv(self.caminho, **self.kwargs)

