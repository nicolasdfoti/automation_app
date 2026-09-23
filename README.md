# Automation Suite — Pipeline OCR (SIGE)

Dos sistemas FastAPI + React independientes que cooperan sobre `shared_store/` (el equivalente mock a una base de datos/API compartida) más un runtime compartido de utilidades en `common/`.

| Sistema | Backend | Frontend | Descripción |
| --- | --- | --- | --- |
| **`target_system/`** | FastAPI :8000 | Vite :5173 | SIGE: propiedades, dashboard, detalle y edición (GET/PUT de propiedades, stats). No conoce la existencia de Automation. |
| **`automation_system/`** | FastAPI :8001 | Vite :5174 | Pipeline OCR: esquemáticos, OCR, comparar, automatizar y la automatización por browser (Playwright sobre la UI de target). |
| **`shared_store/`** | — | — | Datos compartidos: `properties_db.xlsx`, `ground_truth.xlsx`, `ocr_output.xlsx`, `schematics/*.pdf`. Cada sistema lee/escribe estos archivos; ninguno importa código interno del otro. |
| **`common/`** | — | — | Utilidades neutrales (modelos, validación, excel, lock de escritura). |
| **`pdf_creator/`** | — | — | Genera el PDF del esquemático (ground truth). Runtime neutral consumido por Automation. |
| **`pipeline_app/`** | — | — | Prototipo Streamlit legacy del pipeline OCR. Su salida alimenta `ocr_output.xlsx`. |

**Regla arquitectónica central:** Automation **NO importa** `target_system.backend.*` (no clases, funciones ni excepciones del backend de target). Todo acceso a una propiedad de target se hace por HTTP contra la API de target (`GET http://127.0.0.1:8000/api/properties/{codigo}`) o contra la UI de target. El flujo Playwright no toca Excel como fallback: solo escribe a través de la UI real (`http://127.0.0.1:5173/propiedades/{codigo}`), que persiste via target.

---

## Diagrama de arquitectura

```
                         AUTOMATION SYSTEM                          TARGET SYSTEM
          +-------------------------------------+        +------------------------------+
          |  React UI (Vite :5174)              |        |  React UI (Vite :5173)        |
          |  /esquematicos /ocr /comparar       |        |  /propiedades/:codigo         |
          |  /automatizar                       |        |  / (dashboard)                |
          +-------------|-----------------------+        +-------------|----------------+
                        | http://127.0.0.1:8001                      | http://127.0.0.1:8000
          +-------------v-----------------------+        +-------------v----------------+
          |  Automation API (FastAPI :8001)     |        |  Target API (FastAPI :8000)   |
          |  /api/schematics  /api/ocr          |        |  /api/properties  /api/stats  |
          |  /api/compare    /api/automation    |        +-------------|----------------+
          |   (+ Playwright service)            |                      |
          |                                    |        shared_store/ (Excel) via common/
          |       Playwright abre Chromium y    |        +-------------------------------+
          |       edita la UI real de Target -- |------> | UI real de Target (:5173)      |
          |       (guarda por su formulario,    |        |  property-field-* + Guardar    |
          |        nunca escribe Excel directo) |        +-------------------------------+
          +-------------------------------------+

         pipeline_app/ (Streamlit, legacy) y pdf_creator/ (generador PDF)
         operan sobre shared_store/ respetando las reglas de propiedad.
```

---

## Stack tecnológico

| Capa | Tecnología |
| --- | --- |
| Backends | Python 3.11+ + FastAPI + Pydantic v2 |
| Frontends | React 18 + TypeScript + Vite |
| Datos | Archivos Excel reales en `shared_store/` (leer/escribir con `pandas` + `openpyxl`) |
| Lock | Lock por mutex (Windows `msvcrt`) entre procesos en `common/store_lock.py` |
| Automatización UI | Playwright (Python) sobre el navegador Chromium real de Target |
| Legacy | Streamlit (`pipeline_app/`) y generador de PDFs (`pdf_creator/`) |
| Pruebas | Scripts autocontenidos estilo pytest + builds de Vite (`tsc --noEmit` + `npm run build`) |

---

## Quick Start

### Prerrequisitos
- Windows 10/11 o WSL2 con interop Windows
- Python 3.11+
- Node.js 18+
- Playwright Chromium: `playwright install chromium`

### Instalación
```bash
git clone <repo>
cd automation_suite

# Python
python -m venv venv
venv/Scripts/pip install -r requirements.txt
playwright install chromium

# Frontends
cd target_system/frontend && npm install && cd ../..
cd automation_system/frontend && npm install && cd ../..

# Sembrar datos de demo (20 propiedades sintéticas)
venv/Scripts/python.exe target_system/seed.py --count 20
```

### Arranque (4 terminales)
```bash
# Terminal 1: Target API
venv/Scripts/python.exe -m uvicorn target_system.backend.main:app --port 8000

# Terminal 2: Target UI
cd target_system/frontend && npm run dev -- --port 5173

# Terminal 3: Automation API
venv/Scripts/python.exe -m uvicorn automation_system.backend.main:app --port 8001

# Terminal 4: Automation UI
cd automation_system/frontend && npm run dev -- --port 5174
```

### Uso
1. Abre **Automation UI**: http://127.0.0.1:5174
2. **Esquemáticos** → "Generar todos" (crea 20 PDFs + ground truth)
3. **OCR** → "Ejecutar OCR" (extrae texto de los PDFs con pdfplumber)
4. **Comparar** → ve exactitud por campo y diferencias por propiedad
5. **Automatizar** → "Automatizar todas" (abre Chromium, corrige cada propiedad en la UI real de Target, verifica persistencia)
6. Verifica en **Target UI**: http://127.0.0.1:5173/propiedades/{codigo} → `fuente = "automatizacion OCR"`

