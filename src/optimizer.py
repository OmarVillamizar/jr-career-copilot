import os
import sys
import json
import yaml
from models import OptimizedCV

# ── Prompt builder (compartido entre proveedores) ──

def _build_prompt(profile: dict, job_description: str, lang: str) -> str:
    """
    Construye el prompt de optimización de CV con todas las reglas de oro.
    Compartido entre Gemini y DeepSeek.
    """
    language_name = "Spanish" if lang == "es" else "English"

    return (
        "You are an expert technical recruiter and career coach. "
        "Your job is to tailor a junior engineer's CV to match a specific job description. "
        "\n\n"
        "--- PYGMALION EFFECT (FOUNDATIONAL) ---\n"
        "Apply the Pygmalion Effect: frame the candidate's achievements, projects, and academic background in "
        "an empowering light that emphasizes their technical growth, problem-solving ability, and high potential. "
        "The goal is to make a junior profile read as someone ready to contribute — not as someone overstating.\n"
        "\n"
        "--- BULLET FORMULA ---\n"
        "For every bullet point (achievements, tailored_achievements, project achievements), use this structure:\n"
        "[Action Verb] + [Task/Project] + [Quantifiable Result — only if data exists in profile] + [Context/Scale]\n"
        "Example: 'Developed a questionnaire management app with full SDLC ownership, presented at a departmental research conference (RedCOLSI).'\n"
        "\n"
        "--- CRITICAL: FIRST PERSON & NATURAL TONE ---\n"
        "1. The professional summary MUST be written in FIRST PERSON (e.g., 'I am a systems engineering student...', "
        "'My experience includes...', 'I have worked with...'). Never refer to the candidate in third person.\n"
        "2. Use natural, conversational language. Read each sentence aloud — if it sounds like a robot, rewrite it.\n"
        "3. NEVER use buzzwords: 'spearheaded', 'results-driven', 'synergy', 'proven track record', 'seasoned', "
        "'game-changer', 'rockstar', 'ninja', 'deep dive', 'leverage', 'utilize' (use 'use').\n"
        "4. Vary sentence structure. Avoid starting every bullet with the same verb.\n"
        "\n"
        "--- LANGUAGE RULE ---\n"
        f"The output language is '{language_name}' (code: {lang}).\n"
        f"ALL text fields MUST be in '{language_name}'. Translate naturally, not literally.\n"
        "\n"
        "--- SAFETY RULES (TRUTHFULNESS) ---\n"
        "1. NEVER invent achievements, jobs, degrees, certifications, dates, or grades. "
        "Only use what exists in the YAML profile.\n"
        "2. You may rephrase, reorder, and restructure existing bullet points to highlight relevance, "
        "but the core facts must remain 100% truthful.\n"
        "3. Prioritize and reorder skills based on the job description. Only include skills the candidate actually has.\n"
        "4. Include numbers and concrete details only when they exist in the profile. Never fabricate metrics.\n"
        "\n"
        "--- JOB DESCRIPTION MIRRORING ---\n"
        "Reflect the language of the job description. If the posting says 'REST APIs', use 'REST APIs', not just 'APIs'. "
        "Include both acronyms and full forms (e.g., 'Search Engine Optimization (SEO)').\n"
        "\n"
        f"JUNIOR ENGINEER PROFILE (YAML):\n{yaml.dump(profile, allow_unicode=True)}\n\n"
        f"TARGET JOB DESCRIPTION:\n{job_description}\n"
    )


# ── Gemini provider ──

