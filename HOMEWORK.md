# HOMEWORK — Taller Práctico: Robustez y Simulación de Entrevistas con IA

> **Rama objetivo:** `feat/mock-interview-robustness`
> **Stack:** Python 3.10+ · Gemini 2.5 Flash · Pydantic · Google GenAI SDK
> **Autor:** Omar Villamizar

---

## 1. Resumen del entregable

Implementar **2 features** sobre el pipeline existente de `jr-career-copilot`:

| # | Feature | Flag CLI | Output |
|---|---------|----------|--------|
| 1 | **Mock Interview** — Simulador interactivo de entrevista técnica con Gemini como reclutador | `--mock-interview` | `output/job_<name>/interview_transcript.md` |
| 2 | **Robustness Judge** — Validador LLM-as-a-Judge que audita el CV generado | `--robustness` | `output/job_<name>/robustness_report.json` |

Ambos features se integran como flags opcionales al pipeline existente. El flujo normal (`-j archivo.txt`) **no se altera**.

---

## 2. Checklist: lo que ya está hecho

| # | Requisito | Estado |
|---|-----------|--------|
| 1 | `config/student_profile.yaml` con datos reales de Omar Villamizar | ✅ Completo (85 líneas, skills, educación, proyectos, certificaciones) |
| 2 | Pipeline base funcional: `cv_optimizer.py` → `optimizer.py` → `renderers.py` | ✅ Completo |
| 3 | Gemini 2.5 Flash + DeepSeek V4 Pro con Structured Outputs | ✅ Funcionando (multi-proveedor) |
| 4 | Salidas versionadas por job: `.md`, `.html`, `.docx` | ✅ Funcionando (`file_io.py`) |
| 5 | Prompt con reglas de oro: primera persona, sin buzzwords, sin footer IA | ✅ Implementado |
| 6 | Sistema de versionado de outputs (`_v001`, `_v002`, ...) | ✅ Funcionando |

---

## 3. Lo que falta: roadmap paso a paso

### Fase 0 — Preparación (datos)

- [x] **0.1** Crear `jobs/job_ImproveSolutionsSAS.txt` — Agente de Mesa de Ayuda / Soporte Técnico (Cúcuta)
- [x] **0.2** Crear `jobs/job_CapgeminiEngineering.txt` — Vacante real de LinkedIn #2
- [x] **0.3** Crear `jobs/job_Coopidrogas.txt` — Vacante real de LinkedIn #3

> **Convención:** Los archivos de jobs siguen el patrón `job_NOMBRE.txt`. El código limpia prefijos (`job_`, `job_description_`, `oferta_`) al derivar el nombre de carpeta: `job_ImproveSolutionsSAS.txt` → `output/job_ImproveSolutionsSAS/`.
>
> **Nota:** Buscar en LinkedIn vacantes para **Desarrollador Junior**, **Frontend Trainee**, **Backend Junior**, **Soporte TI** o **Analista de Datos Junior** en Colombia. Cada archivo debe contener: título, descripción, responsabilidades, requisitos, tecnologías.

### Fase 1 — Feature 1: Mock Interview (`src/services/mock_interview.py`)

- [x] **1.1** Crear directorio `src/services/` con `__init__.py`
- [x] **1.2** Implementar clase `MockInterviewService` (~230 líneas):
  - `__init__(self, profile: dict, job_description: str)` — recibe perfil y JD
  - `_build_system_instruction()` — construye el `system_instruction` para Gemini
  - `run_interactive()` — loop de chat en consola, máx 7 preguntas
  - `export_transcript(output_path: str)` — guarda historial como Markdown
  - Manejo de `KeyboardInterrupt` (Ctrl+C para salir antes) y `RuntimeError` (API caída)
- [x] **1.3** Integrar flag `--mock-interview` en `cv_optimizer.py`
- [x] **1.4** Integrar en modo interactivo (`-i`) como opción adicional
- [x] **1.5** Agregar flag `--interview-only` (solo entrevista, sin re-optimizar CV)

### Fase 2 — Feature 2: Robustness Judge (`src/services/robustness_judge.py`)

- [x] **2.1** Implementar modelos Pydantic en `src/models.py`:
  - `Alucinacion(linea_cv, dato_inventado, severidad)`
  - `ReporteRobustez(score_honestidad, alucinaciones_detectadas, comentario_auditor)`
