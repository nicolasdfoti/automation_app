"""
generate_for_property(codigo): toma una propiedad que YA existe en
target_system (via shared_store), le arma valores tecnicos "correctos"
(el ground truth — a proposito puede ser distinto de lo que target_system
tiene cargado hoy, que es legacy/erroneo), dibuja el PDF, y marca la
propiedad como "con esquematico" en shared_store.

Esto es lo que garantiza el enganche: un PDF nunca se genera para un
codigo que no exista en el sistema.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_store import db

from . import pdf_builder, schema


def generate_for_property(codigo: str, overrides: dict | None = None) -> tuple[Path, dict]:
    propiedades = db.read_properties()
    fila = propiedades[propiedades["codigo"].astype(str) == str(codigo)]
    if fila.empty:
        raise ValueError(f"La propiedad {codigo} no existe en target_system — no se puede generar su esquematico.")
    fila = fila.iloc[0]

    valores = schema.build_numeric_values(overrides)
    record = {
        "codigo": str(codigo),
        "direccion": fila["direccion"],
        "fecha_relevamiento": schema.hoy(),
        **valores,
    }

    pdf_path = db.SCHEMATICS_DIR / f"{codigo}_mock.pdf"
    pdf_builder.render(record, pdf_path)
    db.append_ground_truth(record)
    db.update_property(codigo, {
        "esquematico_generado": True,
        "archivo_esquematico": pdf_path.name,
    })
    return pdf_path, record


def generate_for_all_pending() -> list[tuple[Path, dict]]:
    pendientes = db.propiedades_pendientes_de_esquematico()
    resultados = []
    for codigo in pendientes["codigo"].astype(str):
        resultados.append(generate_for_property(codigo))
    return resultados


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--codigo", type=str, default=None, help="Generar solo para este codigo")
    ap.add_argument("--todas-pendientes", action="store_true")
    args = ap.parse_args()

    if args.codigo:
        path, record = generate_for_property(args.codigo)
        print(f"Generado: {path}")
    elif args.todas_pendientes:
        resultados = generate_for_all_pending()
        print(f"Generados {len(resultados)} esquematicos pendientes")
    else:
        print("Pasa --codigo X o --todas-pendientes")
