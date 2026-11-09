from exploracao import Explorer
from etl.extracao import ExtractCSV
from etl.tratamento import SocialMediaTransform
from etl.load import CSVLoader
from etl.pipeline import Pipeline


def main():
    pipeline = Pipeline(
        extractor=ExtractCSV("social_media_screentime_mental_health_2026.csv", sep=","),
        transformer=SocialMediaTransform(),
        loader=CSVLoader("saida/df_limpo.csv"),
    )
    resultado = pipeline.run()
    Explorer().resumo_geral(resultado)


if __name__ == "__main__":
    main()