# Automation Suite — Pipeline OCR (SIGE)

Dos sistemas de software independientes que cooperan sobre `shared_store/`
(el equivalente mock a una base de datos/API compartida) mas un runtime
compartido de utilidades:

| Sistema | Backend | Frontend | Descripcion |
| --- | --- | --- | --- |
| **`target_system/`** | FastAPI :8000 | Vite :5173 | "SIGE": propiedades, dashboard, detalle y edicion (GET/PUT de propiedades, stats). No conoce la existencia de Automation. |
| **`automation_system/`** | FastAPI :8001 | Vite :5174 | Pipeline OCR: esquematicos, OCR, comparar, automatizar y la automatizacion por browser (Playwright sobre la UI de target). |
| **`shared_store/`** | — | — | Datos compartidos: `properties_db.xlsx`, `ground_truth.xlsx`, `ocr_output.xlsx`, `schematics/*.pdf`. Cada sistema lee/escribe estos archivos; ninguno importa codigo interno del otro. |
| **`common/`** | — | — | Utilidades neutrales (modelos, validacion, excel, lock de escritura). |
| **`pdf_creator/`** | — | — | Genera el PDF del esquematico (ground truth). Runtime neutral consumido por Automation. |
| **`pipeline_app/`**, `mock_external_system/`, `backend/` (parcial) | — | — | Runtimes legacy / POC protegido sin commit (ver §3 y §7). |

Regla arquitectonica central: **Automation NO importa `target_system.backend.*`**
(no clases, funciones ni excepciones del backend de target). Todo acceso a una
propiedad de target se hace por HTTP contra la API de target
(`GET http://127.0.0.1:8000/api/properties/{codigo}`) o contra la UI de target.
El flujo Playwright no toca Excel como fallback: solo escribe a traves de la UI
real (`http://127.0.0.1:5173/propiedades/{codigo}`), que persiste via target.

## Puertos y arranque

```bash
pip install -r requirements.txt
python target_system/seed.py --count 20

# ---- Target System ----
uvicorn target_system.backend.main:app --host 127.0.0.1 --port 8000
# frontend (Vite dev, puerto fijo 5173):
cd target_system/frontend && npm run dev

# ---- Automation System ----
uvicorn automation_system.backend.main:app --host 127.0.0.1 --port 8001
# frontend (Vite dev, puerto fijo 5174):
cd automation_system/frontend && npm run dev
```

Variables de entorno (Automation):

- `TARGET_API_BASE_URL` — base de la API de target (default `http://127.0.0.1:8000`).
- `TARGET_UI_URL` — base de la UI de target para Playwright (default `http://127.0.0.1:5173`).
- `PLAYWRIGHT_HEADLESS` — `1` para headless, `0` (default) para browser visible.

Playwright (Automatizar > unica correccion, propiedad `550482` campo `superficie_m2`):
requiere la UI de target arriba (`5173`) y su backend (`8000`), ademas del
backend de automation (`8001`):

```bash
curl -X POST http://127.0.0.1:8001/api/automation/playwright \
  -H 'Content-Type: application/json' \
  -d '{"codigo":"550482","field":"superficie_m2"}'
```

## Tests

```bash
# Target (paridad contra docs/phase0_endpoint_baseline.json)
venv/Scripts/python.exe -m target_system.backend.tests.test_target_api

# Automation (logica de correcciones + validaciones de Playwright sin browser)
venv/Scripts/python.exe -m automation_system.backend.tests.test_automation
venv/Scripts/python.exe -m automation_system.backend.tests.test_playwright_validation

# Lock de escritura compartido
venv/Scripts/python.exe -m common.tests.test_store_lock

# Frontends (typecheck + build)
venv/Scripts/python.exe -m pip install -q -r requirements.txt 2>/dev/null; \
cd target_system/frontend    && npm run build && cd ../..; \
cd automation_system/frontend && npm run build && cd ../..
```

## Integridad de datos (invariantes)

Los archivos de `shared_store/` son datos sinteticos autoridad. No se reseedean
ni se "corrigen" quirks del OCR. Verificar por hash (ejemplos conocidos):

```bash
sha256sum shared_store/properties_db.xlsx shared_store/ground_truth.xlsx shared_store/ocr_output.xlsx
find shared_store/schematics -name '*.pdf' | wc -l   # 20
```

La discrepancia de validacion se preserva a proposito: target exige
`superficie_m2 > 0` al editar; automation acepta `>= 0` en sus limites de campo.

