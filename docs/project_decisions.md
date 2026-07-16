# Decisiones de Diseño del Proyecto

# BimBam Knowledge Assistant

## Introducción

Durante el desarrollo del proyecto se tomaron diversas decisiones de diseño con el objetivo de construir un asistente inteligente modular, mantenible y fácil de escalar. Cada tecnología fue seleccionada considerando su facilidad de integración, rendimiento y compatibilidad con la arquitectura Retrieval-Augmented Generation (RAG).

---

# Uso de la arquitectura RAG

Se eligió una arquitectura Retrieval-Augmented Generation (RAG) debido a que permite generar respuestas fundamentadas utilizando únicamente la información contenida en la base documental.

A diferencia de un modelo de lenguaje tradicional, RAG incorpora un proceso de recuperación semántica previo a la generación de la respuesta. Esto reduce considerablemente las alucinaciones y mejora la precisión de las respuestas al trabajar únicamente con información previamente indexada.

---

# Uso de Google Gemini

Se seleccionó Google Gemini 2.5 Flash como modelo conversacional por las siguientes razones:

- Excelente comprensión del lenguaje natural.
- Integración sencilla mediante LangChain.
- Buen rendimiento en tareas de preguntas y respuestas.
- Baja latencia para aplicaciones conversacionales.
- Capacidad para trabajar con grandes cantidades de contexto.

El modelo únicamente recibe el contexto recuperado por el sistema RAG, evitando el uso de información externa.

---

# Uso de Gemini Embeddings

Para la representación vectorial de los documentos se utilizaron Gemini Embeddings.

Las principales razones fueron:

- Compatibilidad con Gemini.
- Buena representación semántica del contenido.
- Integración sencilla mediante LangChain.
- Calidad en la búsqueda por similitud.

Los embeddings permiten convertir tanto los documentos como las preguntas del usuario en vectores numéricos comparables.

---

# Uso de FAISS

Se eligió FAISS como motor de búsqueda vectorial debido a:

- Alta velocidad de búsqueda.
- Excelente rendimiento incluso con grandes volúmenes de información.
- Facilidad para guardar y reutilizar índices.
- Integración directa con LangChain.

FAISS actúa como el componente encargado de recuperar los fragmentos más relevantes antes de consultar el modelo de lenguaje.

---

# Uso de LangChain

LangChain fue utilizado como framework principal para integrar todos los componentes del sistema.

Entre sus ventajas destacan:

- Integración con modelos de lenguaje.
- Compatibilidad con FAISS.
- Manejo de prompts.
- Gestión de documentos.
- Abstracción de componentes RAG.

Su uso permitió desarrollar una arquitectura modular y organizada.

---

# Uso de Streamlit

La interfaz gráfica fue desarrollada utilizando Streamlit.

Las razones principales fueron:

- Desarrollo rápido.
- Interfaz web sencilla.
- Integración directa con Python.
- Facilidad para mostrar conversaciones.
- Compatible con despliegues ligeros.

Streamlit permitió construir una aplicación funcional sin necesidad de desarrollar un frontend independiente.

---

# División de documentos

Los documentos no son enviados completos al modelo.

Cada documento es dividido automáticamente en fragmentos de tamaño controlado.

Esta decisión presenta varias ventajas:

- Reduce el número de tokens enviados.
- Incrementa la precisión de la búsqueda.
- Disminuye el costo de procesamiento.
- Permite recuperar únicamente la información relevante.

---

# Separación por módulos

Cada componente del proyecto fue desarrollado como un módulo independiente.

Esta organización facilita:

- mantenimiento;
- reutilización;
- pruebas;
- escalabilidad;
- incorporación de nuevas funcionalidades.

Cada archivo tiene una responsabilidad claramente definida.

---

# Configuración centralizada

Toda la configuración del proyecto se concentra en `config.py`.

Esto evita valores duplicados dentro del código y permite modificar parámetros importantes desde un único punto.

Entre ellos:

- modelos utilizados;
- tamaño de fragmentos;
- rutas;
- parámetros del retriever;
- configuración del índice FAISS.

---

# Uso de variables de entorno

La API Key de Gemini no se almacena dentro del código fuente.

Se utiliza un archivo `.env` para proteger la información sensible.

Esta práctica mejora la seguridad del proyecto y facilita su despliegue en distintos entornos.

---

# Validación de respuestas

El agente verifica si existe evidencia suficiente antes de mostrar una respuesta.

Cuando la documentación no contiene información relacionada con la consulta, el sistema informa al usuario que no existe información suficiente en la base de conocimiento y evita mostrar fuentes irrelevantes.

Esta decisión reduce el riesgo de interpretar incorrectamente los resultados.

---

# Registro de eventos

Se implementó un sistema de logging para registrar:

- carga de documentos;
- creación del índice;
- recuperación de información;
- consultas;
- errores.

Esto facilita la depuración y el mantenimiento del sistema.

---

# Escalabilidad

La arquitectura fue diseñada para permitir futuras ampliaciones sin modificar la estructura principal.

Entre las posibles mejoras se encuentran:

- incorporación de nuevos documentos;
- soporte para otros formatos de archivo;
- nuevos modelos de lenguaje;
- diferentes motores vectoriales;
- integración con bases de datos externas.

---

# Conclusión

Las decisiones de diseño adoptadas permitieron construir un sistema modular, organizado y fácil de mantener. La combinación de RAG, FAISS, Gemini, LangChain y Streamlit proporciona una solución eficiente para responder preguntas utilizando únicamente información respaldada por la documentación oficial de BimBam Buy.