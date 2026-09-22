# PROJECT OVERVIEW

## 1. Descripción general

Plataforma de gestión inmobiliaria separada en **dos sistemas FastAPI + React**
que comparten un almacén de Excel (`shared_store/`):

- **Target System** — CRUD de propiedades, estadísticas y detalle por código;
  dueño de `properties_db.xlsx`.
- **Automation System** — pipeline OCR sobre planos (`pdf_creator`),
  generación de esquemáticos, comparación de datos vs. OCR y la automatización
  de correcciones (cálculo + aplicación por browser con Playwright sobre la UI
  real de Target, sin escritura directa de Excel).

Ambos comparten la capa `common/` (lectura/escritura de Excel, modelo de
propiedades, validaciones y lock de escritura entre procesos) y el almacén
`shared_store/` con reglas claras de propiedad de cada archivo.

## 2. Stack tecnológico

| Capa | Tecnología |
| --- | --- |
| Backends | Python 3.x + FastAPI + Pydantic v2 |
| Frontends | React 18 + TypeScript + Vite |
| Datos | Archivos Excel reales en `shared_store/` (leer/escribir con `pandas` + `openpyxl`) |
| Lock | Lock por mutex (Windows `msvcrt`) entre procesos en `common/store_lock.py` |
| Automatización UI | Playwright (Python) sobre el navegador Chromium real de Target |
| Legacy | Streamlit (`pipeline_app/`) y generador de PDFs (`pdf_creator/`) |
| Pruebas | `pytest`-style scripts autocontenidos + builds de Vite (`tsc --noEmit` + `npm run build`) |

## 3. Arquitectura

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

## 4. Estructura del repositorio

```
automation_app/
├── README.md
├── PROJECT_OVERVIEW.md          # este documento
├── requirements.txt
├── venv/                        # python venv (Windows)
├── common/                      # capa compartida
│   ├── excel.py                 # lectura/escritura de workbooks
│   ├── models.py                # modelo de propiedades y campos
│   ├── store_lock.py            # lock entre procesos
│   ├── validation.py            # validaciones de campos
│   └── tests/test_store_lock.py
├── shared_store/                # DATA: Excel reales + PDFs
│   ├── db.py                    # API de datos (read/write workbooks)
│   ├── properties_db.xlsx       # dueño: target
│   ├── ground_truth.xlsx        # dueño: pdf_creator
│   ├── ocr_output.xlsx          # dueño: pipeline_app
│   └── schematics/              # PDFs generados
├── target_system/
│   ├── backend/                 # FastAPI :8000 (main.py, deps.py, schemas.py,
│   │                            #  routers/{properties,stats}.py,
│   │                            #  services/{properties,dashboard}.py, tests/)
│   └── frontend/                # React :5173 (src/App.tsx, pages/)
├── automation_system/
│   ├── backend/                 # FastAPI :8001
│   │   ├── main.py              # monta /api/schematics, /api/ocr, /api/compare, /api/automation
│   │   ├── deps.py              # write_lock del store
│   │   ├── schemas.py           # contratos automation + Playwright
│   │   ├── routers/             # schematics.py ocr.py compare.py automation.py
│   │   ├── services/            # schematics.py ocr.py compare.py target_api.py
│   │   │                        #  automation.py playwright_automation.py compare_api.py
│   │   └── tests/               # test_automation.py test_playwright_validation.py
│   └── frontend/                # React :5174
├── pipeline_app/                # legacy Streamlit (OCR)
├── pdf_creator/                 # generador de PDFs (esquematicos/ground truth)
└── docs/phase0_endpoint_baseline.json   # contrato historico (fixture de tests)
```

## 5. Sistema Target (`target_system/`)

Backend FastAPI en `:8000` (main.py con CORS solo para `localhost/127.0.0.1:5173`)
y frontend React/Vite en `:5173`.

- **Rutas del frontend**: `/` (dashboard), `/propiedades` (listado),
  `/propiedades/:codigo` (detalle con campos editables).
- **API**: `GET /api/health`, `GET /api/properties` (listado),
  `GET /api/properties/{codigo}` (detalle), `GET /api/stats`.
- **Servicios**: `services/properties.py` (CRUD sobre `shared_store` vía
  `common/excel.py` y `shared_store/db.py`) y `services/dashboard.py` (stats).
- **Ownership**: Target es el único dueño de `properties_db.xlsx`.
- `target_system/backend/tests/test_target_api.py` valida paridad de contrato
  contra `docs/phase0_endpoint_baseline.json`.

## 6. Sistema Automation (`automation_system/`)

Backend FastAPI en `:8001` (CORS solo para `localhost/127.0.0.1:5174`) y
frontend React/Vite en `:5174`.

- **Rutas del frontend**: `/esquematicos`, `/ocr`, `/comparar`, `/automatizar`.
- **API** (prefix `/api`): `/health`,
  - `/schematics/pending`, `/schematics/catalog`, `/schematics/generate`,
    `/schematics/generate-all`, `/schematics/{codigo}/download`
  - `/ocr/run`, `/ocr/status`, `/ocr/results`
  - `/compare`
  - `/automation/preview`, `/automation/apply`,
    `/automation/playwright`, `/automation/playwright/batch`
- **Servicios**:
  - `schematics.py`, `ocr.py`, `compare.py` (+ `compare_api.py`): pipeline.
  - `automation.py`: cálculo de correcciones pendientes, campos
    automatizables (`FIELD_LABELS`, `FIELD_BOUNDS`), builds de cambios,
    formateo de valores y preview/apply.
  - `playwright_automation.py`: automatización por browser (sección 12).
  - `target_api.py`: proxy de lectura del Target API (`:8000`) para el
    frontend de automation.
- Respecta las reglas de ownership: la corrección de datos en el flujo real se
  hace escribiendo a `shared_store` solo en `/automation/apply` legacy; el
  flujo Playwright **nunca** escribe Excel, edita la UI de Target.

## 7. Capa común (`common/`)

Código compartido por ambos sistemas — sin lógica de negocio de ninguno:

- `excel.py`: lectura/escritura de workbooks pandas/openpyxl.
- `models.py`: modelo de propiedades/campos y normalización.
- `validation.py`: validación de valores/campos.
- `store_lock.py`: **lock entre procesos** (mutex) que serializa la escritura
  de los Excel incluso con varios backends corriendo.
- `tests/test_store_lock.py`: pruebas del lock.

Los `deps.py` de ambos backends exponen `write_lock` para decorar las rutas que
escriben, dejando la capa de datos (`shared_store/db.py`) sin acoplar al lock.

## 8. Datos compartidos y propiedad (`shared_store/`)

| Archivo | Dueño | Escrito por |
| --- | --- | --- |
| `properties_db.xlsx` | Target System | Rutas de update de Target (`services/properties.py`) |
| `ground_truth.xlsx` | `pdf_creator/` | Generador de PDFs / alta de ground truth |
| `ocr_output.xlsx` | `pipeline_app/` | Pipeline OCR (Streamlit legacy) |
| `schematics/` (PDFs) | `pdf_creator/` | Rutas `/api/schematics/generate*` |

API de datos en `shared_store/db.py`: `read_properties`, `write_properties`,
`append_properties`, `update_property`, `propiedades_pendientes_de_esquematico`,
`append_ground_truth`, `upsert_ground_truth`, `read_ground_truth`,
`read_ocr_output`.

## 9. Aplicaciones legacy

- **`pipeline_app/`**: prototipo Streamlit del pipeline OCR (análisis de
  planos). Su salida alimenta `ocr_output.xlsx`. Es **legacy**: la UI moderna
  es Automation (`:5174`, página `/ocr`).
- **`pdf_creator/`**: generador de esquemáticos/PDFs y ground truth. Usa
  `ground_truth.xlsx` y los PDFs de `shared_store/schematics/`. Se invoca
  desde Automation via `/api/schematics/*` (`app_pdf_creator.py`,
  `generator.py`, `pdf_builder.py`, `schema.py`).

## 10. API — rutas existentes

**Target (`:8000`)**
```
GET /api/health
GET /api/properties
GET /api/properties/{codigo}
GET /api/stats
```

**Automation (`:8001`, prefix `/api`)**
```
GET  /api/health
GET  /api/schematics/pending
GET  /api/schematics/catalog
POST /api/schematics/generate
POST /api/schematics/generate-all
GET  /api/schematics/{codigo}/download
POST /api/ocr/run
GET  /api/ocr/status
GET  /api/ocr/results
GET  /api/compare
GET  /api/automation/preview
POST /api/automation/apply
POST /api/automation/playwright
POST /api/automation/playwright/batch
```

## 11. Flujo de negocio E2E

1. **Esquematicos**: Automation pega los planos vía `/api/schematics/generate`,
   `pdf_creator` produce los PDFs y actualiza `ground_truth.xlsx`.
2. **OCR**: el pipeline analiza planos y escribe `ocr_output.xlsx`
   (`/api/ocr/run`, `/api/ocr/status`, `/api/ocr/results`).
3. **Comparar**: `/api/compare` cruza la data registrada vs. OCR y detecta
   discrepancias.
4. **Automatizar**:
   - `/api/automation/preview` → lista de correcciones pendientes (antes/esperado).
   - `/api/automation/apply` → escribe en `shared_store` (flujo legacy).
   - `/api/automation/playwright` y `/api/automation/playwright/batch` →
     **flujo por browser**: Chrome real edita y guarda en la UI de Target
     (persistencia en `properties_db.xlsx` a través de Target).
5. **Verificación**: playwrite recarga el detalle y verifica el valor escrito;
   el usuario puede consultar Target (`/propiedades/:codigo`) y rediseñar
   su dashboard (`/api/stats`).

## 12. Arquitectura de automatización por browser (Playwright)

Implementada en `automation_system/backend/services/playwright_automation.py`.
Trata a Target como sistema **externo**: solo interactúa con su UI.

- **Ciclo de vida persistente**: para toda una corrida se abre **una sola
  instancia de Chromium** (`browser_start`), se crea un único contexto y una
  única página que se **reutiliza** para corregir varias propiedades y campos;
  si una corrección falla se recrea esa página (mismo navegador) y la corrida
  continúa; al terminar se cierra **una sola vez** (`browser_close`, en
  `finally`).
- **Rutas**: `POST /api/automation/playwright` (una propiedad) y
  `POST /api/automation/playwright/batch` (varias propiedades en una corrida).
  Solo se aceptan códigos (+ `field` opcional); el valor que escribe el browser
  **siempre** se recalcula en el servidor a partir de los archivos (nunca se
  confía en el request; sin fallback a Excel directo).
- **Por propiedad**: navegar (`domcontentloaded`, timeout de navegación 30 s) →
  leer valor actual → escribir en `#property-field-superficie|capacidad|
  estacionamiento|anio|salas` → clic en "Guardar cambios" → esperar
  `[role='status']` con "Cambios guardados correctamente" → recargar → verificar
  lectura (tolerancia 1e-9). El resultado por campo incluye
  `field/before/after/verified`; los `steps` documentan el recorrido.
- **Esperas**: mecanismos reales de Playwright (`wait_for_selector`,
  `locator.fill`, espera del toast); sin `sleep` arbitrarios largos.
- **Modos de ejecución**:
  - `headless=False` (default demo/visible): ventana visible y pausas cortas
    entre pasos (`PLAYWRIGHT_STEP_DELAY_MS`, default 750 ms) para continuidad
    visible.
  - `headless=True` (modo rápido): sin ventana y **sin** pausas visibles.
  - Se controla con `PLAYWRIGHT_HEADLESS` (leída al importar el módulo) o por
    corrida con `"headless": true|false` en el JSON del request (recomendado al
    correr la API desde WSL, donde las variables de entorno no cruzan a los
    procesos Windows de forma automática).
- **Endpoints por API** (ejemplos en `README.md`):
  `{"codigo":"877597"}`, `{"codigo":"877597","field":"superficie_m2"}`,
  `{"codigos":["877597","638412"]}`, `{"codigos":[...],"headless":true}`.
- **Resultados**: propiedades sin correcciones pendientes → `no_change`
  (sin abrir navegador); códigos inexistentes → 404; campo no automatizable →
  422.

## 13. Pruebas

Scripts autocontenidos (sin pytest framework) + builds de frontend:

```bash
# Backend Target (paridad contra docs/phase0_endpoint_baseline.json)
./venv/Scripts/python.exe -m target_system.backend.tests.test_target_api

# Backend Automation (logica + contratos de preview/apply + Playwright sin browser)
./venv/Scripts/python.exe -m automation_system.backend.tests.test_automation
./venv/Scripts/python.exe -m automation_system.backend.tests.test_playwright_validation

# Capa comun (lock entre procesos)
./venv/Scripts/python.exe -m common.tests.test_store_lock

# Frontends (typecheck + build)
npx tsc --noEmit   # en target_system/frontend y automation_system/frontend
npm run build      # idem (Vite)
```

> Las suites que mutan `shared_store/` deben correr **secuencialmente** y
> restauran su snapshot interno; correrlas en paralelo causa contiendas de
> escritura sobre los mismos workbooks.

E2E por browser real: se levanta la UI de Target (`:5173`) + ambos backends,
se fuerza un valor desactualizado en una propiedad, se dispara
`/api/automation/playwright/batch` y se comprueba `browser_start=1`,
`browser_close=1` y `verified=true` por campo (also headless con 0 pausas).

