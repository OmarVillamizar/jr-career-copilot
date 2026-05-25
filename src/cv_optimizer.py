import os
import sys
import re
import argparse
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from models import (
    ContactInfo,
    OptimizedExperience,
    OptimizedProject,
    OptimizedEducation,
    Certification,
    OptimizedCV
)
from file_io import (
    load_profile,
    load_job_description,
    save_markdown,
    save_html,
    save_markdown_versioned,
    save_html_versioned,
    save_docx_versioned
)
from renderers import (
    HEADERS,
    generate_markdown,
    generate_html
)
from optimizer import optimize_cv
from docx_renderer import generate_docx


# ── CLI ──

def parse_arguments() -> argparse.Namespace:
    """Analiza los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Optimizador de CV con IA para Ingenieros Junior."
    )
    parser.add_argument(
        "-j", "--job",
        help="Ruta al archivo .txt con la descripción de la vacante (requerido, excepto en modo interactivo)."
    )
    parser.add_argument(
        "-p", "--profile",
        default="config/student_profile.yaml",
        help="Ruta al perfil YAML del ingeniero junior (default: config/student_profile.yaml)."
    )
    parser.add_argument(
        "-o", "--output",
        default="output/optimized_cv.md",
        help="Ruta base de salida Markdown (default: output/optimized_cv.md). Siempre se versiona."
    )
    parser.add_argument(
        "-l", "--lang",
        default="es",
        choices=["es", "en"],
        help="Idioma de salida: 'es' o 'en' (default: 'es')."
    )
    parser.add_argument(
        "-t", "--template",
        default="templates/cv_template.html",
        help="Ruta a la plantilla HTML Jinja2 (default: templates/cv_template.html)."
    )
    parser.add_argument(
        "-m", "--model",
        default="gemini",
        choices=["gemini", "deepseek"],
        help="Modelo de IA a usar: 'gemini' (Gemini 2.5 Flash) o 'deepseek' (DeepSeek V4 Pro). Default: gemini."
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Lanza el CLI interactivo paso a paso (ignora el resto de flags excepto -o)."
    )
    parser.add_argument(
        "--mock-interview",
        action="store_true",
        help="Ejecuta el simulador de entrevista técnica con IA después de optimizar el CV."
    )
    parser.add_argument(
        "--interview-only",
        action="store_true",
        help="Ejecuta SOLO la entrevista simulada (sin re-optimizar el CV). Requiere -j."
    )
    parser.add_argument(
        "--robustness",
        action="store_true",
        help="Ejecuta el validador de robustez (LLM-as-a-Judge) sobre el CV generado."
    )
    return parser.parse_args()


# ── Interactive CLI ──

def _select_file(directory: str, extension: str, label: str) -> Optional[str]:
    """Muestra una lista de archivos en un directorio y permite elegir uno. Retorna None si el usuario sale."""
    if not os.path.isdir(directory):
        print(f"\n[WARN] El directorio '{directory}' no existe.")
        choice = input("  Ingresa la ruta manualmente (o Enter para salir): ").strip()
        return choice if choice else None
    
    files = sorted([
        f for f in os.listdir(directory)
        if f.endswith(extension) and not f.startswith(".")
    ])
    
    if not files:
        print(f"\n[WARN] No se encontraron archivos '{extension}' en '{directory}'.")
        choice = input("  Ingresa la ruta manualmente (o Enter para salir): ").strip()
        return choice if choice else None
    
    files = sorted([
        f for f in os.listdir(directory)
        if f.endswith(extension) and not f.startswith(".")
    ])
    
    if not files:
        print(f"\n[WARN] No se encontraron archivos '{extension}' en '{directory}'.")
        return input(f"  Ingresa la ruta manualmente: ").strip()
    
    print(f"\n{label}:")
    for i, fname in enumerate(files, 1):
        fpath = os.path.join(directory, fname)
        print(f"  [{i}] {fname}")
    print(f"  [0] Salir")
    
    while True:
        choice = input("  Selecciona un número: ").strip()
        if choice == "0":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return os.path.join(directory, files[idx])
        except ValueError:
            pass
        print("  Opción inválida. Intenta de nuevo.")


def interactive_mode(base_output: str) -> None:
    """CLI interactivo paso a paso para configurar y ejecutar el optimizador."""
    print("\n" + "=" * 60)
    print("   OPTIMIZADOR DE CV — MODO INTERACTIVO")
    print("=" * 60)
    
    # 1. Modelo
    print("\n📡 MODELO DE IA:")
    print("  [1] Gemini 2.5 Flash (Google)")
    print("  [2] DeepSeek V4 Pro (DeepSeek)")
    print("  [0] Salir")
    while True:
        model_choice = input("  Elige [1/2/0]: ").strip()
        if model_choice == "1":
            provider = "gemini"
            break
        elif model_choice == "2":
            provider = "deepseek"
            break
        elif model_choice == "0":
            print("Cancelado.")
            return
        print("  Opción inválida.")
    
    # 2. Perfil
    profile_path = _select_file("config", ".yaml", "👤 PERFIL")
    if profile_path is None:
        print("Cancelado.")
        return
    
    # 3. Oferta laboral
    job_path = _select_file("jobs", ".txt", "💼 OFERTA LABORAL")
    if job_path is None:
        print("Cancelado.")
        return
    
    # Si jobs/ no existe o el archivo no se encuentra, crear el directorio
    if not job_path or not os.path.exists(os.path.dirname(job_path)):
        os.makedirs("jobs", exist_ok=True)
        print("\n[INFO] Creado directorio 'jobs/'. Coloca ahí tus archivos .txt con ofertas laborales.")
        print("Cancelado. Vuelve a ejecutar tras agregar archivos.")
        return
    
    # 4. Idioma
    print("\n🌐 IDIOMA DE SALIDA:")
    print("  [1] Español")
    print("  [2] English")
    print("  [0] Salir")
    while True:
        lang_choice = input("  Elige [1/2/0]: ").strip()
        if lang_choice == "1":
            lang = "es"
            break
        elif lang_choice == "2":
            lang = "en"
            break
        elif lang_choice == "0":
            print("Cancelado.")
            return
        print("  Opción inválida.")
    
    # 5. Template
    template_path = _select_file("templates", ".html", "🎨 PLANTILLA HTML")
    if template_path is None:
        print("Cancelado.")
        return
    
    # 6. Confirmación
    job_dir = _job_output_dir(job_path)
    output_md = os.path.join(job_dir, os.path.basename(base_output))
    print("\n" + "=" * 60)
    print("   RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    print(f"  Modelo:      {provider}")
    print(f"  Perfil:      {profile_path}")
    print(f"  Oferta:      {job_path}")
    print(f"  Idioma:      {lang}")
    print(f"  Template:    {template_path}")
    print(f"  Output:      {output_md} (auto-versionado)")
    print()
    
    confirm = input("¿Proceder con la optimización? [s/n]: ").strip().lower()
    if confirm not in ("s", "si", "sí", "y", "yes"):
        print("Cancelado.")
        return
    
    # 7. Ejecutar pipeline
    _run_pipeline(profile_path, job_path, base_output, lang, template_path, provider)

    # 8. ¿Entrevista simulada?
    print()
    run_interview = input("¿Ejecutar entrevista simulada con Gemini? [s/n]: ").strip().lower()
    if run_interview in ("s", "si", "sí", "y", "yes"):
        _run_interview(profile_path, job_path, lang)

    # 9. ¿Auditoría de robustez?
    print()
    run_audit = input("¿Ejecutar auditoría de robustez sobre el CV generado? [s/n]: ").strip().lower()
    if run_audit in ("s", "si", "sí", "y", "yes"):
        _run_robustness(profile_path, job_path, lang, job_dir)


# ── Interview standalone ──

def _run_interview(profile_path: str, job_path: str, lang: str) -> None:
    """
    Ejecuta la entrevista simulada usando el perfil y la vacante,
    sin re-optimizar el CV.

    Args:
        profile_path: Ruta al YAML del perfil.
        job_path: Ruta al TXT de la vacante.
        lang: Idioma ('es' o 'en').
    """
    from services.mock_interview import MockInterviewService

    print("[INFO] Cargando perfil...")
    profile = load_profile(profile_path)
    print("[INFO] Cargando oferta...")
    job_description = load_job_description(job_path)

    interview = MockInterviewService(profile, job_description, lang)
    try:
        interview.run_interactive()
    except Exception as exc:
        print(f"\n[ERROR] Error inesperado en la entrevista: {exc}")
    finally:
        job_dir = _job_output_dir(job_path)
        transcript_path = os.path.join(job_dir, "interview_transcript.md")
        interview.export_transcript(transcript_path)


# ── Robustness standalone ──

def _run_robustness(profile_path: str, job_path: str, lang: str, job_dir: str) -> None:
    """
    Ejecuta la auditoría de robustez sobre el CV ya generado,
    sin re-optimizar. Lee el último CV .md de la carpeta del job.

    Args:
        profile_path: Ruta al YAML del perfil.
        job_path: Ruta al TXT de la vacante.
        lang: Idioma ('es' o 'en').
        job_dir: Carpeta de output del job.
    """
    from services.robustness_judge import RobustnessJudgeService

    # Buscar el último CV Markdown generado
    md_files = sorted([
        f for f in os.listdir(job_dir)
        if f.startswith("optimized_cv_v") and f.endswith(".md")
    ], reverse=True)

    if not md_files:
        print("[ERROR] No se encontró un CV optimizado en la carpeta del job.")
        print(f"  Buscado en: {job_dir}")
        return

    cv_path = os.path.join(job_dir, md_files[0])
    print(f"[INFO] Auditando: {md_files[0]}")

    with open(cv_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    print("[INFO] Cargando perfil...")
    profile = load_profile(profile_path)
    print("[INFO] Cargando oferta...")
    job_description = load_job_description(job_path)

    judge = RobustnessJudgeService(profile, job_description, lang)
    try:
        report = judge.run_validation(md_content)
        report_path = os.path.join(job_dir, "robustness_report.json")
        judge.export_report(report, report_path)
    except RuntimeError as exc:
        print(f"\n[ERROR] {exc}")


# ── Pipeline ──

def _job_slug(job_path: str) -> str:
    """Deriva un nombre limpio de carpeta a partir del archivo de oferta laboral."""
    basename = os.path.splitext(os.path.basename(job_path))[0]
    # Limpiar prefijos comunes
    basename = re.sub(r'^(job_description_|job_|oferta_)', '', basename)
    return f"job_{basename}"

def _job_output_dir(job_path: str) -> str:
    """Crea (si no existe) y devuelve la carpeta de output para un job específico."""
    slug = _job_slug(job_path)
    output_dir = os.path.join("output", slug)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def _run_pipeline(profile_path: str, job_path: str, output_base: str,
                  lang: str, template_path: str, provider: str,
                  run_mock_interview: bool = False,
                  run_robustness: bool = False) -> None:
    """Ejecuta el pipeline completo de optimización y guarda outputs versionados por job."""
    print("\n" + "=" * 60)
    print("   INICIANDO OPTIMIZACIÓN")
    print("=" * 60)
    
    # Derivar carpeta por job
    job_dir = _job_output_dir(job_path)
    output_md = os.path.join(job_dir, os.path.basename(output_base))
    output_html_base = os.path.splitext(output_md)[0] + ".html"
    
    print(f"[INFO] Output será guardado en: '{job_dir}/'")
    print(f"[INFO] Cargando perfil: '{profile_path}'...")
    profile = load_profile(profile_path)
    
    print(f"[INFO] Cargando oferta: '{job_path}'...")
    job_description = load_job_description(job_path)
    
    optimized_cv = optimize_cv(profile, job_description, lang, provider=provider)
    
    print("[INFO] Generando Markdown...")
    md_content = generate_markdown(optimized_cv, lang)
    
    print("[INFO] Generando HTML...")
    html_content = generate_html(optimized_cv, template_path, lang)
    
    md_final = save_markdown_versioned(md_content, output_md)
    html_final = save_html_versioned(html_content, output_html_base)

    print("[INFO] Generando DOCX (formato Harvard ATS)...")
    docx_base = os.path.splitext(output_md)[0] + ".docx"
    # generate_docx recibe contenido markdown y una ruta de salida
    docx_temp = os.path.join(job_dir, "_temp_cv.docx")
    docx_result = generate_docx(md_content, docx_temp)
    if docx_result:
        docx_final = save_docx_versioned(docx_temp, docx_base)
    else:
        docx_final = None
    
    print("=" * 60)
    print("   ¡OPTIMIZACIÓN COMPLETADA!")
    print(f"   Markdown: {md_final}")
    print(f"   HTML:     {html_final}")
    if docx_final:
        print(f"   DOCX:     {docx_final}")
    print("=" * 60)

    # ── Mock Interview ──
    if run_mock_interview:
        from services.mock_interview import MockInterviewService

        interview = MockInterviewService(profile, job_description, lang)
        interview.run_interactive()
        transcript_path = os.path.join(job_dir, "interview_transcript.md")
        interview.export_transcript(transcript_path)

    # ── Robustness Judge ──
    if run_robustness:
        from services.robustness_judge import RobustnessJudgeService

        judge = RobustnessJudgeService(profile, job_description, lang)
        report = judge.run_validation(md_content)
        report_path = os.path.join(job_dir, "robustness_report.json")
        judge.export_report(report, report_path)
    
    _print_checklist()


# ── Checklist ──

def _print_checklist() -> None:
    """Imprime el checklist pre-submission en consola."""
    print("\n[CHECKLIST] Revisa esto antes de enviar tu CV:")
    checks = [
        "¿Todas las fechas son correctas y usan formato consistente (MM/AAAA)?",
        "¿Los nombres de cargos e instituciones son exactos?",
        "¿Toda métrica o número es verificable (no inventado por la IA)?",
        "¿La información de contacto es correcta?",
        "¿Las secciones usan encabezados estándar (Habilidades, Experiencia, Educación)?",
        "¿Las keywords de la oferta aparecen en contexto, no solo en la lista de skills?",
        "¿El resumen profesional está en primera persona y suena natural al leerlo en voz alta?",
        "¿No hay frases genéricas de IA (spearheaded, results-driven, synergy, etc.)?",
        "¿Revisaste el CV línea por línea antes de enviarlo?"
    ]
    for i, check in enumerate(checks, 1):
        print(f"  [{i}] {check}")
    print()


# ── Entry point ──

def main() -> None:
    """Función de ejecución principal del optimizador."""
    args = parse_arguments()
    
    if args.interactive:
        interactive_mode(args.output)
        return

    # --interview-only: solo entrevista, sin re-optimizar CV
    if args.interview_only:
        if not args.job:
            print("\n[ERROR] --interview-only requiere el flag -j/--job.")
            print("Uso: python cv_optimizer.py -j jobs/oferta.txt --interview-only")
            sys.exit(1)
        _run_interview(args.profile, args.job, args.lang)
        return
    
    if not args.job:
        print("\n[ERROR] Se requiere el flag -j/--job o usar -i/--interactive.")
        print("Uso: python cv_optimizer.py -j jobs/oferta.txt [opciones]")
        print("     python cv_optimizer.py -i")
        sys.exit(1)
    
    _run_pipeline(args.profile, args.job, args.output,
                  args.lang, args.template, args.model,
                  run_mock_interview=args.mock_interview,
                  run_robustness=args.robustness)


if __name__ == "__main__":
    main()
