"""Configuración central del proyecto BimBam Knowledge Assistant."""

import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------
# Rutas principales
# ---------------------------------------------------------

# Carpeta raíz del proyecto:
# challenge-alura-agente/
BASE_DIR = Path(__file__).resolve().parent.parent

# Archivo de variables de entorno
ENV_FILE = BASE_DIR / ".env"

# Cargar las variables del archivo .env ubicado en la raíz
load_dotenv(dotenv_path=ENV_FILE)

# Carpetas de documentos
DOCUMENTS_DIR = BASE_DIR / "documents"
PDF_DIR = DOCUMENTS_DIR / "pdf"
CSV_DIR = DOCUMENTS_DIR / "csv"

# Carpetas generadas por la aplicación
DATA_DIR = BASE_DIR / "data"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"
PROCESSED_DOCUMENTS_DIR = DATA_DIR / "processed_documents"
CACHE_DIR = DATA_DIR / "cache"

# Carpetas de documentación y evidencias
DOCS_DIR = BASE_DIR / "docs"
EVIDENCE_DIR = BASE_DIR / "evidencias"


# ---------------------------------------------------------
# Configuración de Gemini
# ---------------------------------------------------------

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
).strip()

CHAT_MODEL = os.getenv(
    "GEMINI_CHAT_MODEL",
    "gemini-2.5-flash",
).strip()

EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-001",
).strip()


# ---------------------------------------------------------
# Configuración de procesamiento
# ---------------------------------------------------------

# Tamaño máximo aproximado de cada fragmento de texto
CHUNK_SIZE = int(
    os.getenv(
        "CHUNK_SIZE",
        "1000",
    )
)

# Cantidad de caracteres compartidos entre fragmentos consecutivos
CHUNK_OVERLAP = int(
    os.getenv(
        "CHUNK_OVERLAP",
        "200",
    )
)

# Número de fragmentos recuperados por consulta
RETRIEVER_TOP_K = int(
    os.getenv(
        "RETRIEVER_TOP_K",
        "4",
    )
)

# Nivel de creatividad del modelo.
# Para responder con documentos conviene mantenerlo bajo.
MODEL_TEMPERATURE = float(
    os.getenv(
        "MODEL_TEMPERATURE",
        "0.1",
    )
)

# Máximo de archivos diferentes que se mostrarán como fuentes
MAX_SOURCES = int(
    os.getenv(
        "MAX_SOURCES",
        "4",
    )
)

# Máximo de caracteres enviados como contexto al modelo
MAX_CONTEXT_CHARACTERS = int(
    os.getenv(
        "MAX_CONTEXT_CHARACTERS",
        "12000",
    )
)

# Nombre utilizado para guardar los archivos del índice FAISS
FAISS_INDEX_NAME = os.getenv(
    "FAISS_INDEX_NAME",
    "bimbam_index",
).strip()


# ---------------------------------------------------------
# Configuración general
# ---------------------------------------------------------

APP_NAME = "BimBam Knowledge Assistant"

APP_DESCRIPTION = (
    "Agente inteligente para consultar políticas, productos, envíos, "
    "garantías y servicios de BimBam Buy."
)

SUPPORTED_PDF_EXTENSION = ".pdf"
SUPPORTED_CSV_EXTENSION = ".csv"


# ---------------------------------------------------------
# Funciones de configuración
# ---------------------------------------------------------

def create_required_directories() -> None:
    """Crea las carpetas requeridas si todavía no existen."""

    required_directories = [
        PDF_DIR,
        CSV_DIR,
        FAISS_INDEX_DIR,
        PROCESSED_DOCUMENTS_DIR,
        CACHE_DIR,
        DOCS_DIR,
        EVIDENCE_DIR,
    ]

    for directory in required_directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def validate_configuration(
    require_api_key: bool = True,
) -> None:
    """
    Verifica que la configuración mínima del proyecto sea válida.

    Args:
        require_api_key:
            Indica si debe comprobarse la existencia de GEMINI_API_KEY.

    Raises:
        ValueError:
            Si falta la API Key o algún parámetro es inválido.
        FileNotFoundError:
            Si no existen las carpetas de documentos.
    """

    if require_api_key and not GEMINI_API_KEY:
        raise ValueError(
            "No se encontró GEMINI_API_KEY. "
            "Agrégala al archivo .env ubicado en la raíz del proyecto."
        )

    if not CHAT_MODEL:
        raise ValueError(
            "GEMINI_CHAT_MODEL no puede estar vacío."
        )

    if not EMBEDDING_MODEL:
        raise ValueError(
            "GEMINI_EMBEDDING_MODEL no puede estar vacío."
        )

    if not FAISS_INDEX_NAME:
        raise ValueError(
            "FAISS_INDEX_NAME no puede estar vacío."
        )

    if CHUNK_SIZE <= 0:
        raise ValueError(
            "CHUNK_SIZE debe ser mayor que cero."
        )

    if CHUNK_OVERLAP < 0:
        raise ValueError(
            "CHUNK_OVERLAP no puede ser negativo."
        )

    if CHUNK_OVERLAP >= CHUNK_SIZE:
        raise ValueError(
            "CHUNK_OVERLAP debe ser menor que CHUNK_SIZE."
        )

    if RETRIEVER_TOP_K <= 0:
        raise ValueError(
            "RETRIEVER_TOP_K debe ser mayor que cero."
        )

    if MAX_SOURCES <= 0:
        raise ValueError(
            "MAX_SOURCES debe ser mayor que cero."
        )

    if MAX_CONTEXT_CHARACTERS <= 0:
        raise ValueError(
            "MAX_CONTEXT_CHARACTERS debe ser mayor que cero."
        )

    if MODEL_TEMPERATURE < 0:
        raise ValueError(
            "MODEL_TEMPERATURE no puede ser negativo."
        )

    if not PDF_DIR.exists():
        raise FileNotFoundError(
            f"No se encontró la carpeta de documentos PDF: {PDF_DIR}"
        )

    if not CSV_DIR.exists():
        raise FileNotFoundError(
            f"No se encontró la carpeta de documentos CSV: {CSV_DIR}"
        )


# Crear automáticamente las carpetas internas necesarias
create_required_directories()