---

<a id="final-report"/>

# §1 Background
## Informe de estado — sistema

El portfolio migra de una suite monolitica (un backend FastAPI :8000, un
frontend Vite :5173, redireccion de imports a `target_system`) hacia una
arquitectura con **dos sistemas independientes y ejecutables por separado**:
Target (portador de datos, sin conocimiento del pipeline OCR) y Automation
(consumidor que solo accede a target por HTTP/UI). La migracion se entrega en
una unica operacion con un unico commit, preservando la integridad de los datos
y las 7 pruebas del POC de Playwright.

# §2 Objectives
## Objetivos

Completar la separacion Target/Automation en UNA operacion, con UN commit,
cumpliendo: (1) Automation sin imports a `target_system.backend.*`; (2) el
`automation_system/` como app independiente (:8001/:5174) sin routers de
propiedades/stats; (3) Target intacto (:8000/:5173) y sin conocimiento de
Automation; (4) sin duplicar logica de negocio; (5) Playwright retargeteado a
la UI de target (:5173) manteniendo propiedad `550482` / campo `superficie_m2`;
(6) los archivos sucios protegidos fuera del commit e inalterados en disco; y
(7) datos (hashes + 20 PDFs) y flujos legacy intactos.

# §3 Key Findings
## Hallazgos clave

- La unica violacion de imports de Automation→Target es en
  `backend/services/schematics.py` y `backend/routers/schematics.py`
  (`target_system.backend.services.properties`), usada para existencia y
  `archivo_esquematico`. Se reemplaza por HTTP contra target.
- `backend/routers/{properties,stats}.py` y `backend/main.py` son delegados de
  target / monolitico: se retiran del arbol (target tiene copias propias).
- Los archivos sucios protegidos (POC Playwright contra Mock External :5174)
  solo importan `backend.main` / `backend.services.automation`; al mover los
  modulos, el POC queda inerte en disco pero intacto y fuera del commit.
- Los 3 imports legacy a `backend.*` (pdf_creator y pipeline_app) se reescriben
  a `automation_system.backend.*`.
- Los selectores de la UI de target para Playwright son
  `#property-field-superficie|-capacidad|-estacionamiento|-anio|-salas`, boton
  "Guardar cambios", feedback `role="status"`.

# §4 Work Completed
## Trabajo completado

- **Fase 1 y 2 entregadas y commiteadas** (`cb2d2c7`): extraccion del Target
  System; paridad de endpoints vs `docs/phase0_endpoint_baseline.json`;
  builds de frontend; regresion del monolitico; Streamlit ok; hashes + 20 PDFs
  verificados.
- **Exploracion completa** de la superficie de codigo (backend, frontend,
  target, mock, common, shared_store, pdf_creator, pipeline_app) y de los
  diffs sucios protegidos.
- **(v1) Este README final-state y el informe §7 se escribieron ANTES de la
  implementacion (requisito Step 7); v2 se completa al cierre (ver §7).**
- **Implementacion completada y verificada** en una unica operacion:

# §5 Active Work
## Trabajo activo

- Migracion del backend de Automation: `git mv` de
  `backend/services/{automation,compare,compare_api,ocr,schematics}.py`,
  `backend/routers/{ocr,compare,schematics}.py`, `backend/deps.py`,
  `backend/routers/__init__.py`, `backend/tests/{__init__,test_automation}.py`
  hacia `automation_system/backend/`, con imports reescritos a
  `automation_system.backend.*`.
- Creacion de modulos nuevos de Automation: `main.py` (:8001, CORS 5174),
  `schemas.py` (solo contratos de automation + Playwright),
  `routers/automation.py` (preview/apply/playwright),
  `services/target_api.py` (cliente HTTP de target),
  `services/playwright_automation.py` (retargeteado a :5173),
  `tests/test_playwright_validation.py` (sin browser).
- Frontend de Automation: Vite :5174 → API :8001, rutas
  Esquematicos/OCR/Comparar/Automatizar, navegacion solo "Pipeline OCR", endpoint
  nuevo `GET /api/schematics/catalog` (pagina Esquematicos desacoplada de
  `fetchProperties` de target), links externos a la UI de target en
  Comparar/Automatizar. Copia sin `Dashboard`, `Properties` ni `PropertyDetail`.
- Retiro del monolitico del arbol: `git rm` de `backend/main.py`,
  `backend/routers/{properties,stats}.py` y `frontend/`; untrack de
  `backend/schemas.py` y `backend/routers/automation.py` (contenido en disco
  intacto).
