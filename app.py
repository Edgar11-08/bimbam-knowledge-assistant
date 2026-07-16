"""Interfaz web de BimBam Knowledge Assistant.

Aplicación conversacional desarrollada con Streamlit para consultar
la base de conocimiento oficial de BimBam Buy.
"""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from src.agent import AgentResponse, BimBamAgent
from src.config import (
    APP_DESCRIPTION,
    APP_NAME,
    CHAT_MODEL,
    EMBEDDING_MODEL,
    RETRIEVER_TOP_K,
)
from src.prompts import (
    EXAMPLE_QUESTIONS,
    WELCOME_MESSAGE,
    format_source_name,
)


# ---------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Estilos
# ---------------------------------------------------------

CUSTOM_CSS = """
<style>
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .app-header {
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 18px;
        background: rgba(128, 128, 128, 0.05);
    }

    .app-header h1 {
        margin: 0;
        font-size: 2rem;
    }

    .app-header p {
        margin: 0.55rem 0 0;
        opacity: 0.8;
    }

    .status-card {
        padding: 0.85rem 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(46, 160, 67, 0.35);
        border-radius: 12px;
        background: rgba(46, 160, 67, 0.08);
    }

    .source-card {
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.6rem;
        border-left: 4px solid #4f8bf9;
        border-radius: 8px;
        background: rgba(79, 139, 249, 0.08);
    }

    .evidence-metadata {
        padding: 0.8rem 1rem;
        margin-bottom: 0.8rem;
        border-radius: 10px;
        background: rgba(128, 128, 128, 0.07);
        line-height: 1.6;
    }

    .evidence-content {
        padding: 1rem;
        border-radius: 10px;
        background: rgba(128, 128, 128, 0.05);
        white-space: pre-wrap;
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .small-muted {
        font-size: 0.85rem;
        opacity: 0.72;
    }

    div[data-testid="stChatMessage"] {
        padding: 0.35rem 0;
    }

    div[data-testid="stChatInput"] {
        padding-bottom: 1rem;
    }
</style>
"""

