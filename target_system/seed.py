"""
Siembra propiedades en target_system con datos "legacy": existen de
antes, tienen codigo y direccion validos, pero los campos tecnicos
estan desactualizados o cargados con imprecision (simula una carga
manual vieja). El valor REAL de cada campo lo trae despues el
esquematico, derivado deterministicamente de estos datos (ver
pdf_creator.schema.derive_correct_values) — es lo que la automatizacion
va a aplicar sobre properties_db.xlsx.
"""
from __future__ import annotations

import random
import string
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db

_CALLES = [
    "Av. Rivadavia", "Av. Corrientes", "Av. San Martin", "Av. Belgrano",
    "Calle Mitre", "Calle Sarmiento", "Av. Libertador", "Calle Moreno",
]
_LOCALIDADES = [
    "San Isidro", "Moron", "Quilmes", "La Matanza", "Tigre",
    "Lomas de Zamora", "Vicente Lopez", "San Miguel",
]


def _codigo_unico(existentes: set[str]) -> str:
    while True:
        c = "".join(random.choices(string.digits, k=6))
        if c not in existentes:
            return c


def _direccion() -> str:
    return f"{random.choice(_CALLES)} {random.randint(100, 4999)}, {random.choice(_LOCALIDADES)}"


def _valor_legacy_erroneo(valor_tipico_min, valor_tipico_max, tipo):
    """Genera un valor 'legacy' para la propiedad: plausible (dentro del
    rango tipico, sin ceros absurdos) pero desactualizado — NUNCA el valor
    real, que despues deriva el esquematico con un ajuste deterministico
    por codigo (pdf_creator.schema.derive_correct_values)."""
    valor = random.uniform(valor_tipico_min, valor_tipico_max)
    return round(valor, 1) if tipo is float else int(valor)


def seed(count: int = 20, seed: int | None = None) -> int:
    if seed is not None:
        random.seed(seed)

    existentes = set(db.read_properties()["codigo"].astype(str)) if not db.read_properties().empty else set()
    registros = []
    for _ in range(count):
        codigo = _codigo_unico(existentes | {r["codigo"] for r in registros})
        registros.append({
            "codigo": codigo,
            "direccion": _direccion(),
            "superficie_m2": _valor_legacy_erroneo(120, 1400, float),
            "capacidad_personas": _valor_legacy_erroneo(15, 350, int),
            "plazas_estacionamiento": _valor_legacy_erroneo(0, 90, int),
            "anio_construccion": _valor_legacy_erroneo(1955, 2023, int),
            "salas": _valor_legacy_erroneo(2, 24, int),
            "esquematico_generado": False,
            "archivo_esquematico": "",
            "fuente": "carga manual (legacy)",
            "ultima_actualizacion": (date.today() - timedelta(days=random.randint(200, 1800))).strftime("%d/%m/%Y"),
        })

    db.append_properties(registros)
    return len(registros)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    n = seed(args.count, args.seed)
    print(f"Sembradas {n} propiedades en {db.PROPERTIES_XLSX}")