- [x] **2.2** Implementar clase `RobustnessJudgeService` (~233 líneas):
  - `__init__(self, profile: dict, job_description: str)` — recibe perfil y JD
  - `_build_audit_prompt(markdown_cv: str)` — construye el prompt de auditoría
  - `run_validation(markdown_cv: str) -> ReporteRobustez` — llama a Gemini con Structured Outputs
  - `export_report(report: ReporteRobustez, output_path: str)` — guarda JSON
- [x] **2.3** Integrar flag `--robustness` en `cv_optimizer.py`
- [x] **2.4** Integrar en modo interactivo (`-i`)

### Fase 3 — Integración y testing

- [x] **3.1** Actualizar `COMANDOS.md` con los nuevos flags
- [x] **3.2** Ejecutar ciclo completo con `job_ImproveSolutionsSAS.txt`:
  - `--mock-interview` ✅ (entrevista + transcripción)
  - `--robustness` ✅ (reporte JSON generado, score 55/100)
- [x] **3.3** Verificar outputs generados en `output/job_ImproveSolutionsSAS/`
- [x] **3.4** Repetir con `job_CapgeminiEngineering.txt` y `job_Coopidrogas.txt` ✅ (3 vacantes operativas)

### Fase Final — Git

- [x] **4.1** Asegurar que la rama es `feat/mock-interview-robustness`
- [x] **4.2** Commits limpios (ver formato en AGENTS.md)
- [x] **4.3** Push y PR (si aplica)

---

## 🎯 Extras implementados (fuera del scope original)

| Extra | Descripción |
|-------|-------------|
| **Multi-proveedor** | Soporte para DeepSeek V4 Pro en los 3 features (optimizador, entrevista, auditoría). Flag `-m deepseek`. |
| **`--interview-only`** | Ejecuta solo la entrevista sin re-optimizar el CV. |
| **`--robustness-only`** | Ejecuta solo la auditoría sin re-optimizar el CV. |
| **Modo interactivo (`-i`)** | CLI paso a paso que guía al usuario por todas las opciones. |
| **DOCX Harvard ATS** | Exportación a formato Word con estilo Harvard (`docx_renderer.py`). |
| **Limpieza de markdown fences** | DeepSeek a veces envuelve JSON en backticks — el parser los limpia automáticamente. |

---

## 4. Plan detallado por feature

### 4.1 Mock Interview (`--mock-interview`)

#### Arquitectura

```
cv_optimizer.py
  │
  ├── parse_arguments()  ← nuevo flag: --mock-interview
  │
  └── main()
        └── if args.mock_interview:
              └── MockInterviewService(profile, job_description)
                    ├── run_interactive()       ← chat loop en consola
                    └── export_transcript()     ← guarda output/interview_transcript.md
```

#### Clase: `MockInterviewService`

```
src/services/
  __init__.py
  mock_interview.py
```

**Métodos:**

| Método | Responsabilidad |
|--------|----------------|
| `__init__(profile, job_description)` | Almacena perfil, JD, inicializa `message_history = []` |
| `_build_system_instruction() -> str` | Construye el `system_instruction` del entrevistador |
| `run_interactive() -> None` | Loop `while len(questions_asked) < 7` con input del usuario |
| `export_transcript(output_path) -> None` | Serializa `message_history` a Markdown |

#### `system_instruction` del entrevistador

Reglas que debe cumplir el prompt:

1. **Rol:** Reclutador técnico experimentado entrevistando a un candidato junior.
2. **Contexto:** Solo preguntar sobre tecnologías y proyectos que aparecen en el **CV del candidato** y en la **JD**.
3. **Límite:** Máximo 7 preguntas. Tras la séptima, generar **feedback constructivo** (fortalezas, áreas de mejora, recomendaciones).
4. **Tono:** Profesional pero amigable. Sin tecnicismos innecesarios.
5. **Formato de respuesta:** Pregunta clara + breve contexto de por qué la hace.
6. **Progresión:** Empezar con preguntas generales (background, proyectos), luego profundizar en tecnologías específicas de la JD, terminar con escenarios prácticos.
7. **No preguntar:** Experiencia laboral que el candidato no tiene (si `experiences` está vacío, no preguntar "cuéntame de tu último trabajo").
8. **Idioma:** Español (por default, respetando `-l`).

