# DOCUMENTATION — CV Optimizer

## Propósito del programa

Optimizador de CV para ingenieros junior/trainees con **tres features integradas**:

| Feature | Descripción | Flag |
|---------|-------------|------|
| **CV Optimizer** | Optimiza el CV para una oferta laboral usando IA | `-j archivo.txt` |
| **Mock Interview** | Simulador de entrevista técnica con IA como reclutador | `--mock-interview` / `--interview-only` |
| **Robustness Judge** | Auditor LLM-as-a-Judge que detecta alucinaciones en el CV | `--robustness` / `--robustness-only` |

Soporta **Gemini 2.5 Flash** y **DeepSeek V4 Pro** en los tres features. El flag `-m` controla el modelo para todo el pipeline.

**Público objetivo:** Omar Villamizar (estudiante 9no semestre Ing. Sistemas, UFPS).

---

## Arquitectura

```
student_profile.yaml ──┐
                       ├──> file_io.py ──> optimizer.py ──> OptimizedCV (Pydantic)
job_description.txt ───┘         │                    │
                                 │                    ├──> renderers.py → .md, .html
                  ┌──────────────┤                    └──> docx_renderer.py → .docx
                  │              │
                  ▼              ▼
          services/        services/
      mock_interview.py  robustness_judge.py
            │                    │
            ▼                    ▼
   interview_transcript.md  robustness_report.json
```

### Módulos

| Módulo | Rol |
|--------|-----|
| `cv_optimizer.py` | Entry point. CLI args, orquestación del pipeline + interview + robustness |
| `file_io.py` | Carga YAML de perfil, carga .txt de vacante, guarda outputs versionados |
| `models.py` | Schemas Pydantic: `OptimizedCV`, `Alucinacion`, `ReporteRobustez` |
| `optimizer.py` | Prompt engineering + llamada Gemini/DeepSeek con `response_schema` |
| `renderers.py` | Genera Markdown plano y HTML con Jinja2 |
| `docx_renderer.py` | Conversor Markdown → DOCX estilo Harvard con python-docx |
| `services/mock_interview.py` | `MockInterviewService`: multi-turn chat, 7 preguntas + feedback |
| `services/robustness_judge.py` | `RobustnessJudgeService`: auditoría con Structured Outputs, score 0-100 |

### Stack técnico

- Python 3.10+
- `google-genai` SDK (Gemini 2.5 Flash) — Structured Outputs vía `response_schema`
- `openai` SDK (DeepSeek V4 Pro) — API compatible con OpenAI, JSON mode
- Pydantic ≥2.6 (validación estructurada en optimizador y auditor)
- Jinja2 (template HTML)
- Python-docx (exportación DOCX Harvard ATS)
- `python-dotenv` (API keys)

---

## Multi-proveedor: Gemini y DeepSeek

El flag `-m` selecciona el modelo para **los tres features simultáneamente**:

```bash
# Gemini (default) — optimiza, entrevista y audita con Gemini
python src/cv_optimizer.py -j jobs/oferta.txt --mock-interview --robustness

# DeepSeek — optimiza, entrevista y audita con DeepSeek
python src/cv_optimizer.py -j jobs/oferta.txt --mock-interview --robustness -m deepseek
```

| Proveedor | Modelo | SDK | Structured Outputs |
|-----------|--------|-----|-------------------|
| `gemini` | `gemini-2.5-flash` | `google-genai` | `response_schema=Pydantic` |
| `deepseek` | `deepseek-chat` | `openai` | `response_format: json_object` + schema en prompt |

**API keys requeridas** (solo la del proveedor que uses):
```env
GEMINI_API_KEY=tu_clave      # Google AI Studio
DEEPSEEK_API_KEY=tu_clave    # platform.deepseek.com
```

---

## Feature 1: Mock Interview (`--mock-interview` / `--interview-only`)

Simulador interactivo de entrevista técnica donde la IA actúa como reclutador.

### Funcionamiento

1. Gemini/DeepSeek recibe el perfil YAML + la descripción de la vacante como contexto
2. El modelo hace preguntas sobre tecnologías del CV y la oferta (máx 7)
3. El candidato responde por consola
4. Tras 7 preguntas, el modelo da feedback constructivo (fortalezas, áreas de mejora)
5. Se exporta transcripción a `output/job_NOMBRE/interview_transcript.md`

