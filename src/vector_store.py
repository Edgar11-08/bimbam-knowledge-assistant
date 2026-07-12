"""Creación, almacenamiento y carga de la base vectorial FAISS.

Este módulo recibe los objetos Document generados por document_loader,
los divide en fragmentos, crea sus embeddings y guarda el índice FAISS
en el almacenamiento local del proyecto.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CSV_DIR,
    FAISS_INDEX_DIR,
    FAISS_INDEX_NAME,
    PDF_DIR,
)
from src.document_loader import DocumentLoader
from src.embeddings_manager import get_embeddings_model
from src.logger import get_logger


logger = get_logger(__name__)


class VectorStoreManager:
    """Administra el ciclo de vida de la base vectorial FAISS."""

    MANIFEST_FILENAME = "manifest.json"

    def __init__(
        self,
        embeddings: Embeddings | None = None,
        index_directory: Path | str = FAISS_INDEX_DIR,
        index_name: str = FAISS_INDEX_NAME,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ) -> None:
        """
        Inicializa el administrador de la base vectorial.

        Args:
            embeddings:
                Modelo utilizado para generar embeddings.
            index_directory:
                Carpeta donde se guardará el índice FAISS.
            index_name:
                Nombre de los archivos del índice.
            chunk_size:
                Cantidad máxima aproximada de caracteres por fragmento.
            chunk_overlap:
                Solapamiento entre fragmentos consecutivos.
        """

        self.embeddings = embeddings or get_embeddings_model()
        self.index_directory = Path(index_directory)
        self.index_name = index_name.strip()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._validate_settings()
        self.index_directory.mkdir(parents=True, exist_ok=True)

        logger.info(
            "VectorStoreManager configurado. Índice: %s",
            self.index_name,
        )

    @property
    def faiss_file(self) -> Path:
        """Devuelve la ruta del archivo principal de FAISS."""

        return self.index_directory / f"{self.index_name}.faiss"

    @property
    def pickle_file(self) -> Path:
        """Devuelve la ruta del almacén de documentos de FAISS."""

        return self.index_directory / f"{self.index_name}.pkl"

    @property
    def manifest_file(self) -> Path:
        """Devuelve la ruta del manifiesto del índice."""

        return self.index_directory / self.MANIFEST_FILENAME

    def _validate_settings(self) -> None:
        """Valida los parámetros utilizados para crear fragmentos."""

        if not self.index_name:
            raise ValueError(
                "El nombre del índice FAISS no puede estar vacío."
            )

        if self.chunk_size <= 0:
            raise ValueError(
                "CHUNK_SIZE debe ser mayor que cero."
            )

        if self.chunk_overlap < 0:
            raise ValueError(
                "CHUNK_OVERLAP no puede ser negativo."
            )

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "CHUNK_OVERLAP debe ser menor que CHUNK_SIZE."
            )

    def create_text_splitter(
        self,
    ) -> RecursiveCharacterTextSplitter:
        """
        Crea el divisor de texto utilizado por la base vectorial.

        Returns:
            Divisor configurado con tamaño y solapamiento.
        """

        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "; ",
                ", ",
                " ",
                "",
            ],
        )

    def split_documents(
        self,
        documents: list[Document],
    ) -> list[Document]:
        """
        Divide los documentos en fragmentos más pequeños.

        Los metadatos originales se conservan y se agregan datos
        relacionados con cada fragmento.

        Args:
            documents:
                Documentos cargados desde PDF y CSV.

        Returns:
            Lista de fragmentos listos para generar embeddings.

        Raises:
            ValueError:
                Si no se proporcionaron documentos.
        """

        if not documents:
            raise ValueError(
                "No se proporcionaron documentos para dividir."
            )

        logger.info(
            "Dividiendo %s documentos en fragmentos.",
            len(documents),
        )

        splitter = self.create_text_splitter()
        chunks = splitter.split_documents(documents)

        if not chunks:
            raise RuntimeError(
                "El divisor de texto no generó fragmentos."
            )

        source_counters: dict[str, int] = defaultdict(int)

        for global_index, chunk in enumerate(chunks, start=1):
            source = str(
                chunk.metadata.get("source", "desconocido")
            )

            source_counters[source] += 1

            chunk.metadata.update(
                {
                    "chunk_id": f"chunk-{global_index:05d}",
                    "chunk_index": source_counters[source],
                    "chunk_characters": len(chunk.page_content),
                }
            )

        logger.info(
            "División completada. Fragmentos generados: %s",
            len(chunks),
        )

        return chunks

    def build_vector_store(
        self,
        chunks: list[Document],
    ) -> FAISS:
        """
        Genera un índice FAISS a partir de fragmentos.

        Esta operación realiza llamadas al modelo de embeddings.

        Args:
            chunks:
                Fragmentos que serán almacenados.

        Returns:
            Base vectorial FAISS creada en memoria.
        """

        if not chunks:
            raise ValueError(
                "No se proporcionaron fragmentos para crear FAISS."
            )

        logger.info(
            "Creando índice FAISS con %s fragmentos.",
            len(chunks),
        )

        try:
            vector_store = FAISS.from_documents(
                documents=chunks,
                embedding=self.embeddings,
            )

            logger.info(
                "Índice FAISS creado correctamente."
            )

            return vector_store

        except Exception as error:
            logger.exception(
                "No fue posible crear el índice FAISS: %s",
                error,
            )

            raise RuntimeError(
                "No fue posible crear la base vectorial. "
                "Verifica Gemini Embeddings, tu conexión y la cuota."
            ) from error

    def save_vector_store(
        self,
        vector_store: FAISS,
        document_count: int,
        chunk_count: int,
        fingerprint: str,
    ) -> None:
        """
        Guarda el índice FAISS y un manifiesto de construcción.

        Args:
            vector_store:
                Índice que se guardará localmente.
            document_count:
                Cantidad de documentos originales.
            chunk_count:
                Cantidad de fragmentos almacenados.
            fingerprint:
                Huella digital de la base de conocimiento.
        """

        self.index_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "Guardando índice FAISS en: %s",
            self.index_directory,
        )

        vector_store.save_local(
            folder_path=str(self.index_directory),
            index_name=self.index_name,
        )

        manifest: dict[str, Any] = {
            "index_name": self.index_name,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "document_count": document_count,
            "chunk_count": chunk_count,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "knowledge_base_fingerprint": fingerprint,
        }

        self.manifest_file.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        logger.info(
            "Índice y manifiesto guardados correctamente."
        )

    def index_exists(self) -> bool:
        """Indica si todos los archivos requeridos existen."""

        return (
            self.faiss_file.exists()
            and self.pickle_file.exists()
            and self.manifest_file.exists()
        )

    def load_vector_store(self) -> FAISS:
        """
        Carga un índice FAISS generado por esta aplicación.

        Returns:
            Índice FAISS cargado.

        Raises:
            FileNotFoundError:
                Si el índice no existe.
            RuntimeError:
                Si no puede cargarse.
        """

        if not self.index_exists():
            raise FileNotFoundError(
                "No existe un índice FAISS completo. "
                "Primero debes construir la base vectorial."
            )

        logger.info(
            "Cargando índice FAISS desde: %s",
            self.index_directory,
        )

        try:
            vector_store = FAISS.load_local(
                folder_path=str(self.index_directory),
                embeddings=self.embeddings,
                index_name=self.index_name,
                allow_dangerous_deserialization=True,
            )

            logger.info(
                "Índice FAISS cargado correctamente."
            )

            return vector_store

        except Exception as error:
            logger.exception(
                "No fue posible cargar el índice FAISS: %s",
                error,
            )

            raise RuntimeError(
                "No fue posible cargar la base vectorial."
            ) from error

    def calculate_knowledge_base_fingerprint(self) -> str:
        """
        Calcula una huella digital de los PDF y CSV.

        Si un documento cambia, se genera una huella diferente y la
        aplicación sabrá que debe reconstruir el índice.

        Returns:
            Hash SHA-256 de los archivos de conocimiento.
        """

        hasher = hashlib.sha256()

        knowledge_files = sorted(
            [
                *PDF_DIR.rglob("*.pdf"),
                *CSV_DIR.rglob("*.csv"),
            ],
            key=lambda path: str(path).lower(),
        )

        for file_path in knowledge_files:
            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(
                file_path.parent.parent
            )

            hasher.update(
                str(relative_path).encode("utf-8")
            )

            with file_path.open("rb") as file:
                while block := file.read(65536):
                    hasher.update(block)

        # Los parámetros también afectan al índice.
        hasher.update(
            str(self.chunk_size).encode("utf-8")
        )
        hasher.update(
            str(self.chunk_overlap).encode("utf-8")
        )

        return hasher.hexdigest()

    def read_manifest(self) -> dict[str, Any]:
        """Lee la información del manifiesto guardado."""

        if not self.manifest_file.exists():
            return {}

        try:
            return json.loads(
                self.manifest_file.read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, json.JSONDecodeError) as error:
            logger.warning(
                "No fue posible leer el manifiesto: %s",
                error,
            )
            return {}

    def index_is_current(self) -> bool:
        """
        Comprueba si el índice coincide con los documentos actuales.

        Returns:
            True cuando no es necesario reconstruir el índice.
        """

        if not self.index_exists():
            return False

        manifest = self.read_manifest()

        stored_fingerprint = manifest.get(
            "knowledge_base_fingerprint"
        )

        current_fingerprint = (
            self.calculate_knowledge_base_fingerprint()
        )

        is_current = stored_fingerprint == current_fingerprint

        if not is_current:
            logger.info(
                "La base de conocimiento cambió. "
                "El índice debe reconstruirse."
            )

        return is_current

    def clear_index(self) -> None:
        """Elimina los archivos generados de la base vectorial."""

        if not self.index_directory.exists():
            return

        logger.info(
            "Eliminando índice FAISS anterior."
        )

        for path in self.index_directory.iterdir():
            if path.name == ".gitkeep":
                continue

            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    def create_vector_store(
        self,
        documents: list[Document],
    ) -> FAISS:
        """
        Ejecuta el proceso completo de creación del índice.

        Args:
            documents:
                Documentos originales de la base de conocimiento.

        Returns:
            Índice FAISS construido y guardado.
        """

        chunks = self.split_documents(documents)
        fingerprint = (
            self.calculate_knowledge_base_fingerprint()
        )

        vector_store = self.build_vector_store(chunks)

        self.save_vector_store(
            vector_store=vector_store,
            document_count=len(documents),
            chunk_count=len(chunks),
            fingerprint=fingerprint,
        )

        return vector_store

    def create_or_load(
        self,
        force_rebuild: bool = False,
    ) -> FAISS:
        """
        Carga un índice existente o construye uno nuevo.

        Args:
            force_rebuild:
                Obliga a regenerar el índice aunque esté actualizado.

        Returns:
            Base vectorial lista para realizar búsquedas.
        """

        if (
            not force_rebuild
            and self.index_is_current()
        ):
            logger.info(
                "El índice está actualizado. Se reutilizará."
            )
            return self.load_vector_store()

        logger.info(
            "Construyendo una nueva base vectorial."
        )

        self.clear_index()

        loader = DocumentLoader()
        documents = loader.load_all_documents()
        loader.print_summary()

        return self.create_vector_store(documents)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
    ) -> list[Document]:
        """
        Realiza una búsqueda semántica para pruebas.

        Args:
            query:
                Pregunta o texto que se desea buscar.
            k:
                Cantidad máxima de resultados.

        Returns:
            Fragmentos más relacionados con la consulta.
        """

        clean_query = query.strip()

        if not clean_query:
            raise ValueError(
                "La consulta no puede estar vacía."
            )

        if k <= 0:
            raise ValueError(
                "El número de resultados debe ser mayor que cero."
            )

        vector_store = self.create_or_load()

        logger.info(
            "Ejecutando búsqueda semántica con k=%s.",
            k,
        )

        return vector_store.similarity_search(
            query=clean_query,
            k=k,
        )


def get_vector_store(
    force_rebuild: bool = False,
) -> FAISS:
    """
    Devuelve la base vectorial lista para usarse.

    Args:
        force_rebuild:
            Indica si debe reconstruirse el índice.

    Returns:
        Índice FAISS cargado o generado.
    """

    manager = VectorStoreManager()

    return manager.create_or_load(
        force_rebuild=force_rebuild
    )