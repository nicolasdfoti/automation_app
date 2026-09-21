# Automation Suite — Demo (datos 100% sinteticos)

Tres sistemas separados que se integran a traves de `shared_store/`
(el equivalente mock a una base de datos/API compartida):

- **`target_system/`** — "SIGE", el sistema que ya tiene las propiedades
  cargadas, con datos tecnicos legacy (a veces erroneos, a veces en 0).
  Multipage: `Home.py` (KPIs generales + actividad reciente con
  auto-refresco), `pages/1_Propiedades.py` (listado filtrable) y
  `pages/2_Detalle_Propiedad.py` (ficha por propiedad, con descarga del
  esquematico si ya lo tiene).
  `streamlit run target_system/Home.py`

- **`pdf_creator/`** — genera el PDF del esquematico para una propiedad
  que YA existe en SIGE (nunca inventa codigos sueltos). El valor que
  dibuja es el "dato correcto" (ground truth), que puede diferir del
  legacy que tiene cargado el sistema.
  `streamlit run pdf_creator/app_pdf_creator.py`

- **`pipeline_app/`** — OCR sobre los PDFs generados, validator (OCR vs ground truth)
  y automatizacion (corrige SIGE con lo que extrajo el OCR).
  `streamlit run pipeline_app/Home.py`

## Primer uso

```bash
pip install -r requirements.txt

# 1) sembrar SIGE con propiedades legacy
python target_system/seed.py --count 20

# 2) generar los esquematicos pendientes
python -c "from pdf_creator import generator; generator.generate_for_all_pending()"

# 3) correr el OCR, comparar y automatizar
cd pipeline_app && python -m ocr.pipeline_mock --workers 4
streamlit run Home.py   # Correr OCR (si no se corrio por CLI) -> Comparar -> Automatizar
```

O hacer los pasos 1 y 2 desde las interfaces de `target_system` y
`pdf_creator` en vez de la consola.
