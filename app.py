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

if len(team_pokemon_names) > 0:
    team_df = df_pokemon[df_pokemon['name'].isin(team_pokemon_names)]
    st.subheader("Tu Equipo Seleccionado")
    cols_to_show = ['name','form_type','type1','type2','total_stats','hp','attack','defense', 'sp_attack','sp_defense','speed']
    st.dataframe(team_df[cols_to_show])

    # --- ANÁLISIS DE DEBILIDADES (LA FUNCIÓN PRINCIPAL) ---
    st.subheader("Análisis de Debilidades Defensivas")
    
    placeholders = ','.join(['%s'] * len(team_pokemon_names))
    weakness_query = f"""
        SELECT 
            te.attacking_type AS tipo_atacante,
            COUNT(*) AS numero_de_debiles,
            GROUP_CONCAT(p.name SEPARATOR ', ') as pokemon_debiles
        FROM pokemon p
        JOIN type_effectiveness te ON p.type1 = te.defending_type OR p.type2 = te.defending_type
        WHERE p.name IN ({placeholders}) AND te.effectiveness > 1.0
        GROUP BY te.attacking_type
        ORDER BY numero_de_debiles DESC;
    """
    
    df_weakness = run_query(weakness_query, team_pokemon_names)

    if not df_weakness.empty:
        st.write("Esta tabla muestra qué tipos de ataque son más peligrosos para tu equipo.")
        fig = px.bar(df_weakness, 
                     x='tipo_atacante', y='numero_de_debiles',
                     hover_data=['pokemon_debiles'],
                     title='Debilidades del Equipo',
                     labels={'tipo_atacante': 'Tipo de Ataque del Oponente', 'numero_de_debiles': 'Nº de Pokémon Débiles'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("¡Tu equipo parece no tener debilidades comunes según las reglas básicas!")
else:
    st.info("Selecciona al menos un Pokémon para analizar sus debilidades.")

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