- Rewrite de imports legacy: `pdf_creator/app_pdf_creator.py` →
  `automation_system.backend.services.schematics`;
  `pipeline_app/pages/2_Comparar.py` →
  `automation_system.backend.services.compare`;
  `pipeline_app/pages/3_Automatizar.py` →
  `automation_system.backend.services.automation`.

# §6 Blocked
## Bloqueado

- Nada bloquea actualmente. Dependencias externas solo a nivel runtime
  (target arriba) para el E2E Playwright por browser, que se documenta y se
  verifica manualmente.
- `requirements.txt` mantiene su diff sucio (agrega `playwright`); no entra al
  commit. Una instalacion fresca del arbol commiteado necesita correr
  `pip install playwright` para el flujo bybrowser.

# §7 Final Report
## Informe final

### v1 — Antes de la implementacion (snapshot)

- `automation_system/` no existe aun en el arbol. El monolitico `backend/` y
  `frontend/` son las aplicaciones actuales; los archivos sucios protegidos
  estan en su estado POC (Playwright contra Mock External :5174).
- La estructura final prevista (§5) es la contrato contra la cual se escribe
  la implementacion. El contenido real de este informe se actualiza en v2
  (despues de implementar) con los artefactos y verificaciones logradas.
- Pendiente de verificar al final: paridad de endpoints, cero imports
  cruzados, sin duplicacion de servicios, hashes + PDFs intactos, tests y
  builds en verde, `git status` mostrando SOLO los archivos sucios protegidos.

### v2 — Despues de la implementacion (verificaciones concretas)

- **Automation plana (cero cross-imports):** `automation_system/` no importa
  `target_system` (grep de imports limpio; solo menciones en docstrings y
  mensajes de error) ni el monolitico `backend.`; `target_system/` no importa
  `automation_system`.
- **Backend Automation verde:** `test_automation` (8 checks de logica de
  correcciones) y `test_playwright_validation` (validation 422 / campo invalido
  422 / propiedad 404 / escenario no_change sin browser) PASS, con
  `shared_store/` restaurado al snapshot en cada corrida. `main.py` importa
  limpio en :8001 con routers schematics/ocr/compare/automation (CORS 5174).
- **Target intacto:** `test_target_api` PASS (paridad contra
  `docs/phase0_endpoint_baseline.json`, PUT 422 preservado, y target responde
  404 en `/api/ocr`, `/compare`, `/schematics`, `/automation`).
- **Lock compartido:** `common.tests.test_store_lock` PASS (mutua exclusion,
  liberacion ante excepcion, timeout).
- **Frontends:** typecheck + build OK en `automation_system/frontend` (:5174 →
  :8001, seccion "Pipeline OCR"). El build de target (:5173) sigue igual.
- **Datos:** hashes intactos
  (`properties_db.xlsx`=ab298809…, `ground_truth.xlsx`=89196d8e…,
  `ocr_output.xlsx`=6a41ca57…); 20 PDFs en `shared_store/schematics/`.
- **Legacy:** los 3 imports `backend.*` reescritos a `automation_system.*`;
  `py_compile` OK en `pdf_creator/app_pdf_creator.py` y
  `pipeline_app/pages/{2_Comparar,3_Automatizar}.py`.
- **Commit:** un unico commit entrega la separacion; `git status` post-commit
  muestra SOLO los archivos sucios protegidos (`backend/`, `frontend/` residue,
  `requirements.txt`, `mock_external_system/`), todos fuera del commit e
  intactos en disco.
- **Verificacion manual (no automatizable sin runtime):** E2E Playwright por
  browser contra la UI real de target (:5173 + :8000 + :8001), documento en
  §Puertos y arranque.

# §8 Deliverables
## Entregables

1. `automation_system/backend/` — FastAPI :8001 (CORS 5174) con
   schematics/ocr/compare/automation y Playwright sobre UI de target.
2. `automation_system/frontend/` — Vite :5174 → API :8001, seccion "Pipeline OCR".
3. `backend/` y `frontend/` monoliticos retirados del arbol (archivos sucios
   protegidos intactos en disco, fuera del commit).
4. Rewrite de imports legacy (`pdf_creator`, `pipeline_app`) → `automation_system.*`.
5. Reporte final de 8 secciones (este archivo, §7) actualizado a v2.
6. Un unico commit que excluye los archivos sucios protegidos.