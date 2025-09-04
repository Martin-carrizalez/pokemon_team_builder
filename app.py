# Archivo: app.py (Versión 100% COMPLETA Y FUNCIONAL)

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

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

# --- INICIO DE LA APP ---
st.set_page_config(layout="wide", page_title="Pokémon Team Builder")
st.title("🔥 Pokémon Team Builder Analítico")
st.markdown("# <span style='color:gold;'>ϞϞ(๑⚈ . ̫ ⚈๑)∩</span> vs <span style='color:red;'>(</span>⦿<span style='color:red;'>)</span>", unsafe_allow_html=True)
st.markdown("Una aplicación que aprovecha una base de datos relacional para analizar las formas alternativas y debilidades de equipos Pokémon.")

# Cargar todos los datos una vez
df_pokemon = run_query("SELECT * FROM pokemon ORDER BY pokedex_number, unique_id")

# --- SECCIÓN 1: CONSTRUCTOR Y ANÁLISIS DE EQUIPO ---
st.header("⚔️ Construye y Analiza tu Equipo")

team_pokemon_names = st.multiselect(
    "Elige hasta 6 Pokémon para formar tu equipo:",
    options=df_pokemon['name'].tolist(),
    max_selections=6
)

# --- SECCIÓN 2: ANÁLISIS DE EQUIPO (con Gráfico Vertical Mejorado) ---
if len(team_pokemon_names) > 0:
    team_df = df_pokemon[df_pokemon['name'].isin(team_pokemon_names)]
    st.subheader("Tu Equipo Seleccionado")
    cols_to_show = ['pokedex_number', 'name', 'form_type', 'type1', 'type2', 'total_stats', 'hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed', 'generation', 'legendary']
    st.dataframe(team_df[cols_to_show])

    # --- CONSULTA SQL AVANZADA PARA LA MATRIZ DE VULNERABILIDAD ---
    st.subheader("📊 Análisis de Vulnerabilidad del Equipo")
    
    team_ids = team_df['unique_id'].tolist()
    placeholders = ','.join(['%s'] * len(team_ids))
    
    score_query = f"""
        SELECT
            all_types.attacking_type,
            SUM(
                COALESCE(
                    CASE
                        WHEN eff.effectiveness = 2.0 THEN 1
                        WHEN eff.effectiveness = 0.5 THEN -1
                        WHEN eff.effectiveness = 0.0 THEN -2
                        ELSE 0
                    END, 0)
            ) AS team_score
        FROM
            (SELECT DISTINCT attacking_type FROM type_effectiveness) AS all_types
        CROSS JOIN
            (SELECT * FROM pokemon WHERE unique_id IN ({placeholders})) AS team_pokemon
        LEFT JOIN
            type_effectiveness eff ON (team_pokemon.type1 = eff.defending_type OR team_pokemon.type2 = eff.defending_type) 
            AND all_types.attacking_type = eff.attacking_type
        GROUP BY
            all_types.attacking_type
        ORDER BY
            team_score DESC;
    """
    
    df_scores = run_query(score_query, team_ids)

    if not df_scores.empty:
        # --- AQUÍ EMPIEZA LA MAGIA DEL DISEÑO DE COLUMNAS CON EL NUEVO GRÁFICO ---
        col1, col2 = st.columns([1, 1.5]) 

        with col1:
            st.write("**Matriz de Score:**")
            st.caption("Rojo = Debilidad, Verde = Resistencia.")
            
            def style_scores(val):
                color = ''
                if val > 0: color = f'background-color: rgba(255, 77, 77, {min(0.25 * val, 1.0)})'
                elif val < 0: color = f'background-color: rgba(85, 184, 85, {min(0.25 * abs(val), 1.0)})'
                return color

            st.markdown(df_scores.style.applymap(style_scores, subset=['team_score']).to_html(), unsafe_allow_html=True)

        with col2:
            st.write("**Gráfico Resumen:**")
            
            # Añadimos una columna de categoría para el color
            df_scores['categoria'] = df_scores['team_score'].apply(lambda x: 'Debilidad' if x > 0 else 'Resistencia')
            
            fig = px.bar(
                df_scores,
                x='attacking_type', # Tipos en el eje X
                y='team_score',     # Score en el eje Y
                color='categoria',  # Coloreamos por categoría
                color_discrete_map={
                    'Debilidad': 'crimson',
                    'Resistencia': 'mediumseagreen'
                },
                title='Resumen de Debilidades y Resistencias del Equipo',
                labels={'team_score': 'Score de Vulnerabilidad', 'attacking_type': 'Tipo de Ataque Oponente'}
            )
            fig.update_layout(
                xaxis_tickangle=-45, # Inclinamos las etiquetas para que no se solapen
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.error("No se pudo calcular el análisis de vulnerabilidad.")

else:
    st.info("Selecciona al menos un Pokémon para analizar tu equipo.")

# --- SECCIÓN 2: DASHBOARD Y ANÁLISIS GENERAL ---
with st.expander("Ver Dashboard y Análisis Avanzado de la Base de Datos"):
    st.header("📊 Dashboard General")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Entradas", f"{len(df_pokemon)}")
    col2.metric("Pokémon Base", f"{df_pokemon['pokedex_number'].nunique()}")
    col3.metric("Formas Alternativas", f"{len(df_pokemon[df_pokemon['form_type'] != 'base'])}")
    
    st.header("📈 Análisis Avanzado (Posible gracias al esquema de BD)")

    # --- GRÁFICO 1: INCREMENTO DE PODER POR MEGA EVOLUCIÓN (COMPLETO) ---
    st.subheader("🚀 Incremento de Poder por Mega Evolución")
    mega_boost_query = """
        SELECT base.base_name, (mega.total_stats - base.total_stats) as incremento
        FROM pokemon base
        JOIN pokemon mega ON base.pokedex_number = mega.pokedex_number
        WHERE base.form_type = 'base' AND mega.form_type = 'mega'
        ORDER BY incremento DESC LIMIT 15;
    """
    df_mega_boost = run_query(mega_boost_query)

    if not df_mega_boost.empty:
        fig_mega = px.bar(df_mega_boost, x='base_name', y='incremento',
                      title='Top 15 Mayores Incrementos de Stats por Mega Evolución',
                      labels={'base_name': 'Pokémon', 'incremento': 'Aumento de Stats Totales'})
        st.plotly_chart(fig_mega, use_container_width=True)

    # --- GRÁFICO 2: POKÉMON CON MÁS FORMAS (COMPLETO) ---
    st.subheader("🔄 Pokémon con Más Formas Alternativas")
    forms_query = """
        SELECT base_name, COUNT(*) as total_formas
        FROM pokemon 
        GROUP BY base_name 
        HAVING total_formas > 2
        ORDER BY total_formas DESC;
    """
    df_forms = run_query(forms_query)

    if not df_forms.empty:
        fig_forms = px.pie(df_forms, names='base_name', values='total_formas',
                       title='Pokémon con 3 o más Formas en el Dataset')
        st.plotly_chart(fig_forms, use_container_width=True)

# --- SECCIÓN 4: DEMOSTRACIÓN DE OBJETOS SQL AVANZADOS ---
st.header("⚙️ Demostración de Lógica en la Base de Datos")

st.subheader("Búsqueda con Procedimiento Almacenado")
st.write("Esta función llama directamente al procedimiento `sp_find_pokemon_by_type` en MySQL.")

col_type, col_stats = st.columns(2)
# Obtenemos la lista de tipos únicos de la base de datos
all_types = sorted(pd.concat([df_pokemon['type1'], df_pokemon['type2']]).dropna().unique())
selected_type = col_type.selectbox("Elige un tipo:", all_types)
min_stats = col_stats.slider("Stats Totales Mínimos:", 300, 800, 500, step=50)

if st.button("Buscar Pokémon con Procedimiento"):
    # En lugar de escribir un SELECT en Python, llamamos al procedimiento
    query = f"CALL sp_find_pokemon_by_type('{selected_type}', {min_stats});"
    
    
    # Usamos una función de ayuda para manejar la llamada
    def call_stored_procedure(query):
        conn = mysql.connector.connect(**DB_CONFIG)  # Nueva conexión cada vez
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()  # Cierra la conexión después de usarla
        return pd.DataFrame(result)

    df_procedure_result = call_stored_procedure(query)

    if not df_procedure_result.empty:
        st.write(f"Resultados para el tipo '{selected_type}' con más de {min_stats} stats totales:")
        st.dataframe(df_procedure_result)
    else:
        st.info("No se encontraron Pokémon con esos criterios.")
        
# --- SECCIÓN 3: DEMOSTRACIÓN DE OBJETOS SQL AVANZADOS (VISTAS) ---

with st.expander("Ver Análisis Avanzado usando Vistas de la Base de Datos"):

    st.subheader("🚀 Análisis de Mega Evoluciones (usando la Vista `vw_mega_evolutions`)")
    st.write("Esta visualización se genera con la simple consulta: `SELECT * FROM vw_mega_evolutions`")

    # La consulta en Python es ahora súper simple gracias a la vista.
    # La lógica compleja (el JOIN) vive y se ejecuta en MySQL.
    mega_view_query = "SELECT * FROM vw_mega_evolutions ORDER BY power_increase DESC;"
    df_mega_view = run_query(mega_view_query)

    if not df_mega_view.empty:
        # Usamos .head(15) para mostrar solo los 15 más relevantes en el gráfico
        fig_mega = px.bar(df_mega_view.head(15), 
                      x='base_name', 
                      y='power_increase',
                      title='Top 15 Mayores Incrementos de Stats por Mega Evolución',
                      labels={'base_name': 'Pokémon', 'power_increase': 'Aumento de Stats'})
        st.plotly_chart(fig_mega, use_container_width=True)
        st.write("Tabla completa de la vista:")
        st.dataframe(df_mega_view)
    else:
        st.warning("No se encontraron datos en la vista de Mega Evoluciones.")

    st.subheader("🔥 Mejores Atacantes de Tipo Fuego (usando la Vista `vw_fire_type_fighters`)")
    st.write("Esta tabla se genera con la simple consulta: `SELECT * FROM vw_fire_type_fighters`")

    # De nuevo, la consulta en Python es muy limpia.
    # La lógica de filtrado vive y se ejecuta en MySQL.
    fire_view_query = "SELECT * FROM vw_fire_type_fighters;"
    df_fire_view = run_query(fire_view_query)
    
    if not df_fire_view.empty:
        st.dataframe(df_fire_view)
    else:
        st.warning("No se encontraron datos en la vista de luchadores de tipo Fuego.")