"""Agente inteligente RAG de BimBam Buy.

Este módulo coordina la recuperación de información, la construcción
del prompt y la generación de respuestas mediante Google Gemini.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import (
    CHAT_MODEL,
    GEMINI_API_KEY,
    MODEL_TEMPERATURE,
    RETRIEVER_TOP_K,
)
from src.logger import get_logger
from src.prompts import (
    ERROR_RESPONSE,
    NO_CONTEXT_RESPONSE,
    build_sources_text,
    get_qa_prompt,
)
from src.retriever import (
    KnowledgeRetriever,
    RetrievalItem,
    RetrievalResult,
)


logger = get_logger(__name__)


@dataclass
class AgentResponse:
    """Representa la respuesta final producida por el agente."""

    question: str
    answer: str
    sources: list[str] = field(default_factory=list)
    retrieval_items: list[RetrievalItem] = field(
        default_factory=list
    )
    context_characters: int = 0
    model_name: str = ""
    success: bool = True
    error_message: str | None = None

    @property
    def has_sources(self) -> bool:
        """Indica si la respuesta incluye fuentes documentales."""

        return bool(self.sources)

    @property
    def sources_text(self) -> str:
        """Devuelve las fuentes en formato legible."""

        return build_sources_text(self.sources)

    @property
    def total_sources(self) -> int:
        """Devuelve la cantidad de fuentes únicas."""

        return len(self.sources)

    @property
    def total_evidences(self) -> int:
        """Devuelve la cantidad de fragmentos utilizados."""

        return len(self.retrieval_items)

    def to_dict(self) -> dict[str, Any]:
        """Convierte la respuesta en un diccionario."""

        return {
            "question": self.question,
            "answer": self.answer,
            "sources": self.sources,
            "sources_text": self.sources_text,
            "total_sources": self.total_sources,
            "total_evidences": self.total_evidences,
            "context_characters": self.context_characters,
            "model_name": self.model_name,
            "success": self.success,
            "error_message": self.error_message,
        }


class BimBamAgent:
    """Agente RAG especializado en la documentación de BimBam Buy."""

    def __init__(
        self,
        retriever: KnowledgeRetriever | None = None,
        model: ChatGoogleGenerativeAI | None = None,
        model_name: str = CHAT_MODEL,
        api_key: str = GEMINI_API_KEY,
        temperature: float = MODEL_TEMPERATURE,
        top_k: int = RETRIEVER_TOP_K,
    ) -> None:
        """
        Inicializa el agente.

        Args:
            retriever:
                Recuperador semántico opcional.
            model:
                Modelo Gemini opcional, útil para pruebas.
            model_name:
                Nombre del modelo conversacional.
            api_key:
                Clave de la API de Gemini.
            temperature:
                Nivel de creatividad del modelo.
            top_k:
                Número de fragmentos solicitados al retriever.
        """

        self.model_name = model_name.strip()
        self.api_key = api_key.strip()
        self.temperature = temperature
        self.top_k = top_k

        self._validate_settings()

        self.retriever = (
            retriever
            if retriever is not None
            else KnowledgeRetriever()
        )

        self.model = (
            model
            if model is not None
            else self.create_model()
        )

        self.prompt = get_qa_prompt()

        logger.info(
            "BimBamAgent configurado con el modelo %s.",
            self.model_name,
        )

    def _validate_settings(self) -> None:
        """Valida la configuración del agente."""

        if not self.api_key:
            raise ValueError(
                "No se encontró GEMINI_API_KEY. "
                "Verifica el archivo .env."
            )

        if not self.model_name:
            raise ValueError(
                "El nombre del modelo de chat no puede estar vacío."
            )

        if self.temperature < 0:
            raise ValueError(
                "La temperatura no puede ser negativa."
            )

        if self.top_k <= 0:
            raise ValueError(
                "top_k debe ser mayor que cero."
            )

    def create_model(self) -> ChatGoogleGenerativeAI:
        """Crea el cliente conversacional de Gemini."""

        logger.info(
            "Creando cliente de Gemini con el modelo %s.",
            self.model_name,
        )

        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=self.temperature,
        )

    @staticmethod
    def normalize_question(question: str) -> str:
        """
        Limpia y valida la pregunta del usuario.

        Args:
            question:
                Pregunta original.

        Returns:
            Pregunta normalizada.
        """

        clean_question = " ".join(question.split())

        if not clean_question:
            raise ValueError(
                "La pregunta no puede estar vacía."
            )

        if len(clean_question) < 3:
            raise ValueError(
                "La pregunta debe contener al menos tres caracteres."
            )

        return clean_question

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza texto para realizar comparaciones más confiables.

        Elimina acentos, unifica mayúsculas y minúsculas,
        y reduce espacios repetidos.
        """

        normalized_text = unicodedata.normalize(
            "NFKD",
            text,
        )

        normalized_text = "".join(
            character
            for character in normalized_text
            if not unicodedata.combining(character)
        )

        return " ".join(
            normalized_text.lower().strip().split()
        )

    @staticmethod
    def extract_text_from_message(
        message: AIMessage | Any,
    ) -> str:
        """
        Extrae texto de la respuesta devuelta por Gemini.

        Algunas versiones pueden devolver texto simple o una lista
        de bloques estructurados.
        """

        content = getattr(message, "content", message)

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []

            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                    continue

                if isinstance(block, dict):
                    block_text = block.get("text")

                    if block_text:
                        text_parts.append(
                            str(block_text)
                        )

            return "\n".join(text_parts).strip()

        return str(content).strip()

    @classmethod
    def is_no_context_response(
        cls,
        answer: str,
    ) -> bool:
        """
        Comprueba si Gemini indicó que no existe información suficiente.

        Gemini puede devolver la frase exacta o agregar una explicación,
        por lo que se buscan distintos patrones equivalentes.
        """

        normalized_answer = cls.normalize_text(answer)

        no_context_patterns = (
            "no encontre informacion suficiente",
            "no encontre suficiente informacion",
            "no hay informacion suficiente",
            "la informacion proporcionada no es suficiente",
            "el contexto no contiene informacion suficiente",
            "la base de conocimiento no contiene informacion suficiente",
            "no se encontro informacion suficiente",
        )

        return any(
            pattern in normalized_answer
            for pattern in no_context_patterns
        )

    def retrieve_context(
        self,
        question: str,
    ) -> RetrievalResult:
        """Recupera el contexto documental para una pregunta."""

        logger.info(
            "Recuperando contexto para la pregunta: %s",
            question,
        )

        return self.retriever.retrieve(
            query=question,
            k=self.top_k,
        )

    def generate_answer(
        self,
        question: str,
        retrieval_result: RetrievalResult,
    ) -> str:
        """
        Genera una respuesta utilizando Gemini.

        Args:
            question:
                Pregunta del usuario.
            retrieval_result:
                Contexto y evidencias recuperadas.

        Returns:
            Respuesta textual del modelo.
        """

        if not retrieval_result.has_results:
            logger.warning(
                "No se recuperó contexto para la pregunta."
            )
            return NO_CONTEXT_RESPONSE

        messages = self.prompt.invoke(
            {
                "context": retrieval_result.context,
                "question": question,
            }
        )

        logger.info(
            "Enviando pregunta y contexto a Gemini."
        )

        response = self.model.invoke(messages)

        answer = self.extract_text_from_message(
            response
        )

        if not answer:
            logger.warning(
                "Gemini devolvió una respuesta vacía."
            )
            return NO_CONTEXT_RESPONSE

        return answer

    def answer(
        self,
        question: str,
    ) -> AgentResponse:
        """
        Ejecuta el flujo RAG completo.

        Args:
            question:
                Pregunta del usuario.

        Returns:
            Respuesta final con texto, fuentes y evidencias.
        """

        clean_question = self.normalize_question(
            question
        )

        logger.info(
            "Procesando consulta con BimBamAgent."
        )

        try:
            retrieval_result = self.retrieve_context(
                clean_question
            )

            if not retrieval_result.has_results:
                return AgentResponse(
                    question=clean_question,
                    answer=NO_CONTEXT_RESPONSE,
                    sources=[],
                    retrieval_items=[],
                    context_characters=0,
                    model_name=self.model_name,
                    success=True,
                )

            answer_text = self.generate_answer(
                question=clean_question,
                retrieval_result=retrieval_result,
            )

            has_supported_answer = (
                not self.is_no_context_response(
                    answer_text
                )
            )

            if not has_supported_answer:
                logger.info(
                    "La información recuperada no respalda "
                    "una respuesta. Se omitirán las fuentes."
                )

            result = AgentResponse(
                question=clean_question,
                answer=answer_text,
                sources=(
                    retrieval_result.sources
                    if has_supported_answer
                    else []
                ),
                retrieval_items=(
                    retrieval_result.items
                    if has_supported_answer
                    else []
                ),
                context_characters=(
                    retrieval_result.context_characters
                    if has_supported_answer
                    else 0
                ),
                model_name=self.model_name,
                success=True,
            )

            logger.info(
                "Respuesta generada correctamente. "
                "Fuentes=%s, evidencias=%s.",
                result.total_sources,
                result.total_evidences,
            )

            return result

        except ValueError:
            raise

        except Exception as error:
            logger.exception(
                "No fue posible procesar la consulta: %s",
                error,
            )

            return AgentResponse(
                question=clean_question,
                answer=ERROR_RESPONSE,
                sources=[],
                retrieval_items=[],
                context_characters=0,
                model_name=self.model_name,
                success=False,
                error_message=str(error),
            )

    def ask(self, question: str) -> str:
        """Devuelve únicamente el texto de la respuesta."""

        return self.answer(question).answer


def get_agent() -> BimBamAgent:
    """Crea el agente con la configuración predeterminada."""

    return BimBamAgent()