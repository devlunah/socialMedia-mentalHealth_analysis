from v1.exploracao import Explorer
from v1.etl.extracao import ExtractCSV
from v1.etl.tratamento import SocialMediaTransform
from v1.etl.load import CSVLoader
from v1.etl.pipeline import Pipeline


def main():
    pipeline = Pipeline(
        extractor=ExtractCSV("social_media_screentime_mental_health_2026_v2.csv", sep=","),
        transformer=SocialMediaTransform(),
        loader=CSVLoader("saida/df_limpo.csv"),
    )
    resultado = pipeline.run()
    Explorer().resumo_geral(resultado)


if __name__ == "__main__":
    main()