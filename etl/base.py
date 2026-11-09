from abc import ABC, abstractmethod
import pandas as pd


class Extractor(ABC):
    """Contrato: toda fonte de dados deve implementar extract()."""

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        pass

    # regra: quem herdar de Extractor precisa criar um método chamado extract() que devolve uma tabela

class Loader(ABC):
    """Contrato: todo destino de dados deve implementar load()."""

    @abstractmethod
    def load(self, df: pd.DataFrame) -> None:
        pass