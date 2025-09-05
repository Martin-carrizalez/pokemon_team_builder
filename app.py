# Archivo: app.py (Versión 100% COMPLETA Y FUNCIONAL - CORREGIDA)

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
# ¡¡¡RECUERDA CAMBIAR ESTO POR TU CONTRASEÑA!!!
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '2076O8233e*', 
    'database': 'pokemon_team_builder'
}

# --- Funciones para acceder a la BD (con caché para velocidad) ---
@st.cache_resource
def get_connection():
    """Establece conexión con la base de datos."""
    return mysql.connector.connect(**DB_CONFIG)

@st.cache_data
def run_query(query, params=None):
    """Ejecuta una consulta SQL y devuelve los resultados como un DataFrame."""
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Error en la consulta a la base de datos: {e}")
        return pd.DataFrame()

def call_stored_procedure(query):
    """Función para llamar procedimientos almacenados"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(result)
    except Exception as e:
        st.error(f"Error ejecutando procedimiento: {e}")
        return pd.DataFrame()

# --- INICIO DE LA APP ---
st.set_page_config(layout="wide", page_title="Pokémon Team Builder")
st.title("🔥 Pokémon Team Builder Analítico")

# Verificar si existe la imagen
try:
    st.image("assets/BANNER.jpg", width=700)
except:
    st.info("Banner no encontrado en assets/BANNER.jpg")

st.markdown("Una aplicación que aprovecha una base de datos relacional para analizar las formas alternativas y debilidades de equipos Pokémon.")

# Cargar todos los datos una vez
df_pokemon = run_query("SELECT * FROM pokemon ORDER BY pokedex_number, unique_id")

if df_pokemon.empty:
    st.error("⚠️ No se pudieron cargar los datos de la base. Verifica la conexión.")
    st.stop()

# --- SECCIÓN 1: CONSTRUCTOR Y ANÁLISIS DE EQUIPO ---
st.header("⚔️ Construye y Analiza tu Equipo")

team_pokemon_names = st.multiselect(
    "Elige hasta 6 Pokémon para formar tu equipo:",
    options=df_pokemon['name'].tolist(),
    max_selections=6
)

# --- SECCIÓN 2: ANÁLISIS DE EQUIPO (con Matriz de Vulnerabilidad) ---
if len(team_pokemon_names) > 0:
    team_df = df_pokemon[df_pokemon['name'].isin(team_pokemon_names)]
    st.subheader("Tu Equipo Seleccionado")
    cols_to_show = ['pokedex_number', 'name', 'form_type', 'type1', 'type2', 'total_stats', 'hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed', 'generation', 'legendary']
    st.dataframe(team_df[cols_to_show])

    # --- CONSULTA SQL AVANZADA PARA LA MATRIZ DE VULNERABILIDAD ---
    st.subheader("📊 Análisis de Vulnerabilidad del Equipo")
    
    team_ids = team_df['unique_id'].tolist()
    placeholders = ','.join(['%s'] * len(team_ids))
    
    # CONSULTA CORREGIDA - Mejor lógica para calcular vulnerabilidades
    score_query = f"""
        SELECT
            te.attacking_type,
            SUM(
                CASE
                    WHEN te.effectiveness = 2.0 THEN 1
                    WHEN te.effectiveness = 0.5 THEN -1
                    WHEN te.effectiveness = 0.0 THEN -2
                    ELSE 0
                END
            ) AS team_score,
            COUNT(DISTINCT p.unique_id) AS pokemon_affected
        FROM
            pokemon p
        JOIN
            type_effectiveness te ON (p.type1 = te.defending_type OR p.type2 = te.defending_type)
        WHERE
            p.unique_id IN ({placeholders})
        GROUP BY
            te.attacking_type
        ORDER BY
            team_score DESC;
    """
    
    df_scores = run_query(score_query, team_ids)

    if not df_scores.empty:
        col1, col2 = st.columns([1, 1.5]) 

        with col1:
            st.write("**Matriz de Vulnerabilidad:**")
            st.caption("Score > 0 = Debilidad, Score < 0 = Resistencia")
            
            # Crear tabla estilizada
            df_display = df_scores.copy()
            df_display['Estado'] = df_display['team_score'].apply(
                lambda x: '🔴 Débil' if x > 0 else '🟢 Resistente' if x < 0 else '⚪ Neutral'
            )
            
            st.dataframe(
                df_display[['attacking_type', 'team_score', 'pokemon_affected', 'Estado']]
                .rename(columns={
                    'attacking_type': 'Tipo Atacante',
                    'team_score': 'Score',
                    'pokemon_affected': 'Pokémon Afectados',
                    'Estado': 'Estado'
                }),
                use_container_width=True
            )

        with col2:
            st.write("**Gráfico de Vulnerabilidades:**")
            
            # Crear colores según el score
            colors = ['crimson' if x > 0 else 'mediumseagreen' if x < 0 else 'gray' 
                     for x in df_scores['team_score']]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=df_scores['attacking_type'],
                    y=df_scores['team_score'],
                    marker_color=colors,
                    text=df_scores['team_score'],
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title='Vulnerabilidades del Equipo por Tipo',
                xaxis_title='Tipo de Ataque',
                yaxis_title='Score de Vulnerabilidad',
                xaxis_tickangle=-45,
                showlegend=False
            )
            
            # Agregar línea de referencia en 0
            fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.error("No se pudo calcular el análisis de vulnerabilidad.")

else:
    st.info("Selecciona al menos un Pokémon para analizar tu equipo.")

# --- SECCIÓN 3: DASHBOARD Y ANÁLISIS GENERAL ---
with st.expander("📊 Ver Dashboard y Análisis Avanzado"):
    st.header("📊 Dashboard General")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Entradas", f"{len(df_pokemon)}")
    with col2:
        st.metric("Pokémon Base", f"{df_pokemon['pokedex_number'].nunique()}")
    with col3:
        st.metric("Formas Alternativas", f"{len(df_pokemon[df_pokemon['form_type'] != 'base'])}")
    with col4:
        legendarios = len(df_pokemon[df_pokemon['legendary'] == True])
        st.metric("Pokémon Legendarios", f"{legendarios}")
    
    # --- GRÁFICO 1: INCREMENTO DE PODER POR MEGA EVOLUCIÓN ---
    st.subheader("🚀 Incremento de Poder por Mega Evolución")
    mega_boost_query = """
        SELECT 
            base.base_name, 
            base.total_stats as stats_base,
            mega.total_stats as stats_mega,
            (mega.total_stats - base.total_stats) as incremento,
            ROUND(((mega.total_stats - base.total_stats) / base.total_stats * 100), 2) as porcentaje_incremento
        FROM pokemon base
        JOIN pokemon mega ON base.pokedex_number = mega.pokedex_number
        WHERE base.form_type = 'base' AND mega.form_type = 'mega'
        ORDER BY incremento DESC 
        LIMIT 15;
    """
    df_mega_boost = run_query(mega_boost_query)

    if not df_mega_boost.empty:
        fig_mega = px.bar(
            df_mega_boost, 
            x='base_name', 
            y='incremento',
            title='Top 15 Mayores Incrementos de Stats por Mega Evolución',
            labels={'base_name': 'Pokémon', 'incremento': 'Aumento de Stats Totales'},
            color='incremento',
            color_continuous_scale='Viridis'
        )
        fig_mega.update_layout(xaxis={'tickangle': -45})
        st.plotly_chart(fig_mega, use_container_width=True)
        
        # Mostrar tabla detallada
        st.write("**Detalles del incremento:**")
        st.dataframe(df_mega_boost)

    # --- GRÁFICO 2: POKÉMON CON MÁS FORMAS (USANDO LA VISTA CORRECTAMENTE) ---
    st.subheader("🔄 Pokémon con Más Formas Alternativas")

    # LA CONSULTA AHORA ES SÚPER SIMPLE: solo llamamos a nuestra vista.
    # Añadimos LIMIT 10 para cumplir tu requisito de mostrar los 10 principales.
    forms_view_query = "SELECT * FROM vw_pokemon_with_most_forms LIMIT 10;"

    df_forms = run_query(forms_view_query)

    if not df_forms.empty:
        st.write("Este gráfico se genera consultando la VISTA `vw_pokemon_with_most_forms` en la base de datos.")
        
        fig_forms = px.pie(
            df_forms, 
            names='base_name', 
            values='total_formas',
            title='Top 10 Pokémon con Más Formas en el Dataset'
        )
        fig_forms.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_forms, use_container_width=True)
        
    else:
        st.warning("No se encontraron Pokémon con múltiples formas para el análisis. Asegúrate de haber ejecutado la última versión del script de setup para corregir los datos.")

    # --- GRÁFICO 3: DISTRIBUCIÓN POR GENERACIÓN ---
    st.subheader("📈 Distribución por Generación")
    generation_query = """
        SELECT 
            generation,
            form_type,
            COUNT(*) as cantidad
        FROM pokemon 
        GROUP BY generation, form_type
        ORDER BY generation, form_type;
    """
    df_generations = run_query(generation_query)
    
    if not df_generations.empty:
        fig_gen = px.bar(
            df_generations,
            x='generation',
            y='cantidad',
            color='form_type',
            title='Distribución de Pokémon por Generación y Tipo de Forma',
            labels={'generation': 'Generación', 'cantidad': 'Cantidad de Pokémon'}
        )
        st.plotly_chart(fig_gen, use_container_width=True)

# --- SECCIÓN 4: DEMOSTRACIÓN DE OBJETOS SQL AVANZADOS ---
st.header("⚙️ Demostración de Objetos SQL Avanzados")

# --- PROCEDIMIENTOS ALMACENADOS ---
st.subheader("🔧 Búsqueda con Procedimiento Almacenado")
st.write("Esta función llama directamente al procedimiento `sp_find_pokemon_by_type` en MySQL.")

col_type, col_stats = st.columns(2)
all_types = sorted(pd.concat([df_pokemon['type1'], df_pokemon['type2']]).dropna().unique())
selected_type = col_type.selectbox("Elige un tipo:", all_types)
min_stats = col_stats.slider("Stats Totales Mínimos:", 300, 800, 500, step=50)

if st.button("🔍 Buscar con Procedimiento Almacenado"):
    query = f"CALL sp_find_pokemon_by_type('{selected_type}', {min_stats});"
    df_procedure_result = call_stored_procedure(query)

    if not df_procedure_result.empty:
        st.success(f"Encontrados {len(df_procedure_result)} Pokémon del tipo '{selected_type}' con más de {min_stats} stats totales:")
        st.dataframe(df_procedure_result)
    else:
        st.info("No se encontraron Pokémon con esos criterios.")

# --- VISTAS ---
with st.expander("📋 Análisis usando Vistas de la Base de Datos"):
    
    st.subheader("🚀 Vista: Análisis de Mega Evoluciones")
    st.code("SELECT * FROM vw_mega_evolutions ORDER BY power_increase DESC;")
    
    mega_view_query = "SELECT * FROM vw_mega_evolutions ORDER BY power_increase DESC;"
    df_mega_view = run_query(mega_view_query)

    if not df_mega_view.empty:
        col_chart, col_data = st.columns([1.5, 1])
        
        with col_chart:
            fig_mega_view = px.bar(
                df_mega_view.head(10), 
                x='base_name', 
                y='power_increase',
                title='Top 10: Incremento por Mega Evolución (Vista)',
                labels={'base_name': 'Pokémon', 'power_increase': 'Aumento de Stats'},
                color='power_increase',
                color_continuous_scale='Plasma'
            )
            fig_mega_view.update_layout(xaxis={'tickangle': -45})
            st.plotly_chart(fig_mega_view, use_container_width=True)
        
        with col_data:
            st.write("**Datos de la Vista:**")
            st.dataframe(df_mega_view.head(10))
    else:
        st.warning("No se encontraron datos en la vista vw_mega_evolutions.")

    st.subheader("🔥 Vista: Mejores Atacantes de Tipo Fuego")
    st.code("SELECT * FROM vw_fire_type_fighters ORDER BY attack DESC;")
    
    fire_view_query = "SELECT * FROM vw_fire_type_fighters ORDER BY attack DESC;"
    df_fire_view = run_query(fire_view_query)
    
    if not df_fire_view.empty:
        st.dataframe(df_fire_view, use_container_width=True)
        
        # Gráfico adicional para la vista
        fig_fire = px.scatter(
            df_fire_view,
            x='attack',
            y='total_stats',
            size='sp_attack',
            color='form_type',
            hover_name='name',
            title='Relación Ataque vs Stats Totales - Pokémon Tipo Fuego',
            labels={'attack': 'Ataque', 'total_stats': 'Stats Totales'}
        )
        st.plotly_chart(fig_fire, use_container_width=True)
    else:
        st.warning("No se encontraron datos en la vista vw_fire_type_fighters.")

# --- PIE DE PÁGINA CON INFORMACIÓN TÉCNICA ---
st.markdown("---")
st.markdown("### 🛠️ Información Técnica del Proyecto")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **Base de Datos:**
    - MySQL 8.0+
    - Tablas: 4
    - Vistas: 2
    - Procedimientos: 1
    - Triggers: 1
    """)

with col2:
    st.info("""
    **Tecnologías:**
    - Python 3.8+
    - Streamlit
    - Plotly
    - Pandas
    - MySQL Connector
    """)

with col3:
    st.info("""
    **Características:**
    - Análisis de vulnerabilidades
    - Formas alternativas
    - Consultas complejas
    - Visualizaciones interactivas
    """)