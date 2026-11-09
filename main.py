from etl.extracao import ExtractCSV
from etl.tratamento import Transform
from etl.load import CSVLoader
from etl.pipeline import Pipeline


def main():
    pipeline = Pipeline(
        extractor=ExtractCSV("vendas.csv", sep=";"),
        transformer=Transform(colunas_obrigatorias=["produto", "valor"]),
        loader=CSVLoader("saida/vendas_limpas.csv"),
    )
    resultado = pipeline.run()
    print(resultado.head())


if __name__ == "__main__":
    main()