def _call_gemini(prompt: str, language_name: str) -> OptimizedCV:
    """
    Llama a Gemini 2.5 Flash con schema Pydantic y devuelve CV validado.
    """
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[ERROR] La variable de entorno GEMINI_API_KEY no está configurada.")
        print("Para solucionarlo:")
        print("  1. Consigue una clave de API gratuita en Google AI Studio (https://aistudio.google.com/).")
        print("  2. Agrega la línea al archivo '.env': GEMINI_API_KEY=tu_clave")
        sys.exit(1)

    print(f"[INFO] Comunicándose con Gemini 2.5 Flash (Idioma: {language_name})...")

    try:
        client = genai.Client()
    except Exception as exc:
        print("\n[ERROR] Falló la inicialización del cliente de Google GenAI:")
        print(exc)
        sys.exit(1)

    try:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OptimizedCV,
            temperature=0.7,
            system_instruction=(
                "You are a senior career coach for engineers. You rewrite junior CVs to match job descriptions, "
                "keeping a natural human tone and never fabricating data."
            )
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        if not response.text:
            raise ValueError("Gemini devolvió una respuesta vacía.")

        cv = OptimizedCV.model_validate_json(response.text)
        print("[INFO] Optimización completada (Gemini 2.5 Flash).")
        return cv

    except Exception as exc:
        print("\n[ERROR] Fallo en la llamada o validación con Gemini:")
        print(exc)
        print("\nConsejo: Verifica tu conexión, API Key y límites de cuota.")
        sys.exit(1)


# ── DeepSeek provider ──

def _call_deepseek(prompt: str, language_name: str) -> OptimizedCV:
    """
    Llama a DeepSeek V4 Pro (API compatible con OpenAI) y devuelve CV validado.
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("\n[ERROR] El paquete 'openai' no está instalado.")
        print("Ejecuta: pip install openai")
        sys.exit(1)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("\n[ERROR] La variable de entorno DEEPSEEK_API_KEY no está configurada.")
        print("Para solucionarlo:")
        print("  1. Consigue una clave de API en https://platform.deepseek.com/api_keys")
        print("  2. Agrega la línea al archivo '.env': DEEPSEEK_API_KEY=tu_clave")
        sys.exit(1)

    print(f"[INFO] Comunicándose con DeepSeek V4 Pro (Idioma: {language_name})...")

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

        schema_json = json.dumps(OptimizedCV.model_json_schema(), ensure_ascii=False, indent=2)

        system_msg = (
            "You are a senior career coach for engineers. You rewrite junior CVs to match job descriptions, "
            "keeping a natural human tone and never fabricating data. "
            "CRITICAL: You MUST respond with a SINGLE valid JSON object that matches the schema below EXACTLY. "
            "Do NOT omit any required fields. Do NOT wrap the JSON in markdown or extra text. "
            "Output ONLY the raw JSON.\n\n"
            f"REQUIRED JSON SCHEMA:\n{schema_json}"
        )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        raw_json = response.choices[0].message.content
        if not raw_json:
            raise ValueError("DeepSeek devolvió una respuesta vacía.")

        cv = OptimizedCV.model_validate_json(raw_json)
        print("[INFO] Optimización completada (DeepSeek V4 Pro).")
        return cv

    except Exception as exc:
        print("\n[ERROR] Fallo en la llamada o validación con DeepSeek:")
        print(exc)
        print("\nConsejo: Verifica tu conexión, API Key y saldo en https://platform.deepseek.com/")
        sys.exit(1)


# ── Public API ──

def optimize_cv(profile: dict, job_description: str, lang: str = "es",
                provider: str = "gemini") -> OptimizedCV:
    """
    Optimiza el CV del ingeniero junior usando el proveedor de IA especificado.

    Args:
        profile (dict): Datos del perfil del ingeniero junior cargados del YAML.
        job_description (str): Descripción del empleo objetivo.
        lang (str): Idioma de salida ('es' o 'en').
        provider (str): Proveedor de IA a usar: 'gemini' (default) o 'deepseek'.

    Returns:
        OptimizedCV: Objeto Pydantic estructurado y validado con el CV optimizado.
    """
    language_name = "Spanish" if lang == "es" else "English"
    prompt = _build_prompt(profile, job_description, lang)

    if provider == "deepseek":
        return _call_deepseek(prompt, language_name)
    elif provider == "gemini":
        return _call_gemini(prompt, language_name)
    else:
        print(f"\n[ERROR] Proveedor desconocido: '{provider}'. Use 'gemini' o 'deepseek'.")
        sys.exit(1)