---

## Variables de entorno (Automation)

| Variable | Default | Descripción |
| --- | --- | --- |
| `TARGET_API_BASE_URL` | `http://127.0.0.1:8000` | Base de la API de target |
| `TARGET_UI_URL` | `http://127.0.0.1:5173` | Base de la UI de target para Playwright |
| `PLAYWRIGHT_HEADLESS` | `0` | `1` para headless (CI/test), `0` para browser visible |
| `PLAYWRIGHT_STEP_DELAY_MS` | `750` | Pausa visible entre pasos en modo headed; `0` desactiva |

> Nota: `PLAYWRIGHT_HEADLESS` se lee al importar el módulo. También puedes forzar por corrida con `"headless": true/false` en el body de la petición (`/api/automation/playwright` y `/api/automation/playwright/batch`).

---

## API Reference (resumen)

### Target System (`:8000`)
| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| GET | `/api/properties` | Listado con filtros (search, fuente, estado, superficie_min/max) |
| GET | `/api/properties/{codigo}` | Detalle de propiedad |
| PUT | `/api/properties/{codigo}` | Actualiza campos editables (direccion, 5 campos numéricos) |
| GET | `/api/stats` | KPIs del dashboard |

### Automation System (`:8001`, prefix `/api`)
| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| GET | `/api/schematics/pending` | Propiedades sin esquemático |
| GET | `/api/schematics/catalog` | Todas las propiedades + estado de esquemático |
| POST | `/api/schematics/generate` | Genera un esquemático (body: `SchematicGenerateRequest`) |
| POST | `/api/schematics/generate-all` | Genera todos los pendientes |
| GET | `/api/schematics/{codigo}/download` | Descarga PDF |
| POST | `/api/ocr/run` | Ejecuta pipeline OCR (`reprocesar_todo` query param) |
| GET | `/api/ocr/status` | Estado del OCR (pendientes/procesados) |
| GET | `/api/ocr/results` | Resultados OCR crudos |
| GET | `/api/compare` | Compara OCR vs Ground Truth (exactitud global, por campo, por propiedad) |
| GET | `/api/automation/preview` | Previsualiza correcciones pendientes (no modifica datos) |
| POST | `/api/automation/playwright` | Automatiza UNA propiedad por browser (body: `PlaywrightAutomationRequest`) |
| POST | `/api/automation/playwright/batch` | Automatiza VARIAS propiedades en UNA sesión de browser (body: `PlaywrightAutomationBatchRequest`) |

---

## Reglas de propiedad de datos (`shared_store/`)

| Archivo | Dueño | Escrito por |
| --- | --- | --- |
| `properties_db.xlsx` | Target System | Rutas de update de Target (`services/properties.py`) |
| `ground_truth.xlsx` | `pdf_creator/` | Generador de PDFs / alta de ground truth |
| `ocr_output.xlsx` | `pipeline_app/` | Pipeline OCR (Streamlit legacy o API) |
| `schematics/*.pdf` | `pdf_creator/` | Rutas `/api/schematics/generate*` |

---

## Tests

```bash
# Target (paridad contra docs/phase0_endpoint_baseline.json)
venv/Scripts/python.exe -m target_system.backend.tests.test_target_api

# Automation (lógica de correcciones + validaciones Playwright sin browser)
venv/Scripts/python.exe -m automation_system.backend.tests.test_automation
venv/Scripts/python.exe -m automation_system.backend.tests.test_playwright_validation

# Lock compartido
venv/Scripts/python.exe -m common.tests.test_store_lock

# Frontends (typecheck + build)
cd target_system/frontend    && npm run build && cd ../..
cd automation_system/frontend && npm run build && cd ../..
```

> Las suites que mutan `shared_store/` deben correr **secuencialmente** y restauran su snapshot interno; correrlas en paralelo causa contiendas de escritura sobre los mismos workbooks.

---

## Limitaciones conocidas

1. **Comparación UI rota**: La vista de comparación en Automation UI muestra "No pudimos cargar la comparación". Está documentada como limitación conocida y queda **fuera de alcance**; no se investiga ni modifica.
2. **Dependencia de runtime de Target**: El flujo Playwright exige Target UI (`:5173`), Target API (`:8000`) y Chromium instalado; no hay mock.
3. **Selectores acoplados a la UI de Target**: Los selectores (`#property-field-*`, "Guardar cambios", `[role='status']`) dependen del DOM del detalle; cambios en ese formulario requieren actualizarlos.
4. **`PLAYWRIGHT_HEADLESS` se lee al importar**: Cambiar el modo por entorno exige reiniciar el proceso; por eso se soporta override por request (`"headless": true|false`).
5. **Excel como almacén**: No hay transacciones, no hay índices, lock global serializa todas las escrituras. No escala.
6. **OCR mock**: Usa pdfplumber sobre PDFs con texto seleccionable (no Tesseract / OCR real de imágenes).
7. **Sin autenticación/autorización**: APIs abiertas, solo CORS restringido a orígenes de desarrollo.

---

## Integridad de datos (invariantes)

Los archivos de `shared_store/` son datos sintéticos autoridad. No se reseedean ni se "corrigen" quirks del OCR. Verificar por hash:

```bash
sha256sum shared_store/properties_db.xlsx shared_store/ground_truth.xlsx shared_store/ocr_output.xlsx
find shared_store/schematics -name '*.pdf' | wc -l   # 20
```

La discrepancia de validación se preserva a propósito: target exige `superficie_m2 > 0` al editar; automation acepta `>= 0` en sus límites de campo.

---

## Licencia

MIT (o la que correspondan) — este es un proyecto de portfolio/demo con datos 100% sintéticos.