st.markdown(
    CUSTOM_CSS,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Estado de la sesión
# ---------------------------------------------------------

def create_welcome_message() -> dict[str, Any]:
    """Construye el mensaje inicial del asistente."""

    return {
        "role": "assistant",
        "content": WELCOME_MESSAGE,
        "sources": [],
        "evidences": [],
        "success": True,
    }


def initialize_session_state() -> None:
    """Inicializa las variables utilizadas durante la sesión."""

    if "messages" not in st.session_state:
        st.session_state.messages = [
            create_welcome_message()
        ]

    if "agent" not in st.session_state:
        st.session_state.agent = None

    if "agent_error" not in st.session_state:
        st.session_state.agent_error = None

    if "selected_question" not in st.session_state:
        st.session_state.selected_question = None


def clear_conversation() -> None:
    """Reinicia el historial de la conversación."""

    st.session_state.messages = [
        create_welcome_message()
    ]

    st.session_state.selected_question = None


def initialize_agent() -> BimBamAgent | None:
    """
    Inicializa el agente una sola vez por sesión.

    Returns:
        Instancia del agente o None si ocurrió un error.
    """

    if st.session_state.agent is not None:
        return st.session_state.agent

    try:
        with st.spinner(
            "Preparando el asistente y cargando "
            "la base de conocimiento..."
        ):
            st.session_state.agent = BimBamAgent()

        st.session_state.agent_error = None

        return st.session_state.agent

    except Exception as error:
        st.session_state.agent_error = str(error)
        return None


# ---------------------------------------------------------
# Conversión y presentación de respuestas
# ---------------------------------------------------------

def response_to_message(
    response: AgentResponse,
) -> dict[str, Any]:
    """
    Convierte una AgentResponse en datos para la interfaz.

    Args:
        response:
            Respuesta generada por el agente.

    Returns:
        Diccionario para almacenarse en el historial.
    """

    evidences: list[dict[str, Any]] = []

    for item in response.retrieval_items:
        metadata = item.document.metadata

        evidences.append(
            {
                "source": item.source,
                "document_name": item.document_name,
                "location": item.location,
                "category": item.category,
                "score": float(item.score),
                "chunk_id": metadata.get(
                    "chunk_id",
                    "sin-identificador",
                ),
                "content": (
                    item.document.page_content.strip()
                ),
            }
        )

    return {
        "role": "assistant",
        "content": response.answer,
        "sources": response.sources,
        "evidences": evidences,
        "success": response.success,
        "error_message": response.error_message,
        "model_name": response.model_name,
        "context_characters": (
            response.context_characters
        ),
    }


def render_sources(
    sources: list[str],
) -> None:
    """Muestra las fuentes documentales de una respuesta."""

    if not sources:
        return

    with st.expander(
        f"Fuentes consultadas ({len(sources)})",
        expanded=False,
    ):
        for source in sources:
            source_name = format_source_name(
                source
            )

            st.markdown(
                (
                    '<div class="source-card">'
                    f"<strong>{escape(source_name)}</strong><br>"
                    '<span class="small-muted">'
                    f"{escape(source)}"
                    "</span>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def build_evidence_preview(
    content: str,
    max_characters: int = 240,
) -> str:
    """
    Construye una vista previa corta del contenido.

    Args:
        content:
            Texto completo de la evidencia.
        max_characters:
            Cantidad máxima de caracteres visibles.

    Returns:
        Vista previa del fragmento.
    """

    clean_content = " ".join(
        content.split()
    )

    if len(clean_content) <= max_characters:
        return clean_content

    return (
        clean_content[:max_characters].rstrip()
        + "..."
    )


def render_evidences(
    evidences: list[dict[str, Any]],
) -> None:
    """Muestra cada evidencia dentro de un desplegable."""

    if not evidences:
        return

    st.markdown(
        f"**Evidencias recuperadas ({len(evidences)})**"
    )

    for index, evidence in enumerate(
        evidences,
        start=1,
    ):
        preview = build_evidence_preview(
            evidence["content"]
        )

        expander_title = (
            f"Evidencia {index} — "
            f"{evidence['document_name']} — "
            f"{evidence['location']}"
        )

        with st.expander(
            expander_title,
            expanded=False,
        ):
            st.markdown(
                (
                    '<div class="evidence-metadata">'
                    f"<strong>Documento:</strong> "
                    f"{escape(evidence['document_name'])}<br>"
                    f"<strong>Ubicación:</strong> "
                    f"{escape(evidence['location'])}<br>"
                    f"<strong>Categoría:</strong> "
                    f"{escape(evidence['category'])}<br>"
                    f"<strong>Fragmento:</strong> "
                    f"{escape(str(evidence['chunk_id']))}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            st.caption(
                f"Vista previa: {preview}"
            )

            st.markdown(
                "**Contenido completo de la evidencia:**"
            )

            st.markdown(
                (
                    '<div class="evidence-content">'
                    f"{escape(evidence['content'])}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def render_message(
    message: dict[str, Any],
) -> None:
    """Muestra un mensaje guardado en el historial."""

    role = message.get(
        "role",
        "assistant",
    )

    # Sin iconos ni avatares dentro del chat.
    with st.chat_message(role):
        st.markdown(
            message.get(
                "content",
                "",
            )
        )

        if role == "assistant":
            render_sources(
                message.get(
                    "sources",
                    [],
                )
            )

            render_evidences(
                message.get(
                    "evidences",
                    [],
                )
            )

            if not message.get(
                "success",
                True,
            ):
                st.error(
                    "La consulta no pudo completarse "
                    "correctamente."
                )


# ---------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------

def render_sidebar(
    agent_available: bool,
) -> None:
    """Construye el panel lateral de la aplicación."""

    with st.sidebar:
        # Se conserva el icono principal.
        st.title("🛍️ BimBam Buy")

        st.caption(
            "Asistente inteligente basado en "
            "documentación oficial."
        )

        if agent_available:
            st.markdown(
                """
                <div class="status-card">
                    <strong>Sistema disponible</strong><br>
                    <span class="small-muted">
                        La base de conocimiento está lista.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.error(
                "El asistente no está disponible."
            )

        # Se conserva el icono de configuración.
        st.subheader("⚙️ Configuración")

        st.text(
            f"Modelo: {CHAT_MODEL}"
        )
        st.text(
            f"Embeddings: {EMBEDDING_MODEL}"
        )
        st.text(
            f"Resultados RAG: {RETRIEVER_TOP_K}"
        )

        st.divider()

        # Se conserva el icono de preguntas frecuentes.
        st.subheader(
            "❓ Preguntas frecuentes"
        )

        for index, example_question in enumerate(
            EXAMPLE_QUESTIONS,
            start=1,
        ):
            if st.button(
                example_question,
                key=f"example-question-{index}",
                use_container_width=True,
                disabled=not agent_available,
            ):
                st.session_state.selected_question = (
                    example_question
                )

        st.divider()

        if st.button(
            "Limpiar conversación",
            use_container_width=True,
        ):
            clear_conversation()
            st.rerun()

        st.caption(
            "Las respuestas se generan únicamente "
            "con la información contenida en la "
            "base documental de BimBam Buy."
        )


# ---------------------------------------------------------
# Procesamiento de preguntas
# ---------------------------------------------------------

def process_question(
    question: str,
    agent: BimBamAgent,
) -> None:
    """
    Procesa una pregunta y agrega la respuesta al historial.

    Args:
        question:
            Consulta escrita o seleccionada.
        agent:
            Instancia del agente RAG.
    """

    clean_question = " ".join(
        question.split()
    )

    if not clean_question:
        return

    user_message = {
        "role": "user",
        "content": clean_question,
        "sources": [],
        "evidences": [],
        "success": True,
    }

    st.session_state.messages.append(
        user_message
    )

    render_message(
        user_message
    )

    # Mensaje del asistente sin avatar.
    with st.chat_message(
        "assistant"
    ):
        try:
            with st.spinner(
                "Consultando la base de conocimiento..."
            ):
                response = agent.answer(
                    clean_question
                )

            assistant_message = (
                response_to_message(
                    response
                )
            )

            st.markdown(
                assistant_message["content"]
            )

            render_sources(
                assistant_message["sources"]
            )

            render_evidences(
                assistant_message["evidences"]
            )

            if not response.success:
                st.error(
                    "No fue posible completar "
                    "la consulta."
                )

            st.session_state.messages.append(
                assistant_message
            )

        except ValueError as error:
            error_message = {
                "role": "assistant",
                "content": str(error),
                "sources": [],
                "evidences": [],
                "success": False,
                "error_message": str(error),
            }

            st.warning(
                str(error)
            )

            st.session_state.messages.append(
                error_message
            )

        except Exception as error:
            error_message = {
                "role": "assistant",
                "content": (
                    "No fue posible procesar tu consulta "
                    "en este momento. Inténtalo nuevamente."
                ),
                "sources": [],
                "evidences": [],
                "success": False,
                "error_message": str(error),
            }

            st.error(
                error_message["content"]
            )

            st.session_state.messages.append(
                error_message
            )


# ---------------------------------------------------------
# Aplicación principal
# ---------------------------------------------------------

def main() -> None:
    """Ejecuta la interfaz principal de Streamlit."""

    initialize_session_state()

    # Se conserva el icono del título del asistente.
    st.markdown(
        (
            '<div class="app-header">'
            f"<h1>🛍️ {escape(APP_NAME)}</h1>"
            f"<p>{escape(APP_DESCRIPTION)}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    agent = initialize_agent()
    agent_available = agent is not None

    render_sidebar(
        agent_available=agent_available
    )

    if not agent_available:
        st.error(
            "No fue posible inicializar el asistente."
        )

        if st.session_state.agent_error:
            with st.expander(
                "Ver detalle técnico",
                expanded=False,
            ):
                st.code(
                    st.session_state.agent_error
                )

        st.info(
            "Verifica la API Key de Gemini, "
            "la cuota disponible y que el índice "
            "FAISS esté correctamente generado."
        )

        st.stop()

    for message in st.session_state.messages:
        render_message(
            message
        )

    selected_question = (
        st.session_state.selected_question
    )

    typed_question = st.chat_input(
        "Escribe una pregunta sobre BimBam Buy...",
        disabled=not agent_available,
    )

    question_to_process = (
        typed_question
        if typed_question
        else selected_question
    )

    if question_to_process:
        st.session_state.selected_question = None

        process_question(
            question=question_to_process,
            agent=agent,
        )


if __name__ == "__main__":
    main()