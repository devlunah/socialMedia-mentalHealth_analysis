COLUNAS_ESPERADAS = [
    "participant_id",
    "age",
    "gender",
    "occupation",
    "region",
    "most_used_platform",
    "platforms_used_count",
    "daily_screen_hours",
    "daily_notifications",
    "night_time_use",
    "minutes_to_first_check_after_waking",
    "primary_purpose",
    "avg_sleep_hours",
    "anxiety_score_0to27",
    "low_mood_score_0to27",
    "life_satisfaction_1to10",
    "loneliness_1to10",
    "self_esteem_1to10",
    "fomo_1to10",
    "social_comparison_1to10",
    "physical_activity_days_per_week",
    "uses_screen_time_limits",
    "attempted_digital_detox",
    "seeks_mental_health_support",
    "wellbeing_band",
]

# Restrições da saída analítica, aplicadas após o tratamento.
COLUNAS_NAO_ANULAVEIS = {"participant_id"}
COLUNAS_UNICAS = {"participant_id"}

# Tipos pandas. Int64, Float64 e boolean aceitam pd.NA.
TIPOS_FINAIS = {
    "participant_id": "string",
    "age": "Int64",
    "gender": "string",
    "occupation": "string",
    "region": "string",
    "most_used_platform": "string",
    "platforms_used_count": "Int64",
    "daily_screen_hours": "Float64",
    "daily_notifications": "Int64",
    "night_time_use": "string",
    "minutes_to_first_check_after_waking": "Int64",
    "primary_purpose": "string",
    "avg_sleep_hours": "Float64",
    "anxiety_score_0to27": "Int64",
    "low_mood_score_0to27": "Int64",
    "life_satisfaction_1to10": "Int64",
    "loneliness_1to10": "Int64",
    "self_esteem_1to10": "Int64",
    "fomo_1to10": "Int64",
    "social_comparison_1to10": "Int64",
    "physical_activity_days_per_week": "Int64",
    "uses_screen_time_limits": "boolean",
    "attempted_digital_detox": "string",
    "seeks_mental_health_support": "string",
    "wellbeing_band": "string",
}

FAIXAS_ANALITICAS = {
    "age_band": (
        "age",
        (17, 24, 34, 44, 54),
        ("<18", "18–24", "25–34", "35–44", "45–54", "55+"),
    ),
    "notifications_band": (
        "daily_notifications",
        (25, 50, 100, 150),
        ("Até 25", "26–50", "51–100", "101–150", "Mais de 150"),
    ),
    "screen_hours_band": (
        "daily_screen_hours",
        (1, 2, 3, 4, 6),
        ("Até 1 h", ">1 até 2 h", ">2 até 3 h", ">3 até 4 h",
         ">4 até 6 h", "Mais de 6 h"),
    ),
    "first_check_band": (
        "minutes_to_first_check_after_waking",
        (5, 15, 30, 60),
        ("Até 5 min", "6–15 min", "16–30 min", "31–60 min", "Mais de 60 min"),
    ),
    "sleep_hours_band": (
        "avg_sleep_hours",
        (5, 6, 7, 8),
        ("Até 5 h", ">5 até 6 h", ">6 até 7 h", ">7 até 8 h", "Mais de 8 h"),
    ),
}

TIPOS_DERIVADOS = {}
for coluna in FAIXAS_ANALITICAS:
    TIPOS_DERIVADOS[coluna] = "string"
    TIPOS_DERIVADOS[f"{coluna}_order"] = "Int64"

COLUNAS_SAIDA = [*COLUNAS_ESPERADAS, *TIPOS_DERIVADOS]
TIPOS_SAIDA = {**TIPOS_FINAIS, **TIPOS_DERIVADOS}

# Limites inclusivos. None significa que não há máximo configurado.
FAIXAS = {
    "age": (0, 120),
    "platforms_used_count": (1, None),
    "daily_screen_hours": (0, 24),
    "daily_notifications": (0, None),
    "minutes_to_first_check_after_waking": (0, None),
    "avg_sleep_hours": (0, 24),
    "anxiety_score_0to27": (0, 27),
    "low_mood_score_0to27": (0, 27),
    "life_satisfaction_1to10": (1, 10),
    "loneliness_1to10": (1, 10),
    "self_esteem_1to10": (1, 10),
    "fomo_1to10": (1, 10),
    "social_comparison_1to10": (1, 10),
    "physical_activity_days_per_week": (0, 7),
}

# Marcadores textuais de ausência encontrados no CSV modificado.
# Aplique após strip() e casefold(). Células vazias também viram pd.NA.
MARCADORES_DE_AUSENCIA = {
    "occupation": {"-", "unknown"},
    "region": {"?",},
    "most_used_platform": {"sem info"},
    "daily_notifications": {"n/d"},
    "minutes_to_first_check_after_waking": {"sem resposta"},
}

# Chaves para consulta após strip() e casefold().
IDADES_POR_EXTENSO = {
    "twenty-five": 25,
    "thirty": 30,
    "thirty-five": 35,
    "forty": 40,
}

MAPA_BOOLEANOS = {
    "yes": True,
    "y": True,
    "true": True,
    "1": True,
    "no": False,
    "n": False,
    "false": False,
    "0": False,
}

# Cada mapa inclui os valores canônicos e as variantes observadas.
# Aplique strip() e casefold() antes da consulta.
ALIASES_CATEGORIAS = {
    "gender": {
        "f": "female",
        "m": "male",
    },
    "region": {
        "latam": "latin america",
        "n. america": "north america",
    },
    "most_used_platform": {
        "insta": "instagram",
        "twitter": "x/twitter",
        "yt": "youtube",
    },
    "attempted_digital_detox": {
        "yes,failed": "yes, failed",
    },
    "seeks_mental_health_support": {
        "considering": "considering it",
    },
    "wellbeing_band": {
        "at risk": "at-risk",
    },
}

ORDENS_CATEGORIAS = {
    "night_time_use": {
        "never": 1,
        "sometimes": 2,
        "often": 3,
        "every night": 4,
    },
    "wellbeing_band": {
        "good": 1,
        "moderate": 2,
        "at-risk": 3,
    },
}