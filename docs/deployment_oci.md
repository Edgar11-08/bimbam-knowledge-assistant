# Despliegue en Oracle Cloud Infrastructure (OCI)

# BimBam Knowledge Assistant

## Introducción

Este documento describe el procedimiento para desplegar BimBam Knowledge Assistant en una máquina virtual de Oracle Cloud Infrastructure (OCI).

El objetivo del despliegue es permitir el acceso al asistente mediante una interfaz web pública utilizando Streamlit.

---

# Requisitos

Antes de iniciar el despliegue se requiere:

- Cuenta activa en Oracle Cloud Infrastructure.
- Instancia Linux creada.
- Acceso mediante SSH.
- Python 3.11 o superior.
- Git.
- Conexión a Internet.
- API Key de Google Gemini.

---

# Tecnologías utilizadas

- Oracle Cloud Infrastructure (OCI)
- Ubuntu Server
- Python
- Streamlit
- Git
- Google Gemini
- FAISS

---

# Preparación del servidor

Actualizar los paquetes del sistema:

```bash
sudo apt update
sudo apt upgrade -y
```

Instalar Python y herramientas necesarias:

```bash
sudo apt install python3 python3-pip python3-venv git -y
```

---

# Clonar el repositorio

Clonar el proyecto desde GitHub:

```bash
git clone https://github.com/USUARIO/bimbam-knowledge-assistant.git
```

Ingresar al directorio:

```bash
cd bimbam-knowledge-assistant
```

---

# Crear el entorno virtual

```bash
python3 -m venv .venv
```

Activar el entorno:

```bash
source .venv/bin/activate
```

---

# Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Configurar variables de entorno

Crear el archivo `.env` en la raíz del proyecto.

Ejemplo:

```text
GEMINI_API_KEY=TU_API_KEY
```

---

# Construcción del índice FAISS

Generar el índice vectorial ejecutando:

```bash
python -c "from src.vector_store import VectorStoreManager; VectorStoreManager().create_or_load(force_rebuild=True)"
```

Una vez generado, el sistema reutilizará el índice automáticamente.

---

# Ejecutar la aplicación

Iniciar Streamlit:

```bash
streamlit run app.py
```

Por defecto la aplicación estará disponible en:

```
http://localhost:8501
```

---

# Configuración de red

Para permitir el acceso desde Internet es necesario:

- abrir el puerto 8501 en OCI;
- configurar las reglas del Security List;
- permitir conexiones TCP entrantes.

---

# Verificación

Una vez iniciado el servicio se recomienda comprobar:

- carga correcta de la aplicación;
- conexión con Gemini;
- carga del índice FAISS;
- funcionamiento del asistente;
- recuperación de documentos.

---

# Evidencias del despliegue

Después del despliegue deberán agregarse capturas de:

- creación de la instancia;
- consola SSH;
- aplicación funcionando;
- URL pública.

Estas evidencias se almacenarán en:

```
evidencias/oci/
```

---

# Posibles problemas

## API Key incorrecta

Verificar el contenido del archivo `.env`.

---

## Dependencias faltantes

Ejecutar nuevamente:

```bash
pip install -r requirements.txt
```

---

## Índice inexistente

Reconstruir el índice utilizando:

```bash
python -c "from src.vector_store import VectorStoreManager; VectorStoreManager().create_or_load(force_rebuild=True)"
```

---

## Puerto bloqueado

Verificar las reglas del firewall y del Security List de OCI.

---

# Conclusión

El despliegue en Oracle Cloud Infrastructure permite ejecutar BimBam Knowledge Assistant como una aplicación web accesible desde Internet.

Gracias a la arquitectura modular del proyecto, el proceso de despliegue es sencillo y puede repetirse fácilmente en nuevos entornos.