### Reglas del entrevistador (system prompt)

- Solo pregunta sobre tecnologías en CV ∩ JD
- Si el perfil no tiene experiencia laboral, no pregunta "cuéntame de tu último trabajo"
- Progresión: general → específico → escenario práctico
- Tono profesional, lenguaje natural, sin revelar que es IA
- Máximo 7 preguntas, luego feedback

### Multi-turn chat (memoria)

El historial crece con cada turno. Gemini usa `contents` (formato Google), DeepSeek usa `messages` (formato OpenAI). El servicio convierte automáticamente entre formatos.

### Comandos

```bash
# Optimizar + entrevista (mismo comando)
python src/cv_optimizer.py -j jobs/oferta.txt --mock-interview

# Solo entrevista (sin re-optimizar, usa el CV ya generado)
python src/cv_optimizer.py -j jobs/oferta.txt --interview-only

# Con DeepSeek
python src/cv_optimizer.py -j jobs/oferta.txt --interview-only -m deepseek
```

En modo interactivo (`-i`), al finalizar la optimización pregunta si querés ejecutar la entrevista.

---

## Feature 2: Robustness Judge (`--robustness`)

Validador LLM-as-a-Judge que audita el CV generado contra el perfil YAML original.

### Funcionamiento

1. Toma el CV generado (Markdown) y el perfil YAML (fuente de verdad)
2. Gemini/DeepSeek compara documento contra documento
3. Detecta: alucinaciones (datos inventados), métricas falsas, cargos inflados, tecnologías añadidas
4. Asigna severidad a cada hallazgo: `baja`, `media`, `alta`
5. Calcula `score_honestidad` (0-100)
6. Exporta reporte JSON a `output/job_NOMBRE/robustness_report.json`

### Modelos Pydantic

```python
class Alucinacion(BaseModel):
    linea_cv: str          # línea del CV con el dato inventado
    dato_inventado: str    # qué dato específico fue inventado
    severidad: str         # 'baja', 'media', 'alta'

class ReporteRobustez(BaseModel):
    score_honestidad: int                    # 0-100
    alucinaciones_detectadas: List[Alucinacion]
    comentario_auditor: str                  # resumen y recomendaciones
```

### Reglas del auditor (system prompt)

- No penaliza reformulaciones legítimas (solo datos inventados)
- Penaliza: métricas sin respaldo, cargos inflados, tecnologías no listadas, fechas alteradas
- Score: 95-100 veraz, 80-94 exageración menor, 60-79 datos no verificables, <59 alucinaciones graves
- Comentario constructivo y específico, no genérico

### Structured Outputs por proveedor

| Proveedor | Método |
|-----------|--------|
| Gemini | `response_schema=ReporteRobustez` (nativo Pydantic) |
| DeepSeek | `response_format={"type": "json_object"}` + schema JSON en system prompt |

### Comandos

```bash
# Optimizar + auditar
python src/cv_optimizer.py -j jobs/oferta.txt --robustness

# Solo auditoría (sin re-optimizar)
python src/cv_optimizer.py -j jobs/oferta.txt --robustness-only

# Con DeepSeek
python src/cv_optimizer.py -j jobs/oferta.txt --robustness-only -m deepseek

# Todo junto
python src/cv_optimizer.py -j jobs/oferta.txt --mock-interview --robustness
```

---

## Formato de salidas

Cada oferta laboral genera su propia carpeta dentro de `output/`:

```
output/
  job_ImproveSolutionsSAS/
    optimized_cv_v001.md           ← CV optimizado (Markdown)
    optimized_cv_v001.html         ← CV optimizado (HTML, imprimible a PDF)
    optimized_cv_v001.docx         ← CV optimizado (DOCX Harvard ATS)
    interview_transcript.md        ← Transcripción de entrevista (--mock-interview)
    robustness_report.json         ← Reporte de auditoría (--robustness)
```

- `.md`, `.html`, `.docx` se **versonan** (`_v001`, `_v002`, ...) — nunca se sobrescriben
- `interview_transcript.md` y `robustness_report.json` **se sobrescriben** en cada ejecución

---

## Cómo usar

### Modo interactivo (recomendado)

```bash
python src/cv_optimizer.py -i
```

El CLI guía paso a paso: modelo → perfil → oferta → idioma → template → confirmación. Al finalizar pregunta si querés ejecutar entrevista simulada y/o auditoría de robustez.

### Modo directo (flags)

```bash
# Solo optimizar CV
python src/cv_optimizer.py -j jobs/oferta.txt

# Optimizar + entrevista + auditoría
python src/cv_optimizer.py -j jobs/oferta.txt --mock-interview --robustness

# Solo entrevista (CV ya optimizado)
python src/cv_optimizer.py -j jobs/oferta.txt --interview-only

# Con DeepSeek en vez de Gemini
python src/cv_optimizer.py -j jobs/oferta.txt --robustness -m deepseek
```

### Flags disponibles

| Flag | Default | Descripción |
|------|---------|-------------|
| `-j`, `--job` | *(requerido)* | Ruta al `.txt` con la descripción de la vacante. |
| `-p`, `--profile` | `config/student_profile.yaml` | Ruta al perfil YAML del estudiante. |
| `-o`, `--output` | `output/optimized_cv.md` | Ruta base de salida (auto-versionada). |
| `-l`, `--lang` | `es` | Idioma: `es` (español) o `en` (inglés). |
| `-t`, `--template` | `templates/cv_template.html` | Plantilla HTML Jinja2. |
| `-m`, `--model` | `gemini` | Modelo para los 3 features: `gemini` o `deepseek`. |
| `-i`, `--interactive` | *(flag)* | CLI interactivo paso a paso. |
| `--mock-interview` | *(flag)* | Optimiza CV + lanza entrevista simulada. |
| `--interview-only` | *(flag)* | Solo entrevista (sin re-optimizar). Requiere `-j`. |
| `--robustness` | *(flag)* | Optimiza CV + ejecuta auditoría de robustez. |
| `--robustness-only` | *(flag)* | Solo auditoría (sin re-optimizar). Requiere `-j`. |

### Variables de entorno (`.env`)

```env
# Gemini (Google AI Studio)
GEMINI_API_KEY=tu_clave

# DeepSeek (platform.deepseek.com)
DEEPSEEK_API_KEY=tu_clave
```

Solo necesitás la key del proveedor que vayas a usar. El programa falla con un mensaje claro si falta.

---

## Buenas prácticas implementadas

| Práctica | Estado |
|----------|--------|
| Single-column layout | ✅ HTML y DOCX |
| Standard section headers | ✅ "Habilidades", "Experiencia", "Educación", "Proyectos", "Certificaciones" |
| No tables/graphics/icons | ✅ Markdown plano, HTML sin tablas |
| Quantifiable metrics | ✅ Fórmula [Verbo] + [Tarea] + [Resultado] + [Contexto] |
| Mirror job description language | ✅ Prompt instruye reflejar lenguaje de la oferta |
| Avoid AI phrases | ✅ Prohibidos: spearheaded, results-driven, synergy, etc. |
| First person | ✅ Prompt fuerza primera persona |
| No AI disclosure footer | ✅ Eliminado de MD, HTML y DOCX |
| Human-in-the-loop review | ✅ Checklist pre-submission en consola |
| Keyword in context | ✅ Keywords dentro de logros reales, no stuffing |
| ATS-ready format | ✅ DOCX Harvard con python-docx, MD plano |
| Secciones vacías omitidas | ✅ `## Experiencia` solo si hay experiences |
| Tiempos verbales correctos | ✅ Presente para roles en curso, pasado para completados |
| Orden cronológico inverso | ✅ Experiencias y proyectos más recientes primero |
| Sin emojis en contacto | ✅ Solo texto plano en info de contacto |
| Multi-modelo | ✅ Gemini 2.5 Flash + DeepSeek V4 Pro en los 3 features |
| Auditoría de veracidad | ✅ Robustness Judge: score 0-100, alucinaciones detectadas |

---

## Referencias

- `REPORT_GOOD_PRACTICES_DEEPSEEK.md` — Reporte de buenas prácticas (DeepSeek, Mayo 2026).
- `REPORT_GOOD_PRACTICES_GPT.md` — Reporte de buenas prácticas (ChatGPT, Mayo 2026).
- `HOMEWORK.md` — Roadmap de implementación con criterios de aceptación.
- `COMANDOS.md` — Cheatsheet rápida de comandos.
- Schemas Pydantic documentados en `src/models.py`.
- Template HTML en `templates/cv_template.html`.