## 14. Puertos y desarrollo local

| Servicio | Puerto | Comando |
| --- | --- | --- |
| Target API | `8000` | `./venv/Scripts/python.exe -m uvicorn target_system.backend.main:app --port 8000` |
| Target UI | `5173` | `cd target_system/frontend && npm run dev -- --port 5173` |
| Automation API | `8001` | `./venv/Scripts/python.exe -m uvicorn automation_system.backend.main:app --port 8001` |
| Automation UI | `5174` | `cd automation_system/frontend && npm run dev -- --port 5174` |

Notas:
- Backends requieren la UI de Target levantada para el flujo Playwright.
- Desde WSL, los procesos (uvicorn/Vite) corren como **Windows**; probe directo
  solo con `urllib` (no `curl` WSL), y limpieza de puertos con `netstat`/
  `taskkill`.
- El lock de `common/store_lock.py` evita escrituras concurrentes sobre los
  Excel entre ambos backends.

## 15. Archivos importantes

| Ruta | Por qué |
| --- | --- |
| `shared_store/db.py` | API de datos sobre los Excel (sin negocio) |
| `shared_store/*.xlsx` (3) | Datos reales; ownership por sistema |
| `common/store_lock.py` | Lock entre procesos para escrituras |
| `common/excel.py`, `common/models.py`, `common/validation.py` | Capa común |
| `target_system/backend/services/properties.py` | CRUD/property updates (único escritor de `properties_db`) |
| `automation_system/backend/services/automation.py` | Cálculo de correcciones, campos y preview |
| `automation_system/backend/services/playwright_automation.py` | Automatización por browser (ciclo de vida persistente) |
| `automation_system/backend/schemas.py` | Contratos automation + Playwright (incl. batch) |
| `automation_system/backend/routers/automation.py` | `preview`, `apply`, `playwright`, `playwright/batch` |
| `docs/phase0_endpoint_baseline.json` | Contrato histórico de endpoints (fixture de tests) |

## 16. Integridad de datos

- **Lock entre procesos**: todas las rutas escritoras de ambos backends se
  decoran con `write_lock` (`deps.py`) → serialización de escritura de
  workbooks a través de procesos.
- **Lógica de negocio en el servicio, no en el request**: Playwright solo
  recibe códigos; los valores se recomputan desde los archivos y se validan
  contra campos y boundarios conocidas antes de escribir.
- **Verificación post-guardado**: tras salvar en la UI, el navegador recarga el
  detalle y confirma que el valor persistido coincide (tolerancia 1e-9).
- **Snapshots en tests/E2E**: las suites y el harness E2E toman snapshot de
  `shared_store`, mutan y restauran antes de terminar.
- **API de datos única**: nada escribe Excel directo por fuera de
  `shared_store/db.py` + `common/excel.py`.

## 17. Limitaciones conocidas

- **Comparación ("No pudimos cargar la comparación")**: la vista de
  comparación presenta actualmente el error "No pudimos cargar la comparación".
  Está documentada como limitación conocida y queda **fuera de alcance** en las
  tareas de automatización: no se investiga ni modifica (ver README).
- **Dependencia de runtime de Target**: el flujo Playwright exige Target UI
  (`:5173`), Target API (`:8000`) y un Chromium instalado; no hay mock.
- **Selectores acoplados a la UI de Target**: los selectores
  (`#property-field-*`, "Guardar cambios", `[role='status']`) dependen del DOM
  del detalle; cambios en ese formulario requieren actualizarlos.
- **`PLAYWRIGHT_HEADLESS` se lee al importar** del módulo: cambiar el modo por
  entorno exige reiniciar el proceso; por eso se soporta el override por
  request (`"headless": true|false`).
- **Después de todo**: no se conoce ninguna otra limitación fuera de este
  documento; cargar la comparación es la única área rota conocida y excluida.

## 18. Decisiones de arquitectura

- Documentadas en detalle en `README.md` (sección "Decisiones de arquitectura").
  Resumen: dos sistemas acoplados por un almacén Excel compartido y una capa
  común; ni Target ni Automation dependen de legacy; Automation escribe en
  Target solo vía su API o la UI real (Playwright), nunca Excel directo; el
  lock entre procesos protege las escrituras; Playwright usa un **ciclo de vida
  persistente** (un solo browser por corrida) con esperas reales en lugar de
  sleeps largos, y soporta modo visible (demo) y headless (rápido).