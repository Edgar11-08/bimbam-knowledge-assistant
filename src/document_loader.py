"""Carga y normalización de documentos PDF y CSV.

Este módulo convierte los archivos de la base de conocimiento de
BimBam Buy en objetos Document de LangChain.

Cada página de un PDF se transforma en un documento independiente.
Cada fila de un CSV se transforma en un documento independiente.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
from langchain_core.documents import Document
from pypdf import PdfReader

from src.config import (
    CSV_DIR,
    PDF_DIR,
    SUPPORTED_CSV_EXTENSION,
    SUPPORTED_PDF_EXTENSION,
)
from src.logger import get_logger


logger = get_logger(__name__)


@dataclass
class LoadingSummary:
    """Resumen del proceso de carga de documentos."""

    pdf_files_found: int = 0
    csv_files_found: int = 0
    pdf_pages_loaded: int = 0
    csv_rows_loaded: int = 0
    empty_elements_skipped: int = 0
    files_with_errors: int = 0

    @property
    def total_files(self) -> int:
        """Devuelve el total de archivos encontrados."""

        return self.pdf_files_found + self.csv_files_found

    @property
    def total_documents(self) -> int:
        """Devuelve el total de objetos Document creados."""

        return self.pdf_pages_loaded + self.csv_rows_loaded


class DocumentLoader:
    """Carga documentos PDF y CSV desde directorios configurables."""

    def __init__(
        self,
        pdf_directory: Path | str = PDF_DIR,
        csv_directory: Path | str = CSV_DIR,
    ) -> None:
        """
        Inicializa el cargador de documentos.

        Args:
            pdf_directory:
                Directorio donde se encuentran los archivos PDF.
            csv_directory:
                Directorio donde se encuentran los archivos CSV.
        """

        self.pdf_directory = Path(pdf_directory)
        self.csv_directory = Path(csv_directory)
        self.summary = LoadingSummary()

    @staticmethod
    def clean_text(text: str | None) -> str:
        """
        Limpia y normaliza texto extraído de documentos.

        Elimina espacios repetidos, tabulaciones, saltos innecesarios
        y caracteres de control que podrían afectar los embeddings.

        Args:
            text:
                Texto original.

        Returns:
            Texto limpio.
        """

        if not text:
            return ""

        cleaned_text = text.replace("\x00", " ")
        cleaned_text = cleaned_text.replace("\r\n", "\n")
        cleaned_text = cleaned_text.replace("\r", "\n")

        # Reemplaza tabulaciones y espacios repetidos.
        cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)

        # Evita más de dos saltos de línea consecutivos.
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        # Elimina espacios al inicio y final de cada línea.
        cleaned_lines = [
            line.strip()
            for line in cleaned_text.splitlines()
            if line.strip()
        ]

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def normalize_document_name(file_path: Path) -> str:
        """
        Convierte el nombre técnico de un archivo en un título legible.

        Ejemplo:
            guia_tiempos_costos_envio_bimbam_buy.pdf

        Resultado:
            Guia Tiempos Costos Envio Bimbam Buy
        """

        name_without_extension = file_path.stem
        normalized_name = name_without_extension.replace("_", " ")
        normalized_name = normalized_name.replace("-", " ")

        return " ".join(normalized_name.split()).title()

    @staticmethod
    def infer_category(file_path: Path) -> str:
        """
        Infiere una categoría básica mediante el nombre del archivo.

        Args:
            file_path:
                Ruta del documento.

        Returns:
            Categoría asignada al documento.
        """

        filename = file_path.stem.lower()

        category_keywords = {
            "shipping": ("envio", "entrega", "rastreo"),
            "refunds": ("reembolso", "devolucion"),
            "warranty": ("garantia",),
            "payments": ("pago", "pagos", "metodo"),
            "affiliates": ("afiliado", "afiliados"),
            "products": ("producto", "productos", "catalogo"),
            "privacy": ("privacidad", "datos"),
            "support": ("soporte", "preguntas", "faq"),
        }

        for category, keywords in category_keywords.items():
            if any(keyword in filename for keyword in keywords):
                return category

        return "general"

    def build_metadata(
        self,
        file_path: Path,
        file_type: str,
        **additional_metadata: object,
    ) -> dict[str, object]:
        """
        Construye los metadatos comunes de un documento.

        Args:
            file_path:
                Ruta del archivo de origen.
            file_type:
                Tipo del archivo, por ejemplo ``pdf`` o ``csv``.
            additional_metadata:
                Metadatos específicos, como página o número de fila.

        Returns:
            Diccionario con los metadatos del documento.
        """

        try:
            file_size_bytes = file_path.stat().st_size
        except OSError:
            file_size_bytes = 0

        metadata: dict[str, object] = {
            "source": file_path.name,
            "source_path": str(file_path.resolve()),
            "document_name": self.normalize_document_name(file_path),
            "file_type": file_type,
            "category": self.infer_category(file_path),
            "file_size_bytes": file_size_bytes,
            "loaded_at": datetime.now(timezone.utc).isoformat(),
        }

        metadata.update(additional_metadata)

        return metadata

    def find_pdf_files(self) -> list[Path]:
        """Encuentra todos los PDF del directorio configurado."""

        if not self.pdf_directory.exists():
            logger.warning(
                "No existe el directorio de PDF: %s",
                self.pdf_directory,
            )
            return []

        return sorted(
            file_path
            for file_path in self.pdf_directory.rglob(
                f"*{SUPPORTED_PDF_EXTENSION}"
            )
            if file_path.is_file()
        )

    def find_csv_files(self) -> list[Path]:
        """Encuentra todos los CSV del directorio configurado."""

        if not self.csv_directory.exists():
            logger.warning(
                "No existe el directorio de CSV: %s",
                self.csv_directory,
            )
            return []

        return sorted(
            file_path
            for file_path in self.csv_directory.rglob(
                f"*{SUPPORTED_CSV_EXTENSION}"
            )
            if file_path.is_file()
        )

    def load_pdf_file(self, file_path: Path) -> list[Document]:
        """
        Carga un PDF y crea un Document por cada página con texto.

        Args:
            file_path:
                Ruta del archivo PDF.

        Returns:
            Lista de páginas convertidas en objetos Document.
        """

        documents: list[Document] = []

        logger.info("Cargando PDF: %s", file_path.name)

        try:
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)

            for page_index, page in enumerate(reader.pages):
                extracted_text = page.extract_text()
                cleaned_text = self.clean_text(extracted_text)

                if not cleaned_text:
                    self.summary.empty_elements_skipped += 1

                    logger.warning(
                        "Página vacía omitida: %s, página %s",
                        file_path.name,
                        page_index + 1,
                    )
                    continue

                metadata = self.build_metadata(
                    file_path=file_path,
                    file_type="pdf",
                    page=page_index + 1,
                    total_pages=total_pages,
                )

                documents.append(
                    Document(
                        page_content=cleaned_text,
                        metadata=metadata,
                    )
                )

                self.summary.pdf_pages_loaded += 1

        except Exception as error:
            self.summary.files_with_errors += 1

            logger.exception(
                "No fue posible cargar el PDF %s: %s",
                file_path.name,
                error,
            )

        return documents

    def load_pdf_documents(self) -> list[Document]:
        """Carga todos los archivos PDF encontrados."""

        pdf_files = self.find_pdf_files()
        self.summary.pdf_files_found = len(pdf_files)

        if not pdf_files:
            logger.warning(
                "No se encontraron documentos PDF en %s",
                self.pdf_directory,
            )
            return []

        documents: list[Document] = []

        for file_path in pdf_files:
            documents.extend(self.load_pdf_file(file_path))

        return documents

    @staticmethod
    def row_to_text(
        row: pd.Series,
        row_number: int,
    ) -> str:
        """
        Convierte una fila de Pandas en texto legible.

        Args:
            row:
                Fila del DataFrame.
            row_number:
                Número de fila dentro del archivo.

        Returns:
            Representación textual de la fila.
        """

        row_lines = [f"Registro: {row_number}"]

        for column_name, value in row.items():
            if pd.isna(value):
                continue

            clean_column_name = str(column_name).strip()
            clean_value = str(value).strip()

            if not clean_value:
                continue

            row_lines.append(
                f"{clean_column_name}: {clean_value}"
            )

        return "\n".join(row_lines)

    def read_csv_with_fallback(self, file_path: Path) -> pd.DataFrame:
        """
        Lee un CSV intentando distintas codificaciones.

        Primero intenta UTF-8. Si falla, intenta UTF-8 con BOM
        y posteriormente latin-1.

        Args:
            file_path:
                Ruta del archivo CSV.

        Returns:
            DataFrame con la información cargada.

        Raises:
            UnicodeDecodeError:
                Si ninguna codificación permite leer el archivo.
        """

        encodings = ("utf-8", "utf-8-sig", "latin-1")
        last_error: UnicodeDecodeError | None = None

        for encoding in encodings:
            try:
                return pd.read_csv(
                    file_path,
                    encoding=encoding,
                )
            except UnicodeDecodeError as error:
                last_error = error

                logger.warning(
                    "No se pudo leer %s con codificación %s.",
                    file_path.name,
                    encoding,
                )

        if last_error is not None:
            raise last_error

        raise ValueError(
            f"No fue posible leer el archivo CSV: {file_path}"
        )

    def load_csv_file(self, file_path: Path) -> list[Document]:
        """
        Carga un CSV y crea un Document por cada fila válida.

        Args:
            file_path:
                Ruta del archivo CSV.

        Returns:
            Lista de filas convertidas en objetos Document.
        """

        documents: list[Document] = []

        logger.info("Cargando CSV: %s", file_path.name)

        try:
            dataframe = self.read_csv_with_fallback(file_path)

            for row_index, row in dataframe.iterrows():
                row_number = int(row_index) + 1
                row_text = self.row_to_text(row, row_number)
                cleaned_text = self.clean_text(row_text)

                if not cleaned_text:
                    self.summary.empty_elements_skipped += 1
                    continue

                metadata = self.build_metadata(
                    file_path=file_path,
                    file_type="csv",
                    row=row_number,
                    total_rows=len(dataframe),
                    columns=list(dataframe.columns),
                )

                documents.append(
                    Document(
                        page_content=cleaned_text,
                        metadata=metadata,
                    )
                )

                self.summary.csv_rows_loaded += 1

        except Exception as error:
            self.summary.files_with_errors += 1

            logger.exception(
                "No fue posible cargar el CSV %s: %s",
                file_path.name,
                error,
            )

        return documents

    def load_csv_documents(self) -> list[Document]:
        """Carga todos los archivos CSV encontrados."""

        csv_files = self.find_csv_files()
        self.summary.csv_files_found = len(csv_files)

        if not csv_files:
            logger.warning(
                "No se encontraron documentos CSV en %s",
                self.csv_directory,
            )
            return []

        documents: list[Document] = []

        for file_path in csv_files:
            documents.extend(self.load_csv_file(file_path))

        return documents

    def load_all_documents(self) -> list[Document]:
        """
        Carga todos los PDF y CSV de la base de conocimiento.

        Returns:
            Lista combinada de documentos.

        Raises:
            RuntimeError:
                Si no fue posible cargar ningún documento.
        """

        logger.info("Iniciando carga de la base de conocimiento.")

        # Reinicia las métricas si se reutiliza la misma instancia.
        self.summary = LoadingSummary()

        documents = [
            *self.load_pdf_documents(),
            *self.load_csv_documents(),
        ]

        if not documents:
            raise RuntimeError(
                "No se pudo cargar ningún documento. "
                "Verifica las carpetas documents/pdf y documents/csv."
            )

        logger.info(
            "Carga finalizada. Se generaron %s documentos.",
            len(documents),
        )

        return documents

    def get_sources(
        self,
        documents: Iterable[Document],
    ) -> list[str]:
        """
        Obtiene una lista sin duplicados de las fuentes cargadas.

        Args:
            documents:
                Documentos cargados.

        Returns:
            Nombres de los archivos fuente.
        """

        sources = {
            str(document.metadata.get("source", "desconocido"))
            for document in documents
        }

        return sorted(sources)

    def print_summary(self) -> None:
        """Imprime en los logs un resumen del proceso de carga."""

        separator = "=" * 58

        logger.info(separator)
        logger.info("RESUMEN DE LA BASE DE CONOCIMIENTO")
        logger.info(separator)
        logger.info(
            "Archivos PDF encontrados: %s",
            self.summary.pdf_files_found,
        )
        logger.info(
            "Archivos CSV encontrados: %s",
            self.summary.csv_files_found,
        )
        logger.info(
            "Páginas PDF cargadas: %s",
            self.summary.pdf_pages_loaded,
        )
        logger.info(
            "Filas CSV cargadas: %s",
            self.summary.csv_rows_loaded,
        )
        logger.info(
            "Elementos vacíos omitidos: %s",
            self.summary.empty_elements_skipped,
        )
        logger.info(
            "Archivos con errores: %s",
            self.summary.files_with_errors,
        )
        logger.info(
            "Total de objetos Document: %s",
            self.summary.total_documents,
        )
        logger.info(separator)


def load_knowledge_base() -> list[Document]:
    """
    Función de acceso rápido para cargar toda la base de conocimiento.

    Returns:
        Documentos PDF y CSV procesados.
    """

    loader = DocumentLoader()
    documents = loader.load_all_documents()
    loader.print_summary()

    return documents