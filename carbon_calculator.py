"""Parsing de lenguaje natural y cálculo ilustrativo de kg CO2e."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Factores de emisión (kg CO2e). Valores APROXIMADOS e ILUSTRATIVOS para el MVP.
# No son datos oficiales ni de un inventario certificado.
#
# Orden de magnitud inspirado en cifras públicas típicas (p. ej. DEFRA/BEIS,
# Our World in Data, estimaciones de porción/viaje). Sirven para demostrar
# el flujo de la app, no para reportes ambientales reales.
# ---------------------------------------------------------------------------

# Alimentación: kg CO2e por porción/comida detectada (no por kg de alimento).
MEAL_FACTORS: dict[str, dict] = {
    "carne": {
        "keywords": ("carne", "res", "vacuno", "bistec", "hamburguesa", "asado"),
        "label": "Comida con carne de res",
        "kg_co2": 6.5,
    },
    "cerdo": {
        "keywords": ("cerdo", "chuleta", "jamon", "jamón", "tocino"),
        "label": "Comida con cerdo",
        "kg_co2": 2.9,
    },
    "pollo": {
        "keywords": ("pollo", "ave", "nuggets"),
        "label": "Comida con pollo",
        "kg_co2": 1.6,
    },
    "pescado": {
        "keywords": ("pescado", "atun", "atún", "salmon", "salmón", "mariscos"),
        "label": "Comida con pescado/mariscos",
        "kg_co2": 1.8,
    },
    "lacteos": {
        "keywords": ("queso", "leche", "yogur", "yogurt", "mantequilla"),
        "label": "Lácteos",
        "kg_co2": 1.3,
    },
    "vegetariana": {
        "keywords": ("ensalada", "vegetariano", "vegano", "verduras", "legumbres"),
        "label": "Comida vegetariana/ensalada",
        "kg_co2": 0.5,
    },
}

# Transporte: kg CO2e por kilómetro recorrido (ocupación media típica).
TRANSPORT_FACTORS: dict[str, dict] = {
    "avion": {
        "keywords": ("avion", "avión", "vuelo", "aereo", "aéreo"),
        "label": "Avión",
        "kg_co2_per_km": 0.255,
        "default_km": 500.0,
    },
    "auto": {
        "keywords": ("auto", "coche", "carro", "automovil", "automóvil", "taxi", "uber"),
        "label": "Auto / taxi",
        "kg_co2_per_km": 0.192,
        "default_km": 10.0,
    },
    "moto": {
        "keywords": ("moto", "motocicleta"),
        "label": "Motocicleta",
        "kg_co2_per_km": 0.103,
        "default_km": 10.0,
    },
    "bus": {
        "keywords": ("bus", "autobus", "autobús", "colectivo", "camion", "camión"),
        "label": "Bus",
        "kg_co2_per_km": 0.089,
        "default_km": 10.0,
    },
    "tren": {
        "keywords": ("tren", "metro", "subte", "ferrocarril", "tranvia", "tranvía"),
        "label": "Tren / metro",
        "kg_co2_per_km": 0.041,
        "default_km": 10.0,
    },
    "bici": {
        "keywords": ("bici", "bicicleta", "cicla"),
        "label": "Bicicleta",
        "kg_co2_per_km": 0.0,
        "default_km": 5.0,
    },
    "caminar": {
        "keywords": ("a pie", "caminando", "caminata", "camine", "caminé"),
        "label": "Caminar",
        "kg_co2_per_km": 0.0,
        "default_km": 2.0,
    },
}

# Energía / hogar: kg CO2e por evento o por hora, según el caso.
ENERGY_FACTORS: dict[str, dict] = {
    "ducha": {
        "keywords": ("ducha", "ducharme", "bañe", "bañé"),
        "label": "Ducha con agua caliente",
        "kg_co2": 0.7,
        "per_hour": False,
    },
    "lavadora": {
        "keywords": ("lavadora", "lavar la ropa", "lavé la ropa", "lave la ropa"),
        "label": "Ciclo de lavadora",
        "kg_co2": 0.6,
        "per_hour": False,
    },
    "ac": {
        "keywords": ("aire acondicionado", "a/c", "climatizacion", "climatización"),
        "label": "Aire acondicionado",
        "kg_co2": 1.2,  # por hora
        "per_hour": True,
        "default_hours": 2.0,
    },
    "calefaccion": {
        "keywords": ("calefaccion", "calefacción", "estufa", "calefactor"),
        "label": "Calefacción",
        "kg_co2": 1.5,  # por hora
        "per_hour": True,
        "default_hours": 2.0,
    },
}


@dataclass
class DetectedActivity:
    """Una actividad reconocida en el texto del usuario."""

    label: str
    category: str
    quantity: float
    unit: str
    kg_co2: float
    note: str = ""


@dataclass
class CalculationResult:
    """Resultado del análisis de un registro diario."""

    original_text: str
    activities: list[DetectedActivity] = field(default_factory=list)
    unrecognized: bool = False

    @property
    def total_kg_co2(self) -> float:
        return round(sum(a.kg_co2 for a in self.activities), 2)


def _normalize(text: str) -> str:
    """Minúsculas y sin tildes para comparar palabras clave."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _extract_distances_km(text: str) -> list[float]:
    """Números seguidos de km, p. ej. '20km' o '15,5 km'."""
    matches = re.findall(r"(\d+(?:[.,]\d+)?)\s*km", text, flags=re.IGNORECASE)
    return [float(m.replace(",", ".")) for m in matches]


