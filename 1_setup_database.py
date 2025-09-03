# Archivo: 1_setup_database.py (Versión FINAL con commits explícitos)

import pandas as pd
import mysql.connector
from mysql.connector import Error

# --- CONFIGURACIÓN ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '2076O8233e*' # ¡CAMBIA ESTO!
}
DB_NAME = 'pokemon_team_builder'

def setup_database_and_import_data():
    """
    Función completa que crea y puebla la base de datos,
    asegurando que cada paso se guarde correctamente.
    """
    conn = None
    cursor = None
    try:
        # --- 1. Crear Base de Datos y Tablas ---
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4")
        cursor.execute(f"USE {DB_NAME}")
        print(f"✅ Base de datos '{DB_NAME}' lista.")

        print("🧹 Limpiando tablas anteriores...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("DROP TABLE IF EXISTS pokemon, type_effectiveness, teams, team_members;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # (El código para crear todas las tablas va aquí, como en la versión anterior)
        # Por brevedad, se omite aquí, pero asegúrate de tener tus 4 sentencias CREATE TABLE
        print("🏗️ Creando tabla 'pokemon'...")
        cursor.execute("""CREATE TABLE pokemon (unique_id INT PRIMARY KEY AUTO_INCREMENT, pokedex_number INT, name VARCHAR(100), base_name VARCHAR(50), form_type ENUM('base','mega','primal','regional','special'), type1 VARCHAR(20), type2 VARCHAR(20), total_stats INT, hp INT, attack INT, defense INT, sp_attack INT, sp_defense INT, speed INT, generation INT, legendary BOOLEAN, INDEX (pokedex_number), INDEX (base_name));""")
        print("🏗️ Creando tabla 'teams'...")
        cursor.execute("""CREATE TABLE teams (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL DEFAULT 'Mi Equipo', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP);""")
        print("🏗️ Creando tabla 'team_members'...")
        cursor.execute("""CREATE TABLE team_members (id INT PRIMARY KEY AUTO_INCREMENT, team_id INT NOT NULL, pokemon_unique_id INT NOT NULL, position INT NOT NULL, FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE, FOREIGN KEY (pokemon_unique_id) REFERENCES pokemon(unique_id), UNIQUE KEY (team_id, position));""")
        print("🏗️ Creando tabla 'type_effectiveness'...")
        cursor.execute("""CREATE TABLE type_effectiveness (attacking_type VARCHAR(20), defending_type VARCHAR(20), effectiveness DECIMAL(2,1), PRIMARY KEY (attacking_type, defending_type));""")
        
        conn.commit() # <<--- GUARDADO #1: Después de crear todas las tablas.
        print("✅ Esquema completo creado y guardado.")

        # --- 2. Procesar Datos del CSV ---
        df = pd.read_csv('Pokemon.csv')
        all_base_names = df[~df['Name'].str.contains('Mega|Primal|Alolan|Galarian|Forme|Size')]['Name'].unique()
        def get_clean_info(name, base_names_list):
            name_lower = name.lower()
            base_name = next((bn for bn in base_names_list if name.startswith(bn)), name)
            form_type = 'base'
            if "mega" in name_lower: form_type = "mega"
            elif "primal" in name_lower: form_type = "primal"
            elif "alolan" in name_lower or "galarian" in name_lower: form_type = "regional"
            elif name != base_name: form_type = "special"
            return pd.Series([base_name, form_type])
        df[['base_name', 'form_type']] = df['Name'].apply(lambda x: get_clean_info(x, all_base_names))
        df_clean = df.where(pd.notna(df), None)
        print(f"📊 {len(df_clean)} filas de Pokémon procesadas.")

        # --- 3. Insertar y Guardar Datos de Pokémon ---
        print("➡️ Insertando datos de Pokémon...")
        poke_cols = ['#','Name','base_name','form_type','Type 1','Type 2','Total','HP','Attack','Defense','Sp. Atk','Sp. Def','Speed','Generation','Legendary']
        poke_data_to_insert = [tuple(row) for row in df_clean[poke_cols].itertuples(index=False)]
        poke_insert_query = """INSERT INTO pokemon (pokedex_number, name, base_name, form_type, type1, type2, total_stats, hp, attack, defense, sp_attack, sp_defense, speed, generation, legendary) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        cursor.executemany(poke_insert_query, poke_data_to_insert)
        conn.commit() # <<--- GUARDADO #2: Inmediatamente después de insertar los Pokémon.
        print(f"✅ ¡{cursor.rowcount} Pokémon guardados en la base de datos!")
        
        # --- 4. Insertar y Guardar Datos de Efectividad de Tipos ---
        print("➡️ Insertando datos de efectividad...")
        type_data = [('Fire', 'Grass', 2.0), ('Fire', 'Water', 0.5), ('Water', 'Fire', 2.0), ('Grass', 'Water', 2.0), ('Electric', 'Water', 2.0), ('Ice', 'Dragon', 2.0), ('Ground', 'Electric', 2.0), ('Fighting', 'Normal', 2.0), ('Poison', 'Grass', 2.0), ('Flying', 'Fighting', 2.0), ('Psychic', 'Fighting', 2.0), ('Bug', 'Grass', 2.0), ('Rock', 'Fire', 2.0), ('Ghost', 'Psychic', 2.0), ('Dragon', 'Dragon', 2.0), ('Steel', 'Fairy', 2.0), ('Fairy', 'Dragon', 2.0), ('Dark', 'Psychic', 2.0)]
        type_insert_query = "INSERT INTO type_effectiveness (attacking_type, defending_type, effectiveness) VALUES (%s, %s, %s)"
        cursor.executemany(type_insert_query, type_data)
        conn.commit() # <<--- GUARDADO #3: Inmediatamente después de insertar las efectividades.
        print(f"✅ ¡{cursor.rowcount} reglas de efectividad guardadas en la base de datos!")

    except FileNotFoundError:
        print("❌ ERROR CRÍTICO: No se encontró el archivo 'data/Pokemon.csv'.")
    except Error as e:
        print(f"❌ Error durante el setup de la base de datos: {e}")
    finally:
        print("🔚 Proceso de setup finalizado.")
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_database_and_import_data()