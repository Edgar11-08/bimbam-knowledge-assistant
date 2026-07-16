# Diseño de Prompts

# BimBam Knowledge Assistant

## Introducción

El comportamiento del asistente está controlado mediante prompts cuidadosamente diseñados para garantizar que las respuestas sean claras, precisas y estén respaldadas únicamente por la documentación oficial de BimBam Buy.

El sistema utiliza la técnica Retrieval-Augmented Generation (RAG), donde el modelo de lenguaje únicamente recibe los fragmentos recuperados por el sistema de búsqueda semántica.

---

# Objetivos del Prompt

El prompt fue diseñado con los siguientes objetivos:

- responder únicamente utilizando el contexto documental;
- evitar respuestas inventadas;
- mantener un lenguaje claro y profesional;
- impedir que el modelo utilice conocimiento externo;
- mostrar información verificable.

---

# Arquitectura del Prompt

La conversación enviada al modelo está formada por dos partes principales:

## Prompt del sistema

Contiene las instrucciones permanentes del asistente.

Entre ellas:

- comportamiento esperado;
- restricciones;
- tono de respuesta;
- manejo de información insuficiente;
- protección contra alucinaciones.

---

## Prompt del usuario

Incluye dos elementos dinámicos:

- el contexto recuperado por FAISS;
- la pregunta realizada por el usuario.

La estructura general es la siguiente:

```
CONTEXTO DOCUMENTAL

(fragmentos recuperados)

PREGUNTA

(pregunta del usuario)
```

---

# Construcción del contexto

Antes de consultar Gemini, el sistema recupera los fragmentos más relevantes utilizando FAISS.

Cada fragmento contiene:

- contenido;
- documento de origen;
- página;
- categoría;
- identificador del fragmento.

Todos estos fragmentos se concatenan para formar el contexto enviado al modelo.

---

# Restricciones del modelo

El prompt establece una serie de reglas obligatorias.

Entre ellas:

- responder únicamente utilizando el contexto recibido;
- no utilizar conocimiento externo;
- no inventar fechas;
- no inventar nombres;
- no inventar políticas;
- no inventar precios;
- responder siempre en español;
- mantener un tono profesional.

Estas restricciones buscan reducir la probabilidad de generar información incorrecta.

---

# Manejo de información insuficiente

Cuando el contexto recuperado no contiene información suficiente para responder una pregunta, el modelo debe responder utilizando un mensaje estándar.

Ejemplo:

```
No encontré información suficiente en la base de conocimiento de BimBam Buy.
```

Posteriormente el agente elimina las fuentes recuperadas para evitar que el usuario interprete incorrectamente que existe documentación relacionada.

---

# Prevención de alucinaciones

Para minimizar respuestas inventadas se implementaron varias estrategias:

- recuperación semántica mediante FAISS;
- contexto limitado únicamente a documentos oficiales;
- instrucciones explícitas dentro del prompt;
- validación posterior de la respuesta;
- eliminación de fuentes cuando no existe evidencia suficiente.

Estas medidas reducen significativamente la posibilidad de generar información falsa.

---

# Formato de las respuestas

Las respuestas generadas por el asistente siguen las siguientes características:

- lenguaje claro;
- redacción profesional;
- listas cuando la información lo requiere;
- conservación de fechas, cantidades y condiciones originales;
- ausencia de información externa.

Cuando existen varios pasos o requisitos, la respuesta utiliza listas para facilitar la lectura.

---

# Ejemplos de preguntas

El sistema fue diseñado para responder consultas como:

- ¿Cuáles son los tiempos y costos de envío?
- ¿Cómo funciona el programa de afiliados?
- ¿Qué métodos de pago acepta BimBam Buy?
- ¿Cómo solicitar una devolución?
- ¿Cuánto dura la garantía?

También identifica preguntas que no pueden responderse porque no existen dentro de la documentación.

---

# Flujo del Prompt

El proceso completo es el siguiente:

```
Usuario

↓

Pregunta

↓

Retriever

↓

FAISS

↓

Fragmentos relevantes

↓

Construcción del contexto

↓

Prompt del sistema

+

Prompt del usuario

↓

Gemini

↓

Respuesta

↓

Validación

↓

Usuario
```

---

# Beneficios del diseño

El diseño del prompt proporciona las siguientes ventajas:

- respuestas consistentes;
- menor cantidad de alucinaciones;
- utilización exclusiva de información oficial;
- facilidad para incorporar nuevos documentos;
- comportamiento uniforme del asistente.

---

# Conclusión

El prompt constituye uno de los componentes más importantes del sistema, ya que define el comportamiento del modelo de lenguaje y garantiza que las respuestas estén fundamentadas únicamente en la documentación oficial de BimBam Buy.
