# DOCUMENTATION — CV Optimizer

## Propósito del programa

Optimizador de CV para ingenieros junior/trainees. Toma un perfil YAML del estudiante y una descripción de vacante, los envía a la API de Gemini 2.5 Flash, y produce un CV optimizado en Markdown y HTML listo para postular.

**Público objetivo:** Omar Villamizar (estudiante 9no semestre Ing. Sistemas, UFPS).

---

## Arquitectura

```
student_profile.yaml ──┐
                       ├──> file_io.py ──> optimizer.py (Gemini API) ──> OptimizedCV (Pydantic)
job_description.txt ───┘                                                      │
                                                                         ┌─────┴──────┐
                                                                         ▼            ▼
                                                                  renderers.py   renderers.py
                                                                      │              │
                                                                      ▼              ▼
                                                               optimized_cv.md  optimized_cv.html
```

### Módulos

| Módulo | Rol |
|--------|-----|
| `cv_optimizer.py` | Entry point. CLI args, orquestación del pipeline |
| `file_io.py` | Carga YAML de perfil, carga .txt de vacante, guarda outputs |
| `models.py` | Schemas Pydantic (`ContactInfo`, `OptimizedExperience`, `OptimizedEducation`, `OptimizedCV`) |
| `optimizer.py` | Prompt engineering + llamada Gemini 2.5 Flash con `response_schema` |
| `renderers.py` | Genera Markdown plano y HTML con Jinja2 |

### Stack técnico

- Python 3.10+
- `google-genai` SDK (Gemini 2.5 Flash)
- Pydantic (validación estructurada)
- Jinja2 (template HTML)
- `python-dotenv` (API key)

---

## Diagnóstico del output actual (`optimized_cv.md`)

### Problema 1: Tercera persona en resumen profesional

**Output actual:** *"Omar Jesús Villamizar Isaza es un prometedor estudiante..."*

**Causa raíz:** El prompt en `optimizer.py` (líneas 46-51) usa *"their achievements"*, *"their academic background"*, *"them"*. El system prompt trata al candidato como *"junior engineer"*. El modelo interpreta que debe describir al candidato como si un reclutador hablara de él.

**Qué dice GOOD_PRACTICES.md:** La sección 6.5 exige *"Inject personality & specificity"*. Un CV en primera persona suena a persona real, no a ficha de reclutador.

**Solución:** Reescribir el prompt para que genere el resumen en **primera persona** y suene a humano real hablando de sí mismo.

### Problema 2: Lenguaje excesivamente "AI"

**Output actual:** *"innata habilidad"*, *"sólida base"*, *"prometedor estudiante"*, *"enfoque proactivo"*.

**Causa raíz:** El prompt pide explícitamente aplicar el *"Pygmalion Effect"* y usar *"strong technical action verbs (e.g., 'Optimized query latency', 'Designed robust microservices', 'Spearheaded testing coverage')"*. Esto incentiva exactamente el lenguaje que GOOD_PRACTICES.md recomienda evitar.

**Qué dice GOOD_PRACTICES.md:** Sección 6.3 — *"Avoid overused AI phrases"*:
- ❌ "Spearheaded"
- ❌ "Seasoned professional"
- ❌ "Results-driven"
- ❌ "Proven track record"
- ❌ Overly complex sentence structures

La sección 6.1 reporta que **49% de los CV generados por IA son descartados** automáticamente por reclutadores.

**Solución:** Eliminar referencias al Pygmalion Effect, eliminar buzzwords del prompt, e instruir tono natural y conversacional.

### Problema 3: Footer revela generación por IA

**Output actual:** *"Currículum optimizado automáticamente utilizando Inteligencia Artificial (Gemini 2.5 Flash)."*

**Qué dice GOOD_PRACTICES.md:** Un reclutador que ve esto descarta el CV automáticamente.

**Solución:** Eliminar el footer del Markdown y HTML, o hacerlo opcional (solo debug).

### Problema 4: Temperatura baja (0.2)

**Valor actual:** `temperature=0.2`

**Qué causa:** Texto robótico, predecible, sin variación natural. El modelo elige siempre las palabras más probables, que son las que suenan a "CV genérico".