#### Chat Memory (patrón multi-turn)

```python
from google import genai
from google.genai import types

messages = []  # historial acumulativo

# Cada turno:
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=self._build_system_instruction(),
    ),
    contents=messages  # historial completo hasta ahora
)

# Agregar al historial:
messages.append({"role": "model", "parts": [{"text": response.text}]})
messages.append({"role": "user", "parts": [{"text": user_input}]})
```

#### Formato de transcripción (`interview_transcript.md`)

```markdown
# Transcripción de Entrevista Técnica

**Candidato:** Omar Jesús Villamizar Isaza
**Vacante:** [título de la JD]
**Fecha:** [fecha actual]
**Preguntas realizadas:** 7/7

---

## Pregunta 1 — [tema]
**Reclutador:** [pregunta]
**Candidato:** [respuesta del usuario]

## Pregunta 2 — [tema]
...

---

## Feedback del Reclutador
[fortalezas, áreas de mejora, recomendaciones]
```

---

### 4.2 Robustness Judge (`--robustness`)

#### Arquitectura

```
cv_optimizer.py
  │
  ├── parse_arguments()  ← nuevo flag: --robustness
  │
  └── main()
        └── _run_pipeline()
              │
              ├── [pipeline normal: optimizar CV]
              │
              └── if args.robustness:   ← se ejecuta DESPUÉS del pipeline
                    └── RobustnessJudgeService(profile, job_description)
                          ├── run_validation(md_content)
                          └── export_report()
```

**Flujo:** El pipeline normal genera el CV optimizado → inmediatamente después, el Robustness Judge audita ese CV generado.

#### Clase: `RobustnessJudgeService`

```
src/services/
  __init__.py
  robustness_judge.py
```

**Métodos:**

| Método | Responsabilidad |
|--------|----------------|
| `__init__(profile, job_description)` | Almacena perfil y JD como fuente de verdad |
| `_build_audit_prompt(markdown_cv) -> str` | Construye el prompt con el CV a auditar + perfil original |
| `run_validation(markdown_cv) -> ReporteRobustez` | Llama a Gemini con Structured Outputs |
| `export_report(report, output_path) -> None` | Serializa `ReporteRobustez` a JSON |

#### Modelos Pydantic (a agregar en `src/models.py`)

```python
class Alucinacion(BaseModel):
    """Una alucinación detectada en el CV generado."""
    linea_cv: str = Field(description="Línea del CV que contiene el dato inventado")
    dato_inventado: str = Field(description="Qué dato específico fue inventado o exagerado")
    severidad: str = Field(description="Severidad: 'baja', 'media', 'alta'")

class ReporteRobustez(BaseModel):
    """Reporte completo de auditoría de robustez del CV generado."""
    score_honestidad: int = Field(
        ge=0, le=100,
        description="Puntuación de honestidad del CV (0-100). 100 = totalmente veraz."
    )
    alucinaciones_detectadas: List[Alucinacion] = Field(
        default_factory=list,
        description="Lista de alucinaciones detectadas"
    )
    comentario_auditor: str = Field(
        description="Resumen del auditor: fortalezas, riesgos detectados, recomendaciones"
    )
```

#### Prompt de auditoría (`_build_audit_prompt`)

El prompt debe instruir a Gemini para:

1. **Comparar** el CV generado (Markdown) contra el perfil YAML original (fuente de verdad).
2. **Detectar alucinaciones**: datos que aparecen en el CV pero NO en el perfil YAML.
3. **Detectar inconsistencias**: fechas contradictorias, cargos inflados, métricas inventadas.
4. **Verificar compliance ético**: ¿se respetó la regla de no inventar? ¿el tono es profesional?
5. **Asignar score de honestidad** (0-100).
6. **Responder en español** (o inglés si `-l en`).

#### Structured Outputs (patrón)

```python
from google import genai
from google.genai import types

# Usar el schema Pydantic directamente (mismo patrón que optimizer.py)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ReporteRobustez,   # Pydantic model
    ),
    contents=prompt
)

report = ReporteRobustez.model_validate_json(response.text)
```

#### Formato de salida (`robustness_report.json`)

