from typing import List, Optional
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    """
    Representa la información de contacto estructurada del ingeniero junior.
    """
    email: Optional[str] = Field(None, description="Email address of the junior engineer")
    phone: Optional[str] = Field(None, description="Phone number of the junior engineer")
    location: Optional[str] = Field(None, description="Physical location or city and country")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")

class OptimizedExperience(BaseModel):
    """
    Representa una experiencia profesional optimizada para la oferta laboral.
    """
    company: str = Field(description="Name of the company or organization")
    role: str = Field(description="Optimized role title aligned with the job description")
    period: str = Field(description="Employment or project period")
    tailored_achievements: List[str] = Field(
        description="Action-oriented, high-impact achievements tailored to the target job description. Focus on metrics, technologies, and results without inventing any facts."
    )

class OptimizedEducation(BaseModel):
    """
    Representa la formación académica optimizada (solo instituciones formales).
    """
    institution: str = Field(description="Name of the educational institution")
    degree: str = Field(description="Degree name")
    period: str = Field(description="Period of study")
    achievements: List[str] = Field(
        description="Key academic achievements, honors, or relevant coursework aligned with the job requirements."
    )

class OptimizedProject(BaseModel):
    """
    Representa un proyecto académico o personal optimizado.
    """
    name: str = Field(description="Project name")
    role: str = Field(description="Role in the project")
    period: str = Field(description="Project period")
    achievements: List[str] = Field(
        description="Key project achievements, technologies used, and results aligned with the job requirements."
    )

class Certification(BaseModel):
    """
    Representa una certificación profesional o académica.
    """
    name: str = Field(description="Certification name")
    issuer: str = Field(description="Issuing organization")
    date: str = Field(description="Date obtained (Month/Year)")

class OptimizedCV(BaseModel):
    """
    Estructura completa del currículum optimizado y adaptado.
    """
    full_name: str = Field(description="Full name of the junior engineer")
    contact_info: ContactInfo = Field(description="Structured contact info of the junior engineer")
    professional_summary: str = Field(
        description="Powerful 3-4 sentence professional summary in first person, applying Pygmalion Effect with natural human tone."
    )
    optimized_skills: List[str] = Field(
        description="List of core technical and professional skills filtered and sorted by relevance to the job description."
    )
    experiences: List[OptimizedExperience] = Field(
        description="List of professional work experiences (only if present in profile). Tailor using action verbs and technical keywords."
    )
    projects: List[OptimizedProject] = Field(
        description="List of academic or personal projects from the profile. Highlight technologies, impact, and relevance to the job."
    )
    education: List[OptimizedEducation] = Field(
        description="List of formal education (universities, technical institutes). Include relevant academic achievements."
    )
    certifications: List[Certification] = Field(
        description="List of certifications from the profile. Include all, prioritizing those relevant to the job."
    )


# ── Robustness Judge models ──

class Alucinacion(BaseModel):
    """
    Una alucinación detectada en el CV generado: dato presente en el CV
    que NO existe en el perfil YAML original (fuente de verdad).
    """
    linea_cv: str = Field(
        description="Exact line from the generated CV that contains the invented or exaggerated data"
    )
    dato_inventado: str = Field(
        description="What specific data was invented, exaggerated, or cannot be verified against the source profile"
    )
    severidad: str = Field(
        description="Severity level: 'baja' (minor rephrasing), 'media' (unverified claim), 'alta' (fabricated fact)"
    )


class ReporteRobustez(BaseModel):
    """
    Reporte completo de auditoría de robustez del CV generado.
    Evalúa veracidad, consistencia y compliance ético.
    """
    score_honestidad: int = Field(
        ge=0, le=100,
        description="Overall honesty score (0-100). 100 = fully truthful, no fabricated data."
    )
    alucinaciones_detectadas: List[Alucinacion] = Field(
        default_factory=list,
        description="List of all detected hallucinations in the CV"
    )
    comentario_auditor: str = Field(
        description="Auditor's detailed commentary: strengths of the CV, risks found, specific recommendations for the candidate"
    )