def _extract_hours(text: str) -> list[float]:
    """Números seguidos de hora(s), p. ej. '3 horas'."""
    matches = re.findall(
        r"(\d+(?:[.,]\d+)?)\s*(?:h|hs|hora|horas)\b",
        text,
        flags=re.IGNORECASE,
    )
    return [float(m.replace(",", ".")) for m in matches]


def _contains_any(normalized_text: str, keywords: tuple[str, ...]) -> bool:
    return any(_normalize(kw) in normalized_text for kw in keywords)


def parse_activities(text: str) -> CalculationResult:
    """
    Extrae actividades por palabras clave y estima kg CO2e.

    Si hay un solo valor de km, se aplica a cada medio de transporte detectado.
    Si hay varios, se emparejan en el orden en que aparecen los medios.
    """
    if not text or not text.strip():
        return CalculationResult(original_text=text or "", unrecognized=True)

    normalized = _normalize(text)
    km_values = _extract_distances_km(text)
    hour_values = _extract_hours(text)
    activities: list[DetectedActivity] = []

    # Transporte (prioridad: el primer match de cada modo).
    transport_hits: list[tuple[str, dict]] = []
    for key, spec in TRANSPORT_FACTORS.items():
        if _contains_any(normalized, spec["keywords"]):
            transport_hits.append((key, spec))

    for index, (_key, spec) in enumerate(transport_hits):
        if len(km_values) == 1:
            km = km_values[0]
            note = f"{km:g} km"
        elif index < len(km_values):
            km = km_values[index]
            note = f"{km:g} km"
        elif km_values:
            km = km_values[-1]
            note = f"{km:g} km (distancia reutilizada)"
        else:
            km = float(spec["default_km"])
            note = f"sin km: se asumen {km:g} km"

        kg = round(km * float(spec["kg_co2_per_km"]), 2)
        activities.append(
            DetectedActivity(
                label=spec["label"],
                category="transporte",
                quantity=km,
                unit="km",
                kg_co2=kg,
                note=note,
            )
        )

    # Alimentación: una porción por tipo detectado.
    for spec in MEAL_FACTORS.values():
        if _contains_any(normalized, spec["keywords"]):
            activities.append(
                DetectedActivity(
                    label=spec["label"],
                    category="alimentación",
                    quantity=1,
                    unit="porción",
                    kg_co2=float(spec["kg_co2"]),
                    note="1 porción estimada",
                )
            )

    # Energía / hogar.
    energy_index = 0
    for spec in ENERGY_FACTORS.values():
        if not _contains_any(normalized, spec["keywords"]):
            continue
        if spec.get("per_hour"):
            if len(hour_values) == 1:
                hours = hour_values[0]
                note = f"{hours:g} h"
            elif energy_index < len(hour_values):
                hours = hour_values[energy_index]
                note = f"{hours:g} h"
            else:
                hours = float(spec["default_hours"])
                note = f"sin horas: se asumen {hours:g} h"
            kg = round(hours * float(spec["kg_co2"]), 2)
            activities.append(
                DetectedActivity(
                    label=spec["label"],
                    category="energía",
                    quantity=hours,
                    unit="h",
                    kg_co2=kg,
                    note=note,
                )
            )
            energy_index += 1
        else:
            activities.append(
                DetectedActivity(
                    label=spec["label"],
                    category="energía",
                    quantity=1,
                    unit="evento",
                    kg_co2=float(spec["kg_co2"]),
                    note="1 uso estimado",
                )
            )

    unrecognized = len(activities) == 0
    return CalculationResult(
        original_text=text.strip(),
        activities=activities,
        unrecognized=unrecognized,
    )