**Solución:** Subir a `temperature=0.7` para permitir redacción más natural sin riesgo de alucinación (el schema Pydantic ya fuerza la estructura).

### Problema 5: `experiences: []` en el perfil

El perfil no tiene experiencia laboral real. El modelo solo tiene proyectos académicos para rellenar la sección. No es un bug del programa, pero el output se beneficia de que el prompt maneje explícitamente este caso para no inflar proyectos como "experiencia profesional".

---

## Cambios aplicados

### 1. `optimizer.py` — Prompt reescrito

| Aspecto | Antes | Después |
|---------|-------|---------|
| Tono | Tercera persona, reclutador hablando del candidato | **Primera persona, el candidato habla de sí mismo** |
| Estilo | Pygmalion Effect, grandilocuente | **Natural, humano, conversacional profesional** |
| Buzzwords | "Spearheaded", "Robust", "Optimized" (solicitados) | **Prohibidos explícitamente** |
| Verbos | Verbos genéricos (diseñé, participé) | **Verb + contexto real + resultado** |
| AI detection | Sin consideración | **Instrucción explícita de sonar humano** |

**Prompt rules añadidas:**
- ✅ "Write the professional summary in FIRST PERSON (e.g., 'I am a...', 'My experience...'). Never refer to yourself in third person."
- ✅ "Use natural, conversational language. Read it aloud — if it sounds like a robot, rewrite it."
- ✅ "Never use buzzwords like 'spearheaded', 'results-driven', 'synergy', 'proven track record', 'seasoned', 'game-changer'..."
- ✅ "The final CV must NOT read as AI-generated. It must sound like a real person wrote it."

### 2. `renderers.py` — Footer eliminado

- Eliminado el footer que revelaba generación por IA.
- Ajustado el espaciado final en Markdown para que termine limpio.
- HTML ya no muestra el mensaje "optimizado por IA".

### 3. `optimizer.py` — Temperatura ajustada

| Parámetro | Antes | Después |
|-----------|-------|---------|
| `temperature` | 0.2 | 0.7 |

Se mantiene `response_schema=OptimizedCV` (validación Pydantic), lo que evita alucinaciones estructurales. La temperatura más alta solo afecta la redacción, no la veracidad de los datos.

### 4. `renderers.py` + `models.py` — Formato mejorado y secciones nuevas

- Skills ahora listados con viñetas (`-`) en vez de coma separada para mejor densidad semántica (más peso ATS).
- Headers simplificados a estándar ATS: "Habilidades", "Educación" (ya no "y Tecnologías" ni "y Proyectos Académicos").
- **Nueva sección `Proyectos`**: schema Pydantic `OptimizedProject` + renderizado en Markdown y HTML.
- **Nueva sección `Certificaciones`**: schema Pydantic `Certification` + renderizado en Markdown y HTML.
- CSS muerto del footer eliminado del template HTML.

---

## Buenas prácticas implementadas (desde GOOD_PRACTICES.md)

| Práctica | Estado |
|----------|--------|
| Single-column layout | ✅ Ya implementado en HTML |
| Standard section headers | ✅ "Resumen Profesional", "Experiencia", "Educación", "Habilidades", "Proyectos", "Certificaciones" |
| No tables/graphics/icons | ✅ Markdown plano, HTML sin tablas |
| Quantifiable metrics | ✅ Prompt instruye fórmula [Verbo] + [Tarea] + [Resultado cuantificable] + [Contexto] |
| Mirror job description language | ✅ Prompt instruye reflejar lenguaje de la oferta |
| Avoid AI phrases (spearheaded, etc.) | ✅ Nuevo prompt los prohíbe explícitamente |
| First person | ✅ Nuevo prompt fuerza primera persona |
| No AI disclosure footer | ✅ Footer eliminado |
| Human-in-the-loop review | ✅ El programa no cambia, pero el prompt mejora la calidad base |
| Keyword in context | ✅ Prompt instruye colocar keywords en achievements |
| Acronyms + full forms | ✅ Prompt instruye incluir ambos |
| No hallucination | ✅ Ya implementado (regla de veracidad en prompt + schema Pydantic) |

