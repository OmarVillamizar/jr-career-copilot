"""
Robustness Judge Service — Validador LLM-as-a-Judge para CV generados.

Audita el CV optimizado contra el perfil YAML original (fuente de verdad)
para detectar alucinaciones, inconsistencias y violaciones éticas.
Soporta Gemini 2.5 Flash y DeepSeek V4 Pro con Structured Outputs.
"""

import json
import os
from typing import Literal

import yaml

from google import genai
from google.genai import types
from openai import OpenAI

from models import ReporteRobustez


class RobustnessJudgeService:
    """
    Servicio de auditoría de robustez para CV generados por IA.

    Compara el CV generado (Markdown) contra el perfil YAML original
    del candidato para detectar datos inventados, métricas falsas,
    cargos inflados y otras violaciones de veracidad.

    Atributos:
        profile (dict): Perfil YAML original del candidato (fuente de verdad).
        job_description (str): Descripción de la vacante (contexto).
        lang (str): Idioma ('es' o 'en').
        provider (str): 'gemini' o 'deepseek'.
    """

    Provider = Literal["gemini", "deepseek"]

    def __init__(
        self,
        profile: dict,
        job_description: str,
        lang: str = "es",
        provider: Provider = "gemini",
    ) -> None:
        """
        Inicializa el servicio de auditoría.

        Args:
            profile: Perfil YAML del candidato (fuente de verdad).
            job_description: Texto completo de la vacante.
            lang: Idioma del reporte ('es' o 'en').
            provider: Modelo a usar: 'gemini' o 'deepseek'.
        """
        self.profile = profile
        self.job_description = job_description
        self.lang = lang
        self.provider = provider

        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY no configurada en .env")
            self._gemini_client = genai.Client()
            self._openai_client = None
        elif provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise RuntimeError("DEEPSEEK_API_KEY no configurada en .env")
            self._openai_client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            self._gemini_client = None
        else:
            raise RuntimeError(f"Proveedor desconocido: '{provider}'. Use 'gemini' o 'deepseek'.")

    # ── Prompt ──

    def _build_audit_prompt(self, markdown_cv: str) -> str:
        """
        Construye el prompt de auditoría con el CV a evaluar y la fuente de verdad.

        Incluye:
        - Perfil YAML original (fuente de verdad)
        - CV generado en Markdown (a auditar)
        - Descripción de la vacante (contexto)
        - Instrucciones precisas de auditoría

        Args:
            markdown_cv: Contenido Markdown del CV generado a auditar.

        Returns:
            str: Prompt completo para el modelo.
        """
        profile_yaml = yaml.dump(self.profile, allow_unicode=True, indent=2)

        if self.lang == "es":
            return (
                "Eres un auditor de calidad especializado en verificar la veracidad de "
                "currículums generados por IA. Tu trabajo es comparar un CV generado contra "
                "el perfil original del candidato (fuente de verdad) y detectar cualquier "
                "dato falso, inventado o exagerado.\n\n"
                "--- REGLAS DE AUDITORÍA ---\n"
                "1. COMPARA el CV generado (Markdown) contra el perfil YAML original. "
                "El perfil YAML es la ÚNICA fuente de verdad. Todo lo que no esté en el "
                "perfil es sospechoso.\n"
                "2. NO penalices reformulaciones legítimas. Si el CV dice 'Desarrollé una API REST' "
                "y el perfil dice 'API REST' en proyectos, NO es alucinación — es redacción.\n"
                "3. SÍ penaliza:\n"
                "   - Datos numéricos inventados (métricas, porcentajes, cantidades no respaldadas)\n"
                "   - Cargos o títulos inflados (ej. 'Líder de equipo' cuando el perfil dice 'miembro')\n"
                "   - Tecnologías añadidas que no están en el perfil\n"
                "   - Fechas o períodos alterados\n"
                "   - Logros fabricados (ej. 'Aumenté las ventas un 30%' sin respaldo)\n"
                "4. Para cada alucinación detectada, asigna severidad:\n"
                "   - 'baja': reformulación menor sin impacto real (no contar como alucinación grave)\n"
                "   - 'media': afirmación no verificable o métrica sin respaldo\n"
                "   - 'alta': dato completamente fabricado (tecnología, cargo, logro inexistente)\n"
                "5. El score_honestidad debe reflejar la proporción de contenido veraz:\n"
                "   - 95-100: CV totalmente veraz, solo reformulaciones legítimas\n"
                "   - 80-94: Alguna exageración menor sin datos falsos graves\n"
                "   - 60-79: Múltiples datos no verificables o una alucinación media\n"
                "   - 40-59: Al menos una alucinación alta o varias medias\n"
                "   - 0-39: Múltiples alucinaciones altas, CV no confiable\n"
                "6. El comentario_auditor debe ser CONSTRUCTIVO y ESPECÍFICO. Explica qué "
                "está bien, qué está mal, y cómo mejorarlo. No uses frases genéricas.\n"
                "7. La descripción de la vacante es SOLO contexto. No evalúes si el CV "
                "encaja con la vacante — solo evalúa veracidad contra el perfil.\n"
                "8. Si no encuentras ninguna alucinación, devuelve lista vacía y "
                "score_honestidad alto (95-100).\n\n"
                "--- PERFIL ORIGINAL DEL CANDIDATO (FUENTE DE VERDAD) ---\n"
                f"{profile_yaml}\n\n"
                "--- DESCRIPCIÓN DE LA VACANTE (CONTEXTO) ---\n"
                f"{self.job_description}\n\n"
                "--- CV GENERADO A AUDITAR ---\n"
                f"{markdown_cv}\n\n"
                "--- INSTRUCCIÓN FINAL ---\n"
                "Audita el CV generado. Responde ÚNICAMENTE con el JSON estructurado "
                "según el schema. Sé preciso, justo y específico."
            )
        else:
            return (
                "You are a quality auditor specialized in verifying the truthfulness of "
                "AI-generated resumes. Your job is to compare a generated CV against the "
                "candidate's original profile (source of truth) and detect any false, "
                "invented, or exaggerated data.\n\n"
                "--- AUDIT RULES ---\n"
                "1. COMPARE the generated CV (Markdown) against the original YAML profile. "
                "The YAML profile is the ONLY source of truth. Anything not in the profile "
                "is suspicious.\n"
                "2. Do NOT penalize legitimate rephrasing. If the CV says 'Developed a REST API' "
                "and the profile mentions 'REST API' in projects, that is NOT a hallucination.\n"
                "3. DO penalize:\n"
                "   - Invented numeric data (metrics, percentages, unbacked quantities)\n"
                "   - Inflated titles (e.g., 'Team Lead' when profile says 'member')\n"
                "   - Added technologies not in the profile\n"
                "   - Altered dates or periods\n"
                "   - Fabricated achievements (e.g., 'Increased sales by 30%' without backup)\n"
                "4. For each detected hallucination, assign severity:\n"
                "   - 'baja' (low): minor rephrasing with no real impact\n"
                "   - 'media' (medium): unverifiable claim or metric without backup\n"
                "   - 'alta' (high): completely fabricated data (technology, role, achievement)\n"
                "5. The honesty score should reflect the proportion of truthful content:\n"
                "   - 95-100: Fully truthful CV, only legitimate rephrasing\n"
                "   - 80-94: Minor exaggeration, no serious false data\n"
                "   - 60-79: Multiple unverifiable claims or one medium hallucination\n"
                "   - 40-59: At least one high hallucination or several medium ones\n"
                "   - 0-39: Multiple high hallucinations, unreliable CV\n"
                "6. The auditor commentary must be CONSTRUCTIVE and SPECIFIC. Explain what's "
                "good, what's wrong, and how to improve. No generic phrases.\n"
                "7. The job description is ONLY context. Do not evaluate whether the CV "
                "fits the job — only evaluate truthfulness against the profile.\n"
                "8. If no hallucinations are found, return an empty list and a high "
                "honesty score (95-100).\n\n"
                "--- ORIGINAL CANDIDATE PROFILE (SOURCE OF TRUTH) ---\n"
                f"{profile_yaml}\n\n"
                "--- JOB DESCRIPTION (CONTEXT) ---\n"
                f"{self.job_description}\n\n"
                "--- GENERATED CV TO AUDIT ---\n"
                f"{markdown_cv}\n\n"
                "--- FINAL INSTRUCTION ---\n"
                "Audit the generated CV. Respond ONLY with the structured JSON "
                "according to the schema. Be precise, fair, and specific."
            )

    # ── Validation ──

    def run_validation(self, markdown_cv: str) -> ReporteRobustez:
        """
        Ejecuta la auditoría completa del CV generado.

        Usa Gemini con response_schema o DeepSeek con response_format
        JSON mode + schema en system prompt.

        Args:
            markdown_cv: Contenido Markdown del CV generado a auditar.

        Returns:
            ReporteRobustez: Reporte estructurado con score, alucinaciones y comentario.

        Raises:
            RuntimeError: Si la API falla o la respuesta no es válida.
        """
        prompt = self._build_audit_prompt(markdown_cv)
        language_name = "Spanish" if self.lang == "es" else "English"
        model_label = "Gemini 2.5 Flash" if self.provider == "gemini" else "DeepSeek V4 Pro"

        print(f"[INFO] Auditando CV con {model_label} (Idioma: {language_name})...")

        if self.provider == "gemini":
            return self._validate_gemini(prompt)
        else:
            return self._validate_deepseek(prompt)

    def _validate_gemini(self, prompt: str) -> ReporteRobustez:
        """Audita usando Gemini 2.5 Flash con response_schema Pydantic."""
        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReporteRobustez,
                temperature=0.3,
                system_instruction=(
                    "You are a precision auditor. Your only job is to compare two documents "
                    "and detect factual discrepancies. Be conservative: only flag data that is "
                    "clearly absent from the source profile. Do not flag rephrasing as hallucination. "
                    "Respond ONLY with valid JSON matching the schema."
                ),
            )
            response = self._gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            if not response.text:
                raise ValueError("Gemini devolvió una respuesta vacía.")

            report = ReporteRobustez.model_validate_json(response.text)
            print(f"[INFO] Auditoría completada. Score de honestidad: {report.score_honestidad}/100")
            return report
        except Exception as exc:
            raise RuntimeError(f"Falló la auditoría con Gemini: {exc}") from exc

    def _validate_deepseek(self, prompt: str) -> ReporteRobustez:
        """Audita usando DeepSeek V4 Pro con JSON mode + schema en system prompt."""
        try:
            schema_json = json.dumps(
                ReporteRobustez.model_json_schema(), ensure_ascii=False, indent=2
            )

            system_msg = (
                "You are a precision auditor. Your only job is to compare two documents "
                "and detect factual discrepancies. Be conservative: only flag data that is "
                "clearly absent from the source profile. Do not flag rephrasing as hallucination.\n\n"
                "CRITICAL: You MUST respond with a SINGLE valid JSON object that matches "
                "the schema below EXACTLY. Do NOT omit any required fields. Do NOT wrap "
                "the JSON in markdown or extra text. Output ONLY the raw JSON.\n\n"
                f"REQUIRED JSON SCHEMA:\n{schema_json}"
            )

            response = self._openai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            raw_json = response.choices[0].message.content
            if not raw_json:
                raise ValueError("DeepSeek devolvió una respuesta vacía.")

            # Limpiar markdown fences si DeepSeek envolvió el JSON
            raw_json = raw_json.strip()
            if raw_json.startswith("```"):
                raw_json = raw_json.split("\n", 1)[-1]  # quitar ```json o ```
                if raw_json.endswith("```"):
                    raw_json = raw_json.rsplit("\n", 1)[0]  # quitar ``` final
                raw_json = raw_json.strip()

            report = ReporteRobustez.model_validate_json(raw_json)
            print(f"[INFO] Auditoría completada. Score de honestidad: {report.score_honestidad}/100")
            return report
        except Exception as exc:
            raise RuntimeError(f"Falló la auditoría con DeepSeek: {exc}") from exc

    # ── Export ──

    def export_report(self, report: ReporteRobustez, output_path: str) -> str:
        """
        Exporta el reporte de robustez a un archivo JSON.

        Args:
            report: Reporte de robustez validado.
            output_path: Ruta del archivo .json de salida.

        Returns:
            str: Ruta donde se guardó el archivo.
        """
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        json_str = report.model_dump_json(indent=2, ensure_ascii=False)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)

        print(f"[INFO] Reporte de robustez guardado en: '{output_path}'")
        return output_path
