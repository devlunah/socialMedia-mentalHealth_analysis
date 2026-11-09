import pandas as pd

from pathlib import Path

from .base import Loader

class CSVLoader(Loader):
    def __init__(self, destino: str, **kwargs):
        self.destino = destino
        self.kwargs = kwargs

    def load(self, df: pd.DataFrame) -> None:
        Path(self.destino).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.destino, index=False, **self.kwargs)