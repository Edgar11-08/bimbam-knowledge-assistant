# Pruebas del Sistema

# BimBam Knowledge Assistant

## Introducción

Durante el desarrollo del proyecto se realizaron diversas pruebas funcionales con el objetivo de verificar el correcto funcionamiento de cada uno de los componentes del sistema.

Las pruebas abarcan desde la carga de documentos hasta la generación de respuestas utilizando la arquitectura Retrieval-Augmented Generation (RAG).

---

# Objetivos de las pruebas

Las pruebas realizadas buscan verificar:

- correcta carga de la documentación;
- generación de embeddings;
- construcción del índice FAISS;
- recuperación semántica;
- generación de respuestas;
- funcionamiento de la interfaz web;
- manejo de errores;
- comportamiento ante preguntas sin respuesta.

---

# Entorno de pruebas

Las pruebas fueron realizadas utilizando el siguiente entorno:

| Componente | Configuración |
|------------|---------------|
| Lenguaje | Python 3.x |
| Sistema Operativo | Windows 11 |
| Modelo conversacional | Gemini 2.5 Flash |
| Modelo de embeddings | Gemini Embedding |
| Motor vectorial | FAISS |
| Framework | Streamlit |
| Framework RAG | LangChain |

---

# Prueba 1 - Carga de documentos

## Objetivo

Verificar que el sistema detecte y cargue correctamente todos los documentos disponibles.

## Resultado esperado

- detectar todos los documentos;
- generar objetos Document;
- crear metadatos correctamente.

## Resultado obtenido

La carga se realizó correctamente.

Se detectaron todos los documentos PDF disponibles y fueron convertidos en objetos Document para su posterior procesamiento.

**Resultado:** ✅ Aprobada

---

# Prueba 2 - Generación de embeddings

## Objetivo

Verificar la comunicación con Gemini Embeddings.

## Resultado esperado

Generar correctamente un embedding para cada fragmento documental.

## Resultado obtenido

Todos los fragmentos fueron convertidos correctamente en vectores utilizando Gemini Embeddings.

**Resultado:** ✅ Aprobada

---

# Prueba 3 - Construcción del índice FAISS

## Objetivo

Comprobar la creación del índice vectorial.

## Resultado esperado

Construcción y almacenamiento del índice.

## Resultado obtenido

El índice fue construido correctamente y almacenado para su reutilización.

**Resultado:** ✅ Aprobada

---

# Prueba 4 - Reutilización del índice

## Objetivo

Verificar que el sistema reutilice un índice existente cuando no existan cambios en la documentación.

## Resultado esperado

Evitar reconstrucciones innecesarias.

## Resultado obtenido

El sistema detectó que el índice se encontraba actualizado y lo reutilizó correctamente.

**Resultado:** ✅ Aprobada

---

# Prueba 5 - Recuperación semántica

## Objetivo

Comprobar que FAISS recupere los fragmentos más relevantes.

## Consulta utilizada

```
¿Cuáles son los tiempos y costos de envío?
```

## Resultado obtenido

El sistema recuperó correctamente los fragmentos pertenecientes al documento oficial de tiempos y costos de envío.

Las evidencias fueron utilizadas posteriormente para construir la respuesta.

**Resultado:** ✅ Aprobada

---

# Prueba 6 - Generación de respuestas

## Objetivo

Verificar la integración completa entre Retriever y Gemini.

## Consulta utilizada

```
¿Cómo solicitar una devolución?
```

## Resultado obtenido

El asistente respondió correctamente utilizando únicamente la documentación recuperada por el sistema RAG.

**Resultado:** ✅ Aprobada

---

# Prueba 7 - Pregunta sin información disponible

## Consulta utilizada

```
¿Quién es el presidente de BimBam Buy y cuál es su número telefónico personal?
```

## Resultado esperado

El sistema debe indicar que no existe información suficiente y no mostrar fuentes.

## Resultado obtenido

El asistente respondió indicando que no existe información suficiente en la base de conocimiento.

Las fuentes recuperadas fueron descartadas automáticamente al no contener evidencia relacionada con la consulta.

**Resultado:** ✅ Aprobada

---

# Prueba 8 - Interfaz Streamlit

## Objetivo

Verificar el funcionamiento de la aplicación web.

## Resultado esperado

- carga correcta;
- conversación con el asistente;
- visualización de respuestas;
- visualización de fuentes;
- visualización de evidencias.

## Resultado obtenido

La interfaz funcionó correctamente durante todas las pruebas realizadas.

**Resultado:** ✅ Aprobada

---

# Prueba 9 - Manejo de errores

## Objetivo

Verificar el comportamiento ante errores de configuración.

## Casos evaluados

- ausencia de API Key;
- índice inexistente;
- documentos no encontrados.

## Resultado obtenido

El sistema detectó correctamente los errores y mostró mensajes informativos al usuario.

**Resultado:** ✅ Aprobada

---

# Resumen de pruebas

| Prueba | Estado |
|---------|--------|
| Carga de documentos | ✅ |
| Embeddings | ✅ |
| Índice FAISS | ✅ |
| Reutilización del índice | ✅ |
| Recuperación semántica | ✅ |
| Generación de respuestas | ✅ |
| Preguntas sin evidencia | ✅ |
| Interfaz Streamlit | ✅ |
| Manejo de errores | ✅ |

---

# Resultados generales

Las pruebas realizadas demuestran que todos los componentes principales del sistema funcionan correctamente y se integran de forma adecuada.

La arquitectura Retrieval-Augmented Generation permite responder preguntas utilizando únicamente información contenida en la documentación oficial de BimBam Buy, reduciendo significativamente la generación de respuestas sin respaldo documental.

---

# Evidencias

Las capturas de pantalla correspondientes a las pruebas realizadas se almacenan en la carpeta:

```
evidencias/
```

Estas evidencias muestran el funcionamiento de la interfaz, la recuperación semántica, las respuestas generadas y la correcta integración de todos los componentes del sistema.

---

# Conclusión

Las pruebas realizadas permitieron verificar el correcto funcionamiento del sistema en cada una de sus etapas.

Los resultados obtenidos confirman que BimBam Knowledge Assistant cumple con el objetivo de proporcionar respuestas fundamentadas utilizando exclusivamente la documentación oficial de BimBam Buy.