"""Historial local de registros diarios en CSV."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from carbon_calculator import CalculationResult

DATA_DIR = Path(__file__).resolve().parent / "data"
HISTORY_FILE = DATA_DIR / "historial.csv"
COLUMNS = ["fecha", "hora", "texto", "total_kg_co2", "desglose"]


def _ensure_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        with HISTORY_FILE.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNS)


def save_entry(result: CalculationResult) -> None:
    """Añade un registro con fecha/hora local."""
    _ensure_file()
    now = datetime.now()
    breakdown = [
        {
            "label": a.label,
            "category": a.category,
            "quantity": a.quantity,
            "unit": a.unit,
            "kg_co2": a.kg_co2,
            "note": a.note,
        }
        for a in result.activities
    ]
    with HISTORY_FILE.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(
            [
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                result.original_text,
                f"{result.total_kg_co2:.2f}",
                json.dumps(breakdown, ensure_ascii=False),
            ]
        )


def load_history() -> pd.DataFrame:
    """Devuelve el historial; vacío si aún no hay registros."""
    _ensure_file()
    df = pd.read_csv(HISTORY_FILE)
    if df.empty:
        return df
    df["total_kg_co2"] = pd.to_numeric(df["total_kg_co2"], errors="coerce")
    return df


def daily_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Suma kg CO2e por día para el gráfico de evolución."""
    if df.empty:
        return pd.DataFrame(columns=["fecha", "kg CO2e"])
    grouped = (
        df.groupby("fecha", as_index=False)["total_kg_co2"]
        .sum()
        .rename(columns={"total_kg_co2": "kg CO2e"})
        .sort_values("fecha")
    )
    return grouped
