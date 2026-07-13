"""Recuperación semántica de información desde la base vectorial.

Este módulo consulta el índice FAISS, elimina fragmentos duplicados,
organiza las fuentes y construye el contexto que posteriormente
recibirá el modelo de lenguaje.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.config import (
    MAX_CONTEXT_CHARACTERS,
    MAX_SOURCES,
    RETRIEVER_TOP_K,
)
from src.logger import get_logger
from src.vector_store import VectorStoreManager


logger = get_logger(__name__)


@dataclass(frozen=True)
class RetrievalItem:
    """Representa un fragmento recuperado desde FAISS."""

    document: Document
    score: float
    rank: int

    @property
    def source(self) -> str:
        """Devuelve el nombre del archivo fuente."""

        return str(
            self.document.metadata.get(
                "source",
                "Fuente desconocida",
            )
        )

    @property
    def document_name(self) -> str:
        """Devuelve el nombre legible del documento."""

        return str(
            self.document.metadata.get(
                "document_name",
                self.source,
            )
        )

    @property
    def category(self) -> str:
        """Devuelve la categoría del documento."""

        return str(
            self.document.metadata.get(
                "category",
                "general",
            )
        )

    @property
    def location(self) -> str:
        """Devuelve la página, fila o fragmento de origen."""

        metadata = self.document.metadata

        if metadata.get("page") is not None:
            return f"Página {metadata['page']}"

        if metadata.get("row") is not None:
            return f"Fila {metadata['row']}"

        if metadata.get("chunk_index") is not None:
            return f"Fragmento {metadata['chunk_index']}"

        return "Ubicación no especificada"


@dataclass
class RetrievalResult:
    """Resultado completo de una operación de recuperación."""

    query: str
    items: list[RetrievalItem] = field(
        default_factory=list
    )
    context: str = ""
    sources: list[str] = field(
        default_factory=list
    )
    context_characters: int = 0
    requested_results: int = 0
    discarded_duplicates: int = 0

    @property
    def documents(self) -> list[Document]:
        """Devuelve únicamente los documentos recuperados."""

        return [
            item.document
            for item in self.items
        ]

    @property
    def total_results(self) -> int:
        """Devuelve el total de resultados utilizados."""

        return len(self.items)

    @property
    def has_results(self) -> bool:
        """Indica si se recuperó información."""

        return bool(self.items and self.context)


class KnowledgeRetriever:
    """Realiza búsquedas semánticas sobre la base de conocimiento."""

    def __init__(
        self,
        vector_store: FAISS | None = None,
        top_k: int = RETRIEVER_TOP_K,
        max_sources: int = MAX_SOURCES,
        max_context_characters: int = MAX_CONTEXT_CHARACTERS,
    ) -> None:
        """
        Inicializa el recuperador.

        Args:
            vector_store:
                Índice FAISS opcional. Si no se proporciona, se carga
                utilizando VectorStoreManager.
            top_k:
                Cantidad máxima de fragmentos que se utilizarán.
            max_sources:
                Cantidad máxima de fuentes únicas que se mostrarán.
            max_context_characters:
                Límite de caracteres para el contexto del modelo.
        """

        self.top_k = top_k
        self.max_sources = max_sources
        self.max_context_characters = (
            max_context_characters
        )

        self._validate_settings()

        self.vector_store = (
            vector_store
            if vector_store is not None
            else VectorStoreManager().create_or_load()
        )

        logger.info(
            "KnowledgeRetriever configurado con top_k=%s "
            "y límite de contexto=%s caracteres.",
            self.top_k,
            self.max_context_characters,
        )

    def _validate_settings(self) -> None:
        """Valida la configuración del recuperador."""

        if self.top_k <= 0:
            raise ValueError(
                "top_k debe ser mayor que cero."
            )

        if self.max_sources <= 0:
            raise ValueError(
                "max_sources debe ser mayor que cero."
            )

        if self.max_context_characters <= 0:
            raise ValueError(
                "max_context_characters debe ser mayor que cero."
            )

    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Limpia y valida una consulta.

        Args:
            query:
                Pregunta original del usuario.

        Returns:
            Pregunta sin espacios innecesarios.

        Raises:
            ValueError:
                Si la pregunta está vacía o es demasiado corta.
        """

        clean_query = " ".join(query.split())

        if not clean_query:
            raise ValueError(
                "La consulta no puede estar vacía."
            )

        if len(clean_query) < 3:
            raise ValueError(
                "La consulta debe contener al menos "
                "tres caracteres."
            )

        return clean_query

    @staticmethod
    def document_fingerprint(
        document: Document,
    ) -> str:
        """
        Calcula una huella del contenido de un fragmento.

        Args:
            document:
                Fragmento recuperado.

        Returns:
            Hash SHA-256 del contenido normalizado.
        """

        normalized_content = " ".join(
            document.page_content.lower().split()
        )

        return hashlib.sha256(
            normalized_content.encode("utf-8")
        ).hexdigest()

    def remove_duplicate_documents(
        self,
        results: list[tuple[Document, float]],
    ) -> tuple[list[tuple[Document, float]], int]:
        """
        Elimina fragmentos cuyo contenido sea idéntico.

        No elimina documentos diferentes que pertenezcan a una misma
        fuente, ya que pueden contener evidencia complementaria.

        Args:
            results:
                Documentos acompañados por su puntuación de FAISS.

        Returns:
            Resultados únicos y cantidad de duplicados descartados.
        """

        unique_results: list[
            tuple[Document, float]
        ] = []

        fingerprints: set[str] = set()
        discarded_duplicates = 0

        for document, score in results:
            fingerprint = self.document_fingerprint(
                document
            )

            if fingerprint in fingerprints:
                discarded_duplicates += 1
                continue

            fingerprints.add(fingerprint)
            unique_results.append(
                (document, float(score))
            )

        return unique_results, discarded_duplicates

    @staticmethod
    def format_context_block(
        item: RetrievalItem,
    ) -> str:
        """
        Convierte un resultado en un bloque estructurado.

        Args:
            item:
                Fragmento recuperado.

        Returns:
            Texto preparado para el prompt del agente.
        """

        metadata = item.document.metadata
        chunk_id = metadata.get(
            "chunk_id",
            "sin-identificador",
        )

        return (
            f"--- EVIDENCIA {item.rank} ---\n"
            f"Fuente: {item.document_name}\n"
            f"Archivo: {item.source}\n"
            f"Ubicación: {item.location}\n"
            f"Categoría: {item.category}\n"
            f"Fragmento: {chunk_id}\n"
            f"Contenido:\n"
            f"{item.document.page_content.strip()}\n"
            f"--- FIN DE EVIDENCIA {item.rank} ---"
        )

    def build_context(
        self,
        items: list[RetrievalItem],
    ) -> tuple[str, list[RetrievalItem]]:
        """
        Construye el contexto respetando el límite configurado.

        Args:
            items:
                Fragmentos ordenados por relevancia.

        Returns:
            Contexto final y elementos realmente incluidos.
        """

        context_blocks: list[str] = []
        included_items: list[RetrievalItem] = []
        current_length = 0

        for item in items:
            block = self.format_context_block(item)

            separator_length = (
                2 if context_blocks else 0
            )

            available_characters = (
                self.max_context_characters
                - current_length
                - separator_length
            )

            if available_characters <= 0:
                break

            if len(block) > available_characters:
                # Solo truncamos cuando todavía no se ha podido
                # incorporar ningún resultado completo.
                if not context_blocks:
                    truncation_notice = (
                        "\n[Fragmento truncado por "
                        "límite de contexto]"
                    )

                    usable_length = max(
                        0,
                        available_characters
                        - len(truncation_notice),
                    )

                    truncated_block = (
                        block[:usable_length].rstrip()
                        + truncation_notice
                    )

                    context_blocks.append(
                        truncated_block
                    )
                    included_items.append(item)

                break

            context_blocks.append(block)
            included_items.append(item)

            current_length += (
                len(block) + separator_length
            )

        context = "\n\n".join(context_blocks)

        return context, included_items

    def get_unique_sources(
        self,
        items: list[RetrievalItem],
    ) -> list[str]:
        """
        Obtiene fuentes sin duplicados manteniendo su orden.

        Args:
            items:
                Resultados incluidos en el contexto.

        Returns:
            Lista limitada de nombres de archivo.
        """

        sources: list[str] = []
        seen_sources: set[str] = set()

        for item in items:
            if item.source in seen_sources:
                continue

            seen_sources.add(item.source)
            sources.append(item.source)

            if len(sources) >= self.max_sources:
                break

        return sources

    def search_with_scores(
        self,
        query: str,
        fetch_k: int,
    ) -> list[tuple[Document, float]]:
        """
        Ejecuta la búsqueda semántica con puntuaciones.

        La puntuación se conserva como valor técnico bruto de FAISS.
        No debe interpretarse directamente como un porcentaje de
        confianza.

        Args:
            query:
                Consulta normalizada.
            fetch_k:
                Cantidad inicial de candidatos.

        Returns:
            Pares de documento y puntuación.
        """

        logger.info(
            "Buscando hasta %s candidatos en FAISS.",
            fetch_k,
        )

        try:
            return (
                self.vector_store
                .similarity_search_with_score(
                    query=query,
                    k=fetch_k,
                )
            )

        except Exception as error:
            logger.exception(
                "Error durante la recuperación semántica: %s",
                error,
            )

            raise RuntimeError(
                "No fue posible consultar la base vectorial."
            ) from error

    def retrieve(
        self,
        query: str,
        k: int | None = None,
    ) -> RetrievalResult:
        """
        Recupera y prepara información para responder una pregunta.

        Args:
            query:
                Pregunta del usuario.
            k:
                Número opcional de fragmentos finales.

        Returns:
            Resultado estructurado de recuperación.
        """

        clean_query = self.normalize_query(query)
        requested_k = self.top_k if k is None else k

        if requested_k <= 0:
            raise ValueError(
                "k debe ser mayor que cero."
            )

        # Pedimos candidatos adicionales porque algunos pueden
        # resultar duplicados o no caber en el contexto.
        fetch_k = max(
            requested_k * 3,
            requested_k,
        )

        logger.info(
            "Recuperando información para la consulta: %s",
            clean_query,
        )

        raw_results = self.search_with_scores(
            query=clean_query,
            fetch_k=fetch_k,
        )

        unique_results, discarded_duplicates = (
            self.remove_duplicate_documents(
                raw_results
            )
        )

        selected_results = unique_results[
            :requested_k
        ]

        preliminary_items = [
            RetrievalItem(
                document=document,
                score=score,
                rank=index,
            )
            for index, (document, score) in enumerate(
                selected_results,
                start=1,
            )
        ]

        context, included_items = self.build_context(
            preliminary_items
        )

        # Reasignamos rangos para garantizar que sean consecutivos
        # después del límite de contexto.
        final_items = [
            RetrievalItem(
                document=item.document,
                score=item.score,
                rank=index,
            )
            for index, item in enumerate(
                included_items,
                start=1,
            )
        ]

        if final_items != included_items:
            context, final_items = self.build_context(
                final_items
            )

        sources = self.get_unique_sources(
            final_items
        )

        result = RetrievalResult(
            query=clean_query,
            items=final_items,
            context=context,
            sources=sources,
            context_characters=len(context),
            requested_results=requested_k,
            discarded_duplicates=discarded_duplicates,
        )

        self.log_statistics(result)

        return result

    @staticmethod
    def log_statistics(
        result: RetrievalResult,
    ) -> None:
        """Registra estadísticas de la recuperación."""

        logger.info(
            "Recuperación finalizada: resultados=%s, "
            "fuentes=%s, caracteres_contexto=%s, "
            "duplicados_descartados=%s.",
            result.total_results,
            len(result.sources),
            result.context_characters,
            result.discarded_duplicates,
        )


def get_retriever() -> KnowledgeRetriever:
    """Crea un recuperador con la configuración predeterminada."""

    return KnowledgeRetriever()