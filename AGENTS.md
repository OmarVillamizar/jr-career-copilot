# AGENTS.md — jr-career-copilot

> Proyecto: Optimizador de CV para ingenieros junior.
> Estudiante: Omar Villamizar — Código 1152239.
> Stack: Python + Gemini 2.5 Flash + DeepSeek V4 Pro + Pydantic + Jinja2.

## Reglas de oro del CV

1. **Primera persona siempre** — El resumen profesional habla como si el candidato se presentara a sí mismo ("Soy estudiante de...", "Mi experiencia incluye..."). Nunca en tercera persona.
2. **Tono humano, no de IA** — Lenguaje natural, conversacional. Si suena a robot, reescribir. Prohibido: *spearheaded*, *results-driven*, *synergy*, *proven track record*, *seasoned*, *game-changer*.
3. **Pygmalion responsable** — Enmarcar logros con altas expectativas y potencial, pero sin inflar ni inventar. El junior debe sonar listo para contribuir, no como un senior disfrazado.
4. **Veracidad absoluta** — Nunca fabricar logros, fechas, métricas o cargos que no estén en el perfil YAML original.
5. **Mirror de la oferta** — Reflejar el lenguaje exacto de la descripción del trabajo. Si dice "REST APIs", usar "REST APIs", no solo "APIs".
6. **ATS-ready** — Formato simple: una columna, viñetas, encabezados estándar. Skills como lista, no como párrafo.
7. **Sin huella IA** — El output final no debe revelar que fue generado por IA. No hay footer, no hay disclaimer.
8. **Revisión humana obligatoria** — El CV generado es un borrador optimizado, no el producto final. El usuario siempre revisa antes de enviar.
9. **Sin emojis ni símbolos especiales** — Caracteres no ASCII (📧📱📍🔗💻) rompen parsers ATS. Usar solo texto plano en la info de contacto.
10. **Sin secciones vacías** — Si el perfil no tiene experiencia laboral, no renderizar la sección "Experiencia Profesional". Una sección vacía delata debilidad y confunde al ATS.
11. **Tiempos verbales correctos** — Presente para roles en curso, pasado para roles y proyectos completados.
12. **Orden cronológico inverso** — Experiencias y proyectos listados del más reciente al más antiguo.
13. **Keywords en contexto, no stuffing** — Las keywords de la oferta deben aparecer dentro de logros reales, nunca como listas vacías de términos.

## Reglas de código

1. **Un módulo, un propósito** — `file_io.py` solo IO, `optimizer.py` solo prompt+API, `renderers.py` solo formato, `models.py` solo schemas.
2. **Prompt en optimizer.py, no en templates** — La lógica de generación vive en el prompt, no en el renderer.
3. **Validación en el borde** — Pydantic valida la respuesta de la IA antes de que toque cualquier renderizador.
4. **Tests protegen el pipeline** — Cada cambio en prompt, schema o render debe pasar los 8 tests existentes.
5. **Sin mágica** — No modificar el perfil YAML del usuario. El programa adapta, no altera la fuente de verdad.
6. **Idioma explícito** — `-l es|en` controla TODO el output. El prompt y los headers deben coincidir.
