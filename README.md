# BimBam Knowledge Assistant

Asistente inteligente basado en la arquitectura **Retrieval-Augmented Generation (RAG)** desarrollado para responder preguntas utilizando exclusivamente la documentación oficial de **BimBam Buy**.

El proyecto utiliza búsqueda semántica mediante **FAISS**, embeddings de **Google Gemini** y un modelo conversacional **Gemini 2.5 Flash**, todo integrado en una aplicación web desarrollada con **Streamlit**.

---

# Características

- Respuestas fundamentadas en documentación oficial.
- Recuperación semántica mediante FAISS.
- Embeddings utilizando Google Gemini.
- Modelo conversacional Gemini 2.5 Flash.
- Interfaz web desarrollada con Streamlit.
- Visualización de fuentes consultadas.
- Evidencias documentales utilizadas para responder.
- Arquitectura modular y escalable.

---

# Arquitectura

```
Usuario
      │
      ▼
Interfaz Streamlit
      │
      ▼
BimBamAgent
      │
      ▼
KnowledgeRetriever
      │
      ▼
Índice FAISS
      │
      ▼
Fragmentos relevantes
      │
      ▼
Prompt RAG
      │
      ▼
Google Gemini
      │
      ▼
Respuesta al usuario
```

---

# Tecnologías utilizadas

- Python
- Streamlit
- LangChain
- Google Gemini 2.5 Flash
- Gemini Embeddings
- FAISS
- python-dotenv

---

# Estructura del proyecto

```
challenge-alura-agente/

├── app.py
├── requirements.txt
├── README.md
│
├── documents/
│   ├── pdf/
│   └── csv/
│
├── src/
│   ├── agent.py
│   ├── config.py
│   ├── document_loader.py
│   ├── embeddings_manager.py
│   ├── logger.py
│   ├── prompts.py
│   ├── retriever.py
│   └── vector_store.py
│
├── data/
│
├── docs/
│
├── evidencias/
│
└── tests/
```

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/Edgar11-08/bimbam-knowledge-assistant.git
```

Entrar al proyecto:

```bash
cd bimbam-knowledge-assistant
```

---

## 2. Crear el entorno virtual

Windows

```bash
python -m venv .venv
```

Activar:

```bash
.venv\Scripts\activate
```

Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 4. Configurar variables de entorno

Crear un archivo llamado:

```
.env
```

Agregar:

```text
GEMINI_API_KEY=TU_API_KEY
```
**Nota:** Reemplaza `TU_API_KEY` por una API Key válida de Google Gemini. Esta clave es necesaria para generar embeddings y responder consultas mediante el modelo de lenguaje.
---

## 5. Construir el índice FAISS

```bash
python -c "from src.vector_store import VectorStoreManager; VectorStoreManager().create_or_load(force_rebuild=True)"
```

---

## 6. Ejecutar la aplicación

```bash
streamlit run app.py
```

---

# Ejemplos de preguntas

El asistente puede responder preguntas como:

- ¿Cuáles son los tiempos y costos de envío?
- ¿Cómo solicitar una devolución?
- ¿Qué métodos de pago acepta BimBam Buy?
- ¿Cómo funciona el programa de afiliados?
- ¿Cuánto dura la garantía?

Cuando la información no existe en la documentación, el sistema informa al usuario que la base de conocimiento no contiene información suficiente.

---

# Flujo de funcionamiento

1. El usuario escribe una pregunta.
2. El sistema realiza una búsqueda semántica en FAISS.
3. Se recuperan los fragmentos más relevantes.
4. Se construye el contexto documental.
5. Gemini genera la respuesta.
6. La aplicación muestra la respuesta junto con las fuentes y evidencias.

---

# Documentación

La documentación del proyecto se encuentra en la carpeta:

```
docs/
```

Incluye:

- architecture.md
- project_decisions.md
- prompts.md
- testing.md
- deployment_oci.md

---

# Pruebas

Durante el desarrollo se verificó:

- Carga de documentos.
- Construcción del índice FAISS.
- Recuperación semántica.
- Generación de respuestas.
- Manejo de preguntas sin evidencia.
- Funcionamiento de la interfaz Streamlit.

Los detalles se encuentran en:

```
docs/testing.md
```

---

# Capturas de pantalla

Las evidencias del proyecto se almacenan en:

```
evidencias/
```

Se recomienda incluir capturas de:

- Interfaz principal.
- Respuesta del asistente.
- Fuentes consultadas.
- Evidencias recuperadas.
- Despliegue en OCI.

---

# Autor

**Edgar Moreno Dominguez**

Proyecto desarrollado como parte del **Challenge Alura – Agentes Inteligentes**, utilizando la arquitectura Retrieval-Augmented Generation (RAG) y Google Gemini.