---

## Lo que NO cambió (core preservado)

- **Pipeline completo**: profile → job → Gemini → Pydantic → Markdown/HTML
- **Estructura de módulos**: `file_io.py`, `models.py`, `optimizer.py`, `renderers.py`
- **CLI interface**: mismos flags `-j`, `-p`, `-o`, `-l`, `-t`
- **Validación Pydantic**: `OptimizedCV` como schema de respuesta
- **Idiomas**: español/inglés (`-l es|en`)
- **Salidas duales**: Markdown + HTML siempre
- **Veracidad**: nunca inventar logros, fechas o métricas

---

## Cómo usar

### Modo rápido (flags por línea de comandos)

```bash
python src/cv_optimizer.py -j jobs/oferta.txt -p config/student_profile.yaml -o output/mi_cv.md -l es -m gemini
```

### Modo interactivo (recomendado)

```bash
python src/cv_optimizer.py -i
```

El CLI te guía paso a paso: modelo → perfil → oferta → idioma → template → confirmación.

### Flags disponibles

| Flag | Default | Descripción |
|------|---------|-------------|
| `-j`, `--job` | *(requerido)* | Ruta al `.txt` con la descripción de la vacante. Solo en modo no interactivo. |
| `-p`, `--profile` | `config/student_profile.yaml` | Ruta al perfil YAML del estudiante. |
| `-o`, `--output` | `output/optimized_cv.md` | Ruta base de salida. Siempre se auto-versiona (`_v001`, `_v002`, ...). |
| `-l`, `--lang` | `es` | Idioma: `es` (español) o `en` (inglés). |
| `-t`, `--template` | `templates/cv_template.html` | Plantilla HTML Jinja2. |
| `-m`, `--model` | `gemini` | Modelo: `gemini` (Gemini 2.5 Flash) o `deepseek` (DeepSeek V4 Pro). |
| `-i`, `--interactive` | *(flag)* | Lanza el CLI interactivo. Ignora el resto de flags excepto `-o`. |

### Directorio `jobs/`

Coloca tus descripciones de vacantes como archivos `.txt` dentro de `jobs/`. El CLI interactivo las lista automáticamente para que elijas.

```
jobs/
  oferta_backend.txt
  oferta_soporte.txt
  oferta_frontend.txt
```

Si el directorio no existe, el programa lo crea automáticamente al entrar en modo interactivo.

### Versionado de outputs

Cada ejecución genera archivos con número de versión automático. Nunca se sobrescribe:

```
output/
  optimized_cv_v001.md
  optimized_cv_v001.html
  optimized_cv_v002.md
  optimized_cv_v002.html
  ...
```

El patrón escanea el directorio y toma el siguiente número disponible. MD y HTML siempre quedan pareados con el mismo número de versión.

### Variables de entorno (`.env`)

```env
# Gemini (Google AI Studio)
GEMINI_API_KEY=tu_clave

# DeepSeek (platform.deepseek.com)
DEEPSEEK_API_KEY=tu_clave
```

Solo necesitás la key del proveedor que vayas a usar. El programa falla con un mensaje claro si falta.

---

## Próximas mejoras sugeridas (fuera del alcance actual)

1. **Análisis de keywords**: Extraer y mostrar qué keywords de la oferta están cubiertas vs. faltantes.
2. **ATS score**: Calcular 0-100 de compatibilidad con ATS.
3. **Soporte DOCX**: Generar .docx (formato preferido por ATS según GOOD_PRACTICES.md).
4. **Modo "humanización"**: Segunda pasada que detecte y remueva frases AI-genéricas.
5. **Multi-modelo**: Soportar Claude, GPT-4, etc. (estructura ya lo permite).
6. **Modo draft/sugerencia**: Que el output sean sugerencias editables, no el CV final.

---

## Referencias

- `GOOD_PRACTICES.md` — Reporte de buenas prácticas para CV generados por IA (Mayo 2026).
- Estructura Pydantic documentada en `src/models.py`.
- Template HTML en `templates/cv_template.html`.