```json
{
  "score_honestidad": 92,
  "alucinaciones_detectadas": [
    {
      "linea_cv": "Optimized PostgreSQL queries reducing latency by 30%",
      "dato_inventado": "El porcentaje '30%' no existe en el perfil YAML original",
      "severidad": "media"
    }
  ],
  "comentario_auditor": "El CV es mayormente veraz. Se detectó una métrica no respaldada..."
}
```

---

### 4.3 Cambios en `cv_optimizer.py`

#### Nuevos flags en `parse_arguments()`

```python
parser.add_argument(
    "--mock-interview",
    action="store_true",
    help="Ejecuta el simulador de entrevista técnica con IA después de optimizar el CV."
)
parser.add_argument(
    "--robustness",
    action="store_true",
    help="Ejecuta el validador de robustez (LLM-as-a-Judge) sobre el CV generado."
)
```

#### Lógica en `main()` / `_run_pipeline()`

```python
# Después de generar md_content en _run_pipeline():

if run_mock_interview:
    from services.mock_interview import MockInterviewService
    interview = MockInterviewService(profile, job_description)
    interview.run_interactive()
    transcript_path = os.path.join(job_dir, "interview_transcript.md")
    interview.export_transcript(transcript_path)

if run_robustness:
    from services.robustness_judge import RobustnessJudgeService
    judge = RobustnessJudgeService(profile, job_description)
    report = judge.run_validation(md_content)
    report_path = os.path.join(job_dir, "robustness_report.json")
    judge.export_report(report, report_path)
```

Los parámetros `run_mock_interview` y `run_robustness` deben pasar por todo el pipeline hasta `_run_pipeline()`.

---

## 5. Estructura de archivos (resultado final)

```
jr-career-copilot/
├── config/
│   └── student_profile.yaml          ← ✅ ya existe
├── jobs/
│   ├── job_ImproveSolutionsSAS.txt      ← ✅ ya existe
│   ├── job_CapgeminiEngineering.txt     ← ✅ ya existe
│   └── job_Coopidrogas.txt             ← ✅ ya existe
├── src/
│   ├── cv_optimizer.py               ← ✏️ modificar (nuevos flags + lógica)
│   ├── models.py                     ← ✏️ modificar (Alucinacion, ReporteRobustez)
│   ├── optimizer.py                  ← sin cambios
│   ├── file_io.py                    ← sin cambios
│   ├── renderers.py                  ← sin cambios
│   ├── docx_renderer.py              ← sin cambios
│   ├── test_cv_optimizer.py          ← sin cambios (opcional: nuevos tests)
│   └── services/                     ← 🆕 nuevo directorio
│       ├── __init__.py               ← 🆕
│       ├── mock_interview.py         ← 🆕 (~200 líneas)
│       └── robustness_judge.py       ← 🆕 (~250 líneas)
├── output/
│   └── job_ImproveSolutionsSAS/
│       ├── optimized_cv_v001.md      ← generado por pipeline normal
│       ├── optimized_cv_v001.html
│       ├── optimized_cv_v001.docx
│       ├── interview_transcript.md   ← 🆕 generado por --mock-interview
│       └── robustness_report.json    ← 🆕 generado por --robustness
└── ...
```

---

## 6. Criterios de aceptación (alineados con rúbrica)

### Feature 1 — Mock Interview (30%)

| # | Criterio | Verificación |
|---|----------|-------------|
| 1.1 | Chat interactivo funciona en consola | Ejecutar `--mock-interview`, responder preguntas |
| 1.2 | Memoria preservada (el entrevistador referencia respuestas anteriores) | Pregunta 3 debe hacer referencia a respuesta de pregunta 1 |
| 1.3 | Máximo 7 preguntas, luego feedback automático | Contar preguntas en transcripción |
| 1.4 | Solo pregunta sobre tecnologías del CV + JD | Verificar que no pregunta sobre tecnologías no listadas |
| 1.5 | Transcripción exportada correctamente | Abrir `interview_transcript.md`, verificar formato |
| 1.6 | Manejo de Ctrl+C (salida graceful) | Presionar Ctrl+C a mitad de entrevista |
| 1.7 | Respetar idioma (`-l es` / `-l en`) | Probar con ambos |

### Feature 2 — Robustness Judge (30%)

