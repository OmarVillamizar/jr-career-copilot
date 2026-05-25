# COMANDOS — jr-career-copilot
COMANDO PARA INICIAR EN MENÚ INTERCATIVO DE CLI:
python src/cv_optimizer.py -i

## Requisitos previos

Colocar ofertas laborales como `.txt` en `jobs/`:
```
jobs/
  oferta_backend.txt
  oferta_soporte.txt
```

## Entrevista simulada (sin re-optimizar)

Si ya optimizaste el CV y solo quieres practicar la entrevista:

```bash
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --interview-only
```

## Entrevista simulada (optimizar + entrevista)

```bash
python src/cv_optimizer.py -j jobs/job_ImproveSolutionsSAS.txt --mock-interview
```
---
## Modo interactivo (recomendado)

```bash
python src/cv_optimizer.py -i
```

El CLI te guía paso a paso. Podés salir con `0` en cualquier menú.

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
| `-m` | `gemini` | Modelo: `gemini` o `deepseek` |
| `-t` | `templates/cv_template.html` | Plantilla HTML |
| `-i` | — | Modo interactivo |
| `--mock-interview` | — | Optimiza CV + simulador de entrevista técnica |
| `--interview-only` | — | Solo entrevista (sin re-optimizar). Requiere `-j` |
| `--robustness` | — | Validador LLM-as-a-Judge sobre el CV generado |

---

## Salidas

Cada oferta laboral genera su propia carpeta dentro de `output/` con 3 formatos versionados:

```
output/
  job_improvesolutions/
    optimized_cv_v001.md
    optimized_cv_v001.html
    optimized_cv_v001.docx
    optimized_cv_v002.md
    optimized_cv_v002.html
    optimized_cv_v002.docx
  job_backend/
    optimized_cv_v001.md
    optimized_cv_v001.html
    optimized_cv_v001.docx
```

- **.md** — Markdown plano, legible en cualquier editor
- **.html** — Estilo premium, imprimible a PDF desde el navegador
- **.docx** — Formato Harvard ATS-friendly, editable en Word (recomendado para enviar)

Nunca se sobrescribe. Cada job tiene su espacio aislado.
