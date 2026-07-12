"""Administración del modelo de embeddings de Google Gemini.

Este módulo crea y valida el modelo utilizado para convertir textos
y consultas en vectores numéricos.

El almacenamiento de los vectores pertenece a vector_store.py.
"""

from __future__ import annotations

from functools import lru_cache
from math import sqrt

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.config import EMBEDDING_MODEL, GEMINI_API_KEY
from src.logger import get_logger


logger = get_logger(__name__)


class EmbeddingsManager:
    """Administra la creación y validación de embeddings con Gemini."""

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL,
        api_key: str = GEMINI_API_KEY,
    ) -> None:
        """
        Inicializa el administrador de embeddings.

        Args:
            model_name:
                Nombre del modelo de embeddings de Gemini.
            api_key:
                Clave de acceso a la API de Gemini.

        Raises:
            ValueError:
                Si no se proporciona una API Key o un modelo válido.
        """

        self.model_name = model_name.strip()
        self.api_key = api_key.strip()

        self._validate_settings()

        logger.info(
            "EmbeddingsManager configurado con el modelo: %s",
            self.model_name,
        )

    def _validate_settings(self) -> None:
        """Valida los parámetros mínimos del administrador."""

        if not self.api_key:
            raise ValueError(
                "No se encontró la API Key de Gemini. "
                "Verifica GEMINI_API_KEY en el archivo .env."
            )

        if not self.model_name:
            raise ValueError(
                "El nombre del modelo de embeddings no puede estar vacío."
            )

    def create_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """
        Crea una instancia del modelo de embeddings.

        Returns:
            Modelo de embeddings configurado para Gemini.
        """

        logger.info(
            "Creando cliente de embeddings con el modelo %s.",
            self.model_name,
        )

        return GoogleGenerativeAIEmbeddings(
            model=self.model_name,
            google_api_key=self.api_key,
        )

    def validate_connection(self) -> dict[str, object]:
        """
        Realiza una consulta pequeña para validar la conexión con Gemini.

        Esta prueba genera un único embedding, por lo que realiza una
        llamada real a la API.

        Returns:
            Información básica del vector generado.

        Raises:
            RuntimeError:
                Si la API no responde o el vector generado es inválido.
        """

        test_text = (
            "BimBam Buy ofrece información sobre envíos, pagos y garantías."
        )

        logger.info("Validando conexión con Gemini Embeddings.")

        try:
            embeddings = self.create_embeddings()
            vector = embeddings.embed_query(test_text)

            if not vector:
                raise ValueError(
                    "Gemini devolvió un vector vacío."
                )

            if not all(
                isinstance(value, (int, float))
                for value in vector
            ):
                raise TypeError(
                    "El vector contiene valores no numéricos."
                )

            vector_norm = self.calculate_vector_norm(vector)

            result: dict[str, object] = {
                "model": self.model_name,
                "dimensions": len(vector),
                "vector_norm": round(vector_norm, 6),
                "status": "connected",
            }

            logger.info(
                "Conexión validada. Dimensiones del vector: %s.",
                len(vector),
            )

            return result

        except Exception as error:
            logger.exception(
                "No fue posible validar Gemini Embeddings: %s",
                error,
            )

            raise RuntimeError(
                "No fue posible conectar con Gemini Embeddings. "
                "Verifica la API Key, el modelo, la conexión a Internet "
                "y la cuota disponible."
            ) from error

    @staticmethod
    def calculate_vector_norm(vector: list[float]) -> float:
        """
        Calcula la norma euclidiana de un vector.

        Args:
            vector:
                Vector numérico generado por el modelo.

        Returns:
            Norma euclidiana del vector.
        """

        return sqrt(
            sum(float(value) ** 2 for value in vector)
        )

    def embed_query(self, query: str) -> list[float]:
        """
        Convierte una consulta en un vector.

        Args:
            query:
                Pregunta o consulta del usuario.

        Returns:
            Vector correspondiente a la consulta.

        Raises:
            ValueError:
                Si la consulta está vacía.
        """

        clean_query = query.strip()

        if not clean_query:
            raise ValueError(
                "La consulta no puede estar vacía."
            )

        logger.info("Generando embedding para una consulta.")

        embeddings = self.create_embeddings()

        return embeddings.embed_query(clean_query)

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Convierte una lista de textos en vectores.

        Args:
            texts:
                Fragmentos de documentos que serán indexados.

        Returns:
            Lista de vectores generados.

        Raises:
            ValueError:
                Si la lista está vacía o contiene textos inválidos.
        """

        clean_texts = [
            text.strip()
            for text in texts
            if text and text.strip()
        ]

        if not clean_texts:
            raise ValueError(
                "No se proporcionaron textos válidos para generar embeddings."
            )

        logger.info(
            "Generando embeddings para %s textos.",
            len(clean_texts),
        )

        embeddings = self.create_embeddings()

        return embeddings.embed_documents(clean_texts)


@lru_cache(maxsize=1)
def get_embeddings_model() -> Embeddings:
    """
    Devuelve una instancia reutilizable del modelo de embeddings.

    El decorador lru_cache evita recrear el cliente cada vez que otro
    módulo solicita el modelo.

    Returns:
        Modelo compatible con LangChain.
    """

    manager = EmbeddingsManager()

    return manager.create_embeddings()