| # | Criterio | Verificación |
|---|----------|-------------|
| 2.1 | Detecta alucinaciones reales | Insertar dato falso en perfil, verificar que lo detecta |
| 2.2 | Output es JSON válido | `python -c "import json; json.load(open('.../robustness_report.json'))"` |
| 2.3 | Score de honestidad entre 0-100 | Verificar rango en JSON |
| 2.4 | Comentario del auditor es útil y accionable | Leer `comentario_auditor`, verificar que no es genérico |
| 2.5 | No alucina él mismo (el juez no inventa problemas) | Probar con perfil 100% veraz, score debe ser >90 |
| 2.6 | Estructura Pydantic validada | Si Gemini devuelve JSON inválido, el programa debe fallar con error claro |

### Ingeniería de Prompts (20%)

| # | Criterio |
|---|----------|
| 3.1 | System prompt del entrevistador previene preguntas off-topic |
| 3.2 | System prompt del entrevistador maneja el caso "sin experiencia laboral" |
| 3.3 | Prompt del auditor es preciso: compara CV vs perfil YAML, no vs "lo que espera ver" |
| 3.4 | Prompt del auditor no penaliza reformulaciones legítimas (solo datos inventados) |

### Code Quality (10%)

| # | Criterio |
|---|----------|
| 4.1 | Type hints en todos los métodos públicos |
| 4.2 | Docstrings en clases y métodos públicos |
| 4.3 | Sin duplicación de código con módulos existentes |
| 4.4 | Manejo de errores: API key faltante, respuesta vacía, JSON inválido |

### Git & Entrega (10%)

| # | Criterio |
|---|----------|
| 5.1 | Rama `feat/mock-interview-robustness` |
| 5.2 | Commits con formato Conventional Commits |
| 5.3 | No hay archivos basura, secrets, o `.pyc` commiteados |

---

## 7. Comandos de verificación

### Mock Interview

```bash
# Vacante 1
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --mock-interview

# Vacante 2
python src/cv_optimizer.py -j jobs/job_CapgeminiEngineering.txt --mock-interview

# Vacante 3
python src/cv_optimizer.py -j jobs/job_Coopidrogas.txt --mock-interview
```

### Robustness Judge

```bash
# Vacante 1
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --robustness

# Vacante 2
python src/cv_optimizer.py -j jobs/job_CapgeminiEngineering.txt --robustness

# Vacante 3
python src/cv_optimizer.py -j jobs/job_Coopidrogas.txt --robustness
```

### Ambos features juntos

```bash
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --mock-interview --robustness
```

### Validación de JSON

```bash
python -c "import json; data=json.load(open('output/job_ImproveSolutionsSAS/robustness_report.json', encoding='utf-8')); print(f'Score: {data[\"score_honestidad\"]}/100')"
```

---

## 8. Notas técnicas importantes

### SDK de Gemini

El proyecto ya usa el SDK moderno:
```python
from google import genai
from google.genai import types
client = genai.Client()
```

**No usar** `google-generativeai` ni `genai.models.generate_content()` (API legacy). Usar el patrón de `optimizer.py`:
```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(...),
    contents=...   # para multi-turn chat
)
```

### Estructura de `contents` (chat multi-turn)

Para Mock Interview, el historial se pasa como `contents`:
```python
contents=[
    {"role": "user", "parts": [{"text": "..."}]},
    {"role": "model", "parts": [{"text": "..."}]},
    {"role": "user", "parts": [{"text": "..."}]},
    # ... crece con cada turno
]
```

El primer `contents` debe iniciar con un mensaje del usuario simulando el inicio de la entrevista, o el `system_instruction` debe instruir al modelo a hacer la primera pregunta directamente.

### Directorio `output/`

Los outputs de los nuevos features **van dentro de la carpeta por job** (mismo patrón que los CV), pero **no se versionan** (son únicos por ejecución — la última ejecución sobrescribe la anterior):

```
output/job_ImproveSolutionsSAS/
  optimized_cv_v001.md
  optimized_cv_v001.html
  optimized_cv_v001.docx
  interview_transcript.md       ← sobrescribe cada vez
  robustness_report.json        ← sobrescribe cada vez
```

### Ramas Git

```bash
git checkout -b feat/mock-interview-robustness
```

Si la rama ya existe:
```bash
git checkout feat/mock-interview-robustness
```
