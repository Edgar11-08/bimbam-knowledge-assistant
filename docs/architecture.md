# Arquitectura del Proyecto

# BimBam Knowledge Assistant

## Descripción general

BimBam Knowledge Assistant es un asistente inteligente desarrollado mediante la arquitectura Retrieval-Augmented Generation (RAG). Su propósito es responder preguntas utilizando únicamente la documentación oficial de BimBam Buy, evitando generar respuestas sin respaldo documental.

El sistema combina recuperación semántica mediante FAISS, modelos de embeddings de Google Gemini y un modelo conversacional Gemini 2.5 Flash para construir respuestas precisas basadas exclusivamente en la base de conocimiento.

---

# Objetivos

El proyecto fue desarrollado con los siguientes objetivos:

- Construir un asistente inteligente basado en documentación.
- Implementar recuperación semántica mediante FAISS.
- Utilizar Google Gemini para generar respuestas fundamentadas.
- Reducir las alucinaciones del modelo.
- Mantener una arquitectura modular y escalable.
- Facilitar la incorporación de nuevos documentos sin modificar la lógica del sistema.

---

# Arquitectura general

El flujo general del sistema es el siguiente:

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
          Google Gemini 2.5 Flash
                       │
                       ▼
          Respuesta fundamentada
                       │
                       ▼
                Usuario final
```

---

# Diagrama de componentes

```
                   +----------------------+
                   |       Usuario        |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |      Streamlit       |
                   |      (app.py)        |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |    BimBamAgent       |
                   |     agent.py         |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   | KnowledgeRetriever   |
                   |   retriever.py       |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |      FAISS Index     |
                   |   vector_store.py    |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   | Gemini Embeddings    |
                   | embeddings_manager.py|
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   | Gemini 2.5 Flash     |
                   +----------------------+
```

---

# Organización del proyecto

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
├── docs/
│
├── evidencias/
│
├── tests/
│
├── data/
│   ├── faiss_index/
│   ├── processed_documents/
│   └── cache/
│
└── src/
    ├── config.py
    ├── logger.py
    ├── document_loader.py
    ├── embeddings_manager.py
    ├── vector_store.py
    ├── retriever.py
    ├── prompts.py
    └── agent.py
```

---

# Descripción de los módulos

## config.py

Centraliza toda la configuración del proyecto, incluyendo rutas, variables de entorno, modelos utilizados, parámetros del RAG y validaciones generales.

---

## logger.py

Implementa el sistema de registro de eventos. Permite monitorear la carga de documentos, creación del índice, consultas realizadas y posibles errores.

---

## document_loader.py

Carga automáticamente todos los documentos PDF y archivos CSV disponibles en la carpeta correspondiente. Además, genera los metadatos necesarios para su posterior procesamiento.

---

## embeddings_manager.py

Administra la creación de embeddings utilizando Google Gemini Embeddings. Este módulo encapsula toda la comunicación con el servicio de embeddings.

---

## vector_store.py

Construye y administra el índice vectorial mediante FAISS. Entre sus responsabilidades se encuentran:

- dividir documentos en fragmentos;
- generar embeddings;
- construir el índice;
- guardar y reutilizar el índice;
- realizar búsquedas vectoriales.

---

## retriever.py

Realiza la recuperación semántica. Selecciona los fragmentos más relevantes para responder cada consulta y construye el contexto que será enviado al modelo conversacional.

---

## prompts.py

Contiene todos los prompts utilizados por el sistema, incluyendo las instrucciones del modelo, mensajes de error, preguntas de ejemplo y restricciones para evitar respuestas inventadas.

---

## agent.py

Coordina todo el flujo del sistema:

- recibe la pregunta;
- recupera el contexto;
- construye el prompt;
- consulta Gemini;
- valida la respuesta;
- devuelve el resultado final.

---

## app.py

Implementa la interfaz web utilizando Streamlit. Permite conversar con el asistente, visualizar las fuentes consultadas y revisar las evidencias recuperadas.

---

# Flujo de una consulta

Cada pregunta realizada por el usuario sigue el siguiente proceso:

1. El usuario escribe una pregunta.
2. Streamlit envía la consulta al agente.
3. El agente solicita información al retriever.
4. El retriever consulta el índice FAISS.
5. FAISS devuelve los fragmentos más similares.
6. Se construye el contexto documental.
7. El agente genera el prompt.
8. Gemini produce una respuesta.
9. El agente valida la respuesta.
10. Streamlit presenta la respuesta junto con las fuentes y evidencias.

---

# Base de conocimiento

La base de conocimiento está formada por documentos PDF oficiales de BimBam Buy.

Durante el proceso de indexación cada documento es dividido automáticamente en fragmentos, lo que permite recuperar únicamente la información necesaria para responder cada pregunta.

---

# Recuperación semántica

El sistema utiliza FAISS como motor de búsqueda vectorial.

Cada fragmento documental es convertido en un embedding utilizando Google Gemini Embeddings.

Cuando el usuario realiza una consulta:

- la pregunta también se convierte en embedding;
- FAISS busca los vectores más similares;
- los fragmentos recuperados forman el contexto enviado al modelo.

Este proceso permite recuperar información aunque la pregunta no utilice exactamente las mismas palabras presentes en los documentos.

---

# Modelo conversacional

Las respuestas son generadas utilizando Google Gemini 2.5 Flash.

El modelo únicamente recibe los fragmentos recuperados por el retriever y nunca la totalidad de los documentos, reduciendo el consumo de tokens y minimizando las alucinaciones.

---

# Manejo de respuestas sin evidencia

Si la documentación no contiene información suficiente para responder una consulta, el sistema devuelve un mensaje estándar indicando que la base de conocimiento no posee información suficiente.

En estos casos no se muestran fuentes ni evidencias para evitar interpretaciones incorrectas.

---

# Tecnologías utilizadas

- Python
- Streamlit
- LangChain
- Google Gemini
- Gemini Embeddings
- FAISS
- python-dotenv

---

# Principios de diseño

Durante el desarrollo se siguieron los siguientes principios:

- modularidad;
- separación de responsabilidades;
- reutilización de componentes;
- configuración centralizada;
- escalabilidad;
- mantenibilidad;
- validación de errores;
- documentación del código.

---

# Resumen

La arquitectura implementada permite construir un asistente RAG robusto, modular y fácilmente escalable. Cada componente cumple una responsabilidad específica, facilitando el mantenimiento del proyecto y permitiendo incorporar nuevas fuentes documentales o modelos de inteligencia artificial sin modificar la arquitectura principal.