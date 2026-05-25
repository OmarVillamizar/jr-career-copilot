import os
import sys
import re
import yaml

def load_profile(profile_path: str) -> dict:
    """
    Carga y analiza el perfil del ingeniero junior desde un archivo YAML.
    
    Args:
        profile_path (str): Ruta al archivo YAML.
        
    Returns:
        dict: Diccionario con la información del perfil del ingeniero junior.
    """
    if not os.path.exists(profile_path):
        print(f"\n[ERROR] No se pudo encontrar el archivo de perfil del ingeniero junior en: '{profile_path}'")
        print("Sugerencia: Crea el archivo a partir de la plantilla y asegúrate de que la ruta sea correcta.")
        sys.exit(1)
        
    try:
        with open(profile_path, "r", encoding="utf-8") as file:
            profile_data = yaml.safe_load(file)
            if not profile_data:
                raise ValueError("El archivo de perfil de ingeniero junior está vacío.")
            return profile_data
    except yaml.YAMLError as exc:
        print(f"\n[ERROR] Error de sintaxis al analizar el archivo YAML '{profile_path}':")
        print(exc)
        print("\nSugerencia: Revisa la indentación y asegúrate de no usar tabuladores, solo espacios.")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Ocurrió un error inesperado al leer el perfil del ingeniero junior:")
        print(exc)
        sys.exit(1)

def load_job_description(job_path: str) -> str:
    """
    Carga la descripción del puesto de trabajo desde un archivo de texto.
    
    Args:
        job_path (str): Ruta al archivo de texto.
        
    Returns:
        str: El contenido del archivo de descripción de trabajo.
    """
    if not os.path.exists(job_path):
        print(f"\n[ERROR] No se pudo encontrar el archivo de descripción de trabajo en: '{job_path}'")
        print("Sugerencia: Proporciona una ruta válida a un archivo de texto plano (.txt) con la vacante.")
        sys.exit(1)
        
    try:
        with open(job_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                raise ValueError("El archivo de descripción de trabajo está vacío.")
            return content
    except Exception as exc:
        print(f"\n[ERROR] Ocurrió un error al leer la descripción del trabajo en '{job_path}':")
        print(exc)
        sys.exit(1)

def save_markdown(content: str, output_path: str) -> None:
    """
    Guarda el currículum en formato Markdown en la ruta de salida especificada.
    
    Args:
        content (str): Contenido en formato Markdown.
        output_path (str): Ruta del archivo donde se guardará.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"[INFO] Currículum optimizado (Markdown) guardado en: '{output_path}'")
    except Exception as exc:
        print(f"\n[ERROR] No se pudo guardar el archivo Markdown en '{output_path}':")
        print(exc)
        sys.exit(1)

def save_html(content: str, output_path: str) -> None:
    """
    Guarda el currículum en formato HTML en la ruta de salida especificada.
    
    Args:
        content (str): Contenido del documento HTML.
        output_path (str): Ruta del archivo donde se guardará.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"[INFO] Currículum optimizado (HTML interactivo) guardado en: '{output_path}'")
        print("Sugerencia: Abre este archivo HTML en tu navegador y selecciona 'Imprimir -> Guardar como PDF'")
        print("            para obtener un documento PDF con maquetación profesional y limpia.")
    except Exception as exc:
        print(f"\n[ERROR] No se pudo guardar el archivo HTML en '{output_path}':")
        print(exc)
        sys.exit(1)

def _next_version_path(base_path: str) -> str:
    """
    Encuentra la siguiente ruta versionada para no sobrescribir outputs anteriores.
    
    Escanea el directorio en busca de archivos con patrón: {base}_v{NNN}.{ext}
    y devuelve la ruta con el siguiente número disponible.
    
    Args:
        base_path (str): Ruta base deseada (ej: 'output/mi_cv.md').
        
    Returns:
        str: Ruta versionada (ej: 'output/mi_cv_v001.md').
    """
    directory = os.path.dirname(base_path) or "."
    base_name = os.path.splitext(os.path.basename(base_path))[0]
    extension = os.path.splitext(base_path)[1]
    
    pattern = re.compile(rf"^{re.escape(base_name)}_v(\d+)\.md$")
    max_version = 0
    
    if os.path.exists(directory):
        for fname in os.listdir(directory):
            match = pattern.match(fname)
            if match:
                max_version = max(max_version, int(match.group(1)))
    
    next_version = max_version + 1
    return os.path.join(directory, f"{base_name}_v{next_version:03d}{extension}")

def save_markdown_versioned(content: str, output_path: str) -> str:
    """
    Guarda el currículum Markdown sin sobrescribir versiones anteriores.
    
    Args:
        content (str): Contenido en formato Markdown.
        output_path (str): Ruta base deseada.
        
    Returns:
        str: Ruta final donde se guardó el archivo.
    """
    versioned_path = _next_version_path(output_path)
    save_markdown(content, versioned_path)
    return versioned_path

def save_html_versioned(content: str, output_path: str) -> str:
    """
    Guarda el currículum HTML sin sobrescribir versiones anteriores.
    
    Args:
        content (str): Contenido del documento HTML.
        output_path (str): Ruta base deseada.
        
    Returns:
        str: Ruta final donde se guardó el archivo.
    """
    versioned_path = _next_version_path(output_path)
    save_html(content, versioned_path)
    return versioned_path
