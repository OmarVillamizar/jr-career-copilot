"""
Mock Interview Service — Simulador interactivo de entrevista técnica.

Soporta Gemini 2.5 Flash y DeepSeek V4 Pro. Actúa como reclutador
técnico, hace preguntas contextuales basadas en el CV del candidato
y la descripción de la vacante. Máximo 7 preguntas, luego feedback.
"""

import os
from datetime import datetime
from typing import Any, Literal, cast

import yaml

from google import genai
from google.genai import types
from openai import OpenAI


class MockInterviewService:
    """
    Servicio de entrevista técnica simulada con IA.

    Usa multi-turn chat con Gemini 2.5 Flash o DeepSeek V4 Pro.
    El entrevistador solo pregunta sobre tecnologías presentes en
    el CV del candidato y en la descripción del puesto. Tras 7
    preguntas, proporciona feedback constructivo.

    Atributos:
        profile (dict): Perfil YAML del candidato.
        job_description (str): Descripción de la vacante.
        lang (str): Idioma ('es' o 'en').
        provider (str): 'gemini' o 'deepseek'.
        message_history (list): Historial multi-turn para el chat.
        transcript_entries (list): Preguntas y respuestas para exportar.
        candidate_name (str): Nombre completo del candidato.
    """

    MAX_QUESTIONS = 7
    Provider = Literal["gemini", "deepseek"]

    def __init__(
        self,
        profile: dict,
        job_description: str,
        lang: str = "es",
        provider: Provider = "gemini",
    ) -> None:
        """
        Inicializa el servicio de entrevista.

        Args:
            profile: Perfil YAML del candidato.
            job_description: Texto completo de la vacante.
            lang: Idioma de la entrevista ('es' o 'en').
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
            try:
                from openai import OpenAI
            except ImportError:
                raise RuntimeError("El paquete 'openai' no está instalado. Ejecuta: pip install openai")
            self._openai_client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
            self._gemini_client = None
        else:
            raise RuntimeError(f"Proveedor desconocido: '{provider}'. Use 'gemini' o 'deepseek'.")

        self.message_history: list[dict[str, Any]] = []
        self.transcript_entries: list[dict[str, str]] = []
        self.candidate_name = profile.get("personal_info", {}).get("full_name", "Candidato")

    # ── System Instruction ──

    def _build_system_instruction(self) -> str:
        """
        Construye la instrucción de sistema para el entrevistador IA.

        Incluye el perfil del candidato, la vacante, y las reglas
        de la entrevista (límite de preguntas, temas permitidos,
        tono, feedback). Compartido entre Gemini y DeepSeek.

        Returns:
            str: System instruction.
        """
        profile_yaml = yaml.dump(self.profile, allow_unicode=True, indent=2)

        if self.lang == "es":
            return (
                "Eres un reclutador técnico experimentado realizando una entrevista a un "
                "candidato junior. Tu objetivo es evaluar sus conocimientos técnicos de "
                "forma justa y constructiva.\n\n"
                "--- REGLAS DE LA ENTREVISTA ---\n"
                "1. SOLO pregunta sobre tecnologías, herramientas y proyectos que aparezcan "
                "en el perfil del candidato Y en la descripción de la vacante. No preguntes "
                "sobre tecnologías que el candidato no conoce.\n"
                "2. Si el candidato NO tiene experiencia laboral (experiences vacío), NO "
                "preguntes 'cuéntame de tu último trabajo' ni 'describe tu experiencia en X empresa'. "
                "Enfócate en proyectos académicos, personales y formación.\n"
                "3. Haz EXACTAMENTE 7 preguntas. Después de que el candidato responda la "
                "séptima pregunta, NO hagas más preguntas — espera a que se te solicite el feedback.\n"
                "4. Progresión: empieza con preguntas generales (background, formación), luego "
                "profundiza en tecnologías específicas de la vacante, y termina con un escenario "
                "práctico o pregunta situacional.\n"
                "5. Tono: profesional pero cálido. Sin tecnicismos innecesarios. Haz que el "
                "candidato se sienta cómodo.\n"
                "6. Cada pregunta debe ser concisa (2-3 oraciones máximo). Incluye brevemente "
                "por qué es relevante para el puesto.\n"
                "7. NO repitas preguntas que ya hayas hecho antes.\n"
                "8. NUNCA reveles que eres una IA. Actúa como un reclutador humano real.\n\n"
                "--- PERFIL DEL CANDIDATO ---\n"
                f"{profile_yaml}\n\n"
                "--- DESCRIPCIÓN DE LA VACANTE ---\n"
                f"{self.job_description}\n\n"
                "--- INSTRUCCIÓN FINAL ---\n"
                "Comienza la entrevista presentándote brevemente como reclutador de la empresa "
                "y haz la PRIMERA pregunta. No des feedback hasta que se te solicite explícitamente "
                "después de la séptima respuesta."
            )
        else:
            return (
                "You are an experienced technical recruiter conducting an interview with a "
                "junior candidate. Your goal is to fairly and constructively assess their "
                "technical knowledge.\n\n"
                "--- INTERVIEW RULES ---\n"
                "1. ONLY ask about technologies, tools, and projects that appear in the "
                "candidate's profile AND the job description. Do not ask about technologies "
                "the candidate doesn't know.\n"
                "2. If the candidate has NO work experience (experiences is empty), do NOT "
                "ask 'tell me about your last job'. Focus on academic, personal projects, "
                "and education.\n"
                "3. Ask EXACTLY 7 questions. After the candidate answers the 7th question, "
                "do NOT ask more — wait for explicit feedback request.\n"
                "4. Progression: start general (background, education), then dive into "
                "specific job technologies, and end with a practical scenario.\n"
                "5. Tone: professional but warm. No unnecessary jargon. Make the candidate "
                "feel comfortable.\n"
                "6. Each question should be concise (2-3 sentences max). Briefly state why "
                "it's relevant to the role.\n"
                "7. Do NOT repeat questions you've already asked.\n"
                "8. NEVER reveal you are an AI. Act like a real human recruiter.\n\n"
                "--- CANDIDATE PROFILE ---\n"
                f"{profile_yaml}\n\n"
                "--- JOB DESCRIPTION ---\n"
                f"{self.job_description}\n\n"
                "--- FINAL INSTRUCTION ---\n"
                "Start the interview by briefly introducing yourself as the company's recruiter "
                "and ask the FIRST question. Do not provide feedback until explicitly requested "
                "after the 7th answer."
            )

    # ── Model call (provider dispatch) ──

    def _call_model(self) -> str:
        """
        Llama al modelo configurado (Gemini o DeepSeek) con el historial
        acumulado y devuelve la respuesta.

        Returns:
            str: Texto de respuesta del modelo.

        Raises:
            RuntimeError: Si la API falla o devuelve vacío.
        """
        if self.provider == "gemini":
            return self._call_gemini()
        else:
            return self._call_deepseek()

    def _call_gemini(self) -> str:
        """Llama a Gemini 2.5 Flash con multi-turn chat."""
        try:
            config = types.GenerateContentConfig(
                system_instruction=self._build_system_instruction(),
                temperature=0.8,
            )
            response = self._gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=self.message_history,
                config=config,
            )
            if not response.text:
                raise ValueError("Gemini devolvió una respuesta vacía.")
            return response.text
        except Exception as exc:
            raise RuntimeError(f"Falló la comunicación con Gemini: {exc}") from exc

    def _call_deepseek(self) -> str:
        """Llama a DeepSeek V4 Pro con multi-turn chat (API OpenAI-compatible)."""
        try:
            system_instruction = self._build_system_instruction()
            openai_messages = [{"role": "system", "content": system_instruction}]

            for msg in self.message_history:
                role = "assistant" if msg["role"] == "model" else "user"
                text = msg["parts"][0]["text"]
                openai_messages.append({"role": role, "content": text})

            response = self._openai_client.chat.completions.create(
                model="deepseek-chat",
                messages=openai_messages,
                temperature=0.8,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("DeepSeek devolvió una respuesta vacía.")
            return content
        except Exception as exc:
            raise RuntimeError(f"Falló la comunicación con DeepSeek: {exc}") from exc

    # ── Interactive Loop ──

    def run_interactive(self) -> None:
        """
        Ejecuta el loop interactivo de la entrevista en consola.

        Flujo:
        1. Inicia la entrevista con un kickoff message.
        2. Loop de 7 preguntas: reclutador pregunta → candidato responde.
        3. Solicita feedback final al modelo.
        4. Muestra feedback en consola.
        """
        print("\n" + "=" * 60)
        print("   ENTREVISTA TÉCNICA SIMULADA")
        print("=" * 60)
        print(f"\nCandidato: {self.candidate_name}")
        print(f"Modelo: {'Gemini 2.5 Flash' if self.provider == 'gemini' else 'DeepSeek V4 Pro'}")
        print(f"Preguntas máximas: {self.MAX_QUESTIONS}")
        print("Presiona Ctrl+C en cualquier momento para salir.\n")

        # Kickoff: primer mensaje del usuario para iniciar la entrevista
        kickoff = (
            "Inicia la entrevista. Preséntate brevemente como reclutador "
            "y haz la primera pregunta."
        )
        self.message_history.append(
            {"role": "user", "parts": [{"text": kickoff}]}
        )

        try:
            # ── Ronda de preguntas ──
            for question_num in range(1, self.MAX_QUESTIONS + 1):
                try:
                    model_text = self._call_model()
                except RuntimeError as exc:
                    print(f"\n[ERROR] {exc}")
                    print("[INFO] La transcripción parcial se guardará de todos modos.")
                    self._feedback_text = f"(Entrevista interrumpida por error de API en pregunta {question_num})"
                    break

                self.message_history.append(
                    {"role": "model", "parts": [{"text": model_text}]}
                )

                print(f"--- Pregunta {question_num}/{self.MAX_QUESTIONS} ---")
                print(f"\n🤖 Reclutador: {model_text}\n")

                user_answer = input("👤 Tú: ").strip()
                if not user_answer:
                    user_answer = "(sin respuesta)"

                self.message_history.append(
                    {"role": "user", "parts": [{"text": user_answer}]}
                )

                self.transcript_entries.append({
                    "num": str(question_num),
                    "question": model_text,
                    "answer": user_answer,
                })

            # ── Feedback ──
            if not hasattr(self, '_feedback_text'):
                feedback_prompt = (
                    "El candidato ha respondido las 7 preguntas. Ahora proporciona "
                    "tu FEEDBACK FINAL. Incluye: 1) Fortalezas del candidato, "
                    "2) Áreas de mejora, 3) Recomendaciones para futuras entrevistas, "
                    "4) Impresión general. Sé constructivo y específico. "
                    "NO hagas más preguntas."
                )
                self.message_history.append(
                    {"role": "user", "parts": [{"text": feedback_prompt}]}
                )

                try:
                    feedback_text = self._call_model()
                    self.message_history.append(
                        {"role": "model", "parts": [{"text": feedback_text}]}
                    )

                    print("\n" + "=" * 60)
                    print("   FEEDBACK DEL RECLUTADOR")
                    print("=" * 60)
                    print(f"\n{feedback_text}\n")

                    self.transcript_entries.append({
                        "num": "feedback",
                        "question": "",
                        "answer": "",
                    })
                    self._feedback_text = feedback_text
                except RuntimeError as exc:
                    print(f"\n[ERROR] {exc}")
                    self._feedback_text = "(No se pudo generar feedback por error de API)"

        except KeyboardInterrupt:
            print("\n\n[INFO] Entrevista interrumpida por el usuario.")
            self._feedback_text = "(Entrevista interrumpida antes del feedback)"

        print("=" * 60)
        print("   ENTREVISTA FINALIZADA")
        print("=" * 60)

    # ── Export ──

    def export_transcript(self, output_path: str) -> str:
        """
        Exporta la transcripción completa de la entrevista a Markdown.

        Args:
            output_path: Ruta del archivo .md de salida.

        Returns:
            str: Ruta donde se guardó el archivo.
        """
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        today = datetime.now().strftime("%d/%m/%Y")
        total = len([e for e in self.transcript_entries if e["num"] != "feedback"])
        feedback = getattr(self, "_feedback_text", "(No disponible)")

        lines = [
            f"# Transcripción de Entrevista Técnica",
            "",
            f"**Candidato:** {self.candidate_name}",
            f"**Modelo:** {'Gemini 2.5 Flash' if self.provider == 'gemini' else 'DeepSeek V4 Pro'}",
            f"**Preguntas realizadas:** {total}/{self.MAX_QUESTIONS}",
            f"**Fecha:** {today}",
            "",
            "---",
            "",
        ]

        for entry in self.transcript_entries:
            if entry["num"] == "feedback":
                continue
            lines.append(f"## Pregunta {entry['num']}")
            lines.append("")
            lines.append(f"**Reclutador:** {entry['question']}")
            lines.append("")
            lines.append(f"**Candidato:** {entry['answer']}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## Feedback del Reclutador",
            "",
            feedback,
            "",
        ])

        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[INFO] Transcripción guardada en: '{output_path}'")
        return output_path
