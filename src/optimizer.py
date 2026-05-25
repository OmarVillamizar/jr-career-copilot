import os
import sys
import yaml
from google import genai
from google.genai import types
from models import OptimizedCV

def optimize_cv(profile: dict, job_description: str, lang: str = "es") -> OptimizedCV:
    """
    Se conecta con la API de Gemini 2.5 Flash para optimizar el CV del ingeniero junior
    basándose en la descripción del empleo utilizando la SDK oficial de google-genai.
    
    Args:
        profile (dict): Datos del perfil del ingeniero junior cargados del YAML.
        job_description (str): Descripción del empleo objetivo.
        lang (str): Idioma de salida para los campos del currículum ('es' o 'en').
        
    Returns:
        OptimizedCV: Objeto Pydantic estructurado y validado con el currículum optimizado.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[ERROR] La variable de entorno GEMINI_API_KEY no está configurada.")
        print("Para solucionar esto:")
        print("  1. Consigue una clave de API gratuita en Google AI Studio (https://aistudio.google.com/).")
        print("  2. Crea un archivo llamado '.env' en la raíz del proyecto.")
        print("  3. Agrega la siguiente línea al archivo '.env':")
        print("     GEMINI_API_KEY=tu_clave_de_api_secreta_aqui")
        print("  4. Alternativamente, puedes exportarla en tu terminal:")
        print("     export GEMINI_API_KEY=\"tu_clave_de_api_secreta_aqui\"")
        sys.exit(1)

    print("\n[INFO] Inicializando cliente de Google GenAI...")
    try:
        client = genai.Client()
    except Exception as exc:
        print("\n[ERROR] Falló la inicialización del cliente de Google GenAI:")
        print(exc)
        sys.exit(1)

    # Mapeo descriptivo del idioma de destino para el prompt
    language_name = "Spanish" if lang == "es" else "English"

    # Prompt: Efecto Pigmalión como base (altas expectativas -> alto rendimiento),
    # pero con restricciones de tono natural, primera persona y sin buzzwords.
    prompt = (
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

    print(f"[INFO] Comunicándose con Gemini 2.5 Flash para optimizar el CV (Idioma de salida: {language_name})...")
    
    try:
        # Configurar la llamada estructurada con el esquema Pydantic
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OptimizedCV,
            temperature=0.7,  # Mayor naturalidad en redacción; schema Pydantic previene alucinaciones
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
        
        # Validar la respuesta con el esquema Pydantic
        if not response.text:
            raise ValueError("Gemini devolvió una respuesta vacía.")
            
        optimized_cv = OptimizedCV.model_validate_json(response.text)
        print("[INFO] Optimización completada con éxito por la Inteligencia Artificial.")
        return optimized_cv

    except Exception as exc:
        print("\n[ERROR] Ocurrió un fallo en la llamada o validación con la API de Gemini:")
        print(exc)
        print("\nConsejo: Verifica tu conexión a internet, comprueba que tu API Key sea correcta y que no ")
        print("hayas excedido los límites de cuota (Rate Limits) del modelo gemini-2.5-flash.")
        sys.exit(1)
