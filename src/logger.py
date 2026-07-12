"""Configuración centralizada del sistema de logs."""

import logging
import sys

LOGGER_NAME = "BimBamKnowledgeAssistant"


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Devuelve un logger configurado para el proyecto.

    Args:
        name: Nombre opcional del módulo que solicita el logger.

    Returns:
        Logger configurado.
    """

    logger_name = LOGGER_NAME if not name else f"{LOGGER_NAME}.{name}"
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger