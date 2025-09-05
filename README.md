🔥 Pokémon Team Builder Analítico ϞϞ(๑⚈ . ̫ ⚈๑)∩ (⦿)

📖 Resumen del Proyecto
Pokémon Team Builder Analítico es una aplicación web interactiva desarrollada como proyecto final para la materia de Bases de Datos. La aplicación permite a los usuarios construir equipos Pokémon de hasta seis miembros y recibir un análisis de vulnerabilidad exhaustivo y en tiempo real, basado en una base de datos relacional robusta construida en MySQL.

El núcleo del proyecto es demostrar un diseño de base de datos avanzado, capaz de manejar datos complejos como las múltiples formas de un Pokémon (Mega Evoluciones, formas Primal, etc.), y el uso de consultas SQL complejas para proveer análisis estratégicos que de otra manera serían imposibles de obtener.

La interfaz, construida con Streamlit, consume los datos procesados y presenta los análisis de forma visual e intuitiva.

✨ Características Principales
Constructor de Equipos Interactivo: Selecciona hasta 6 Pokémon de una lista completa de 800 entradas (incluyendo formas alternativas).

Análisis de Equipo por Matriz de Vulnerabilidad: En lugar de un simple conteo, la aplicación calcula un "score" de vulnerabilidad para cada uno de los 18 tipos de ataque. Un score positivo (rojo) indica una debilidad, mientras que un score negativo (verde) indica una resistencia o inmunidad.

Base de Datos Robusta con Limpieza de Datos: El proyecto incluye un script de preparación (import_mejorado.py) que lee, limpia, procesa y estandariza los datos de múltiples fuentes CSV, resolviendo problemas como nombres inconsistentes, datos duplicados (formas alternativas) y conflicto de idiomas en los datos de origen.

Visualizaciones Avanzadas: Gráficos interactivos que muestran el incremento de poder de las Mega Evoluciones y un diagrama de pastel de los Pokémon con más formas, todo generado a partir de Vistas (Views) en la base de datos.

Lógica de Negocio en la Base de Datos: Implementación de Procedimientos Almacenados para búsquedas complejas y Triggers para mantener la integridad de los datos (ej. limitar un equipo a 6 miembros).

🛠️ Stack Tecnológico
Lenguaje de Programación: Python 3.10+

Base de Datos: MySQL

Frontend y Aplicación Web: Streamlit

Análisis y Manipulación de Datos: Pandas

Visualizaciones: Plotly Express

Conector de Base de Datos: mysql-connector-python