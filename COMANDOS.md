# COMANDOS — jr-career-copilot

COMANDO PARA INICIAR EN MENÚ INTERACTIVO DE CLI:
python src/cv_optimizer.py -i

## Requisitos previos

Colocar ofertas laborales como `.txt` en `jobs/`:
```
jobs/
  oferta_backend.txt
  oferta_soporte.txt
```

## Multi-proveedor: Gemini y DeepSeek

El flag `-m` controla el modelo para **los tres features** (optimizador, entrevista, auditoría):

```bash
# Gemini (default) — optimiza, entrevista y audita con Gemini 2.5 Flash
python src/cv_optimizer.py -j jobs/oferta.txt --mock-interview --robustness

# DeepSeek — optimiza, entrevista y audita con DeepSeek V4 Pro
python src/cv_optimizer.py -j jobs/oferta.txt --mock-interview --robustness -m deepseek
```

## Entrevista simulada

```bash
# Solo entrevista, sin re-optimizar (Gemini)
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --interview-only

# Solo entrevista con DeepSeek
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --interview-only -m deepseek

# Optimizar + entrevista (Gemini)
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --mock-interview

# Optimizar + entrevista (DeepSeek)
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --mock-interview -m deepseek
```

## Auditoría de robustez

```bash
# Optimizar + auditar (Gemini)
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --robustness

# Optimizar + auditar (DeepSeek)
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --robustness -m deepseek

# Solo auditoría, sin re-optimizar (Gemini)
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --robustness-only

# Solo auditoría con DeepSeek
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --robustness-only -m deepseek
```

Genera `robustness_report.json` con score de honestidad (0-100), alucinaciones detectadas y comentario del auditor.

## Todo junto

```bash
# Optimizar + entrevista + auditoría (Gemini)
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --mock-interview --robustness

# Optimizar + entrevista + auditoría (DeepSeek)
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --mock-interview --robustness -m deepseek
```

---

## Modo interactivo (recomendado)

```bash
python src/cv_optimizer.py -i
```

El CLI te guía paso a paso. Al finalizar la optimización pregunta si querés:
- Ejecutar entrevista simulada (con el modelo elegido)
- Ejecutar auditoría de robustez (con el modelo elegido)

Podés salir con `0` en cualquier menú.

---

## Modo directo (flags)

### Gemini (default)

```bash
python src/cv_optimizer.py -j jobs/oferta.txt
```

### DeepSeek

```bash
python src/cv_optimizer.py -j jobs/oferta.txt -m deepseek
```

### Con todos los flags

```bash
python src/cv_optimizer.py -j jobs/oferta.txt -p config/student_profile.yaml -l es -m gemini -o output/mi_cv.md
```

### En inglés

```bash
python src/cv_optimizer.py -j jobs/oferta.txt -l en
```

---

## Flags

| Flag | Default | Qué hace |
|------|---------|----------|
| `-j` | *(requerido)* | Archivo .txt con la oferta |
| `-p` | `config/student_profile.yaml` | Tu perfil YAML |
| `-o` | `output/optimized_cv.md` | Ruta base de salida |
| `-l` | `es` | Idioma: `es` o `en` |
| `-m` | `gemini` | Modelo para los 3 features: `gemini` o `deepseek` |
| `-t` | `templates/cv_template.html` | Plantilla HTML |
| `-i` | — | Modo interactivo |
| `--mock-interview` | — | Optimiza CV + simulador de entrevista técnica |
| `--interview-only` | — | Solo entrevista (sin re-optimizar). Requiere `-j` |
| `--robustness` | — | Optimiza CV + auditoría LLM-as-a-Judge |
| `--robustness-only` | — | Solo auditoría (sin re-optimizar). Requiere `-j` |

---

## Salidas

Cada oferta laboral genera su propia carpeta dentro de `output/` con formatos versionados:

```
output/
  job_ImproveSolutionsSAS/
    optimized_cv_v001.md
    optimized_cv_v001.html
    optimized_cv_v001.docx
    interview_transcript.md       ← --mock-interview / --interview-only
    robustness_report.json        ← --robustness
```

- **.md** — Markdown plano, legible en cualquier editor
- **.html** — Estilo premium, imprimible a PDF desde el navegador
- **.docx** — Formato Harvard ATS-friendly, editable en Word (recomendado para enviar)
- **interview_transcript.md** — Transcripción de la entrevista simulada (preguntas, respuestas, feedback)
- **robustness_report.json** — Reporte de auditoría: score de honestidad, alucinaciones, comentarios

Los CV (.md, .html, .docx) nunca se sobrescriben — se versionan (_v001, _v002...). La transcripción y el reporte se sobrescriben en cada ejecución.
