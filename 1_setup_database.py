# Archivo: 1_setup_database.py (Versión FINAL Y CORREGIDA)
import pandas as pd
import mysql.connector
from mysql.connector import Error

# --- CONFIGURACIÓN ---
DB_CONFIG = { 'host': 'localhost', 'user': 'root', 'password': '2076O8233e*' }
DB_NAME = 'pokemon_team_builder'

def create_and_populate_db():
    try:
        # --- 1. Crear Base de Datos y Tablas ---
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4")
        cursor.execute(f"USE {DB_NAME}")
        print(f"✅ Base de datos '{DB_NAME}' lista.")

        print("🧹 Limpiando tablas anteriores...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("DROP TABLE IF EXISTS pokemon, type_effectiveness;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        print("🏗️ Creando tabla 'pokemon'...")
        cursor.execute("""
        CREATE TABLE pokemon (
            unique_id INT PRIMARY KEY AUTO_INCREMENT, pokedex_number INT, name VARCHAR(100),
            base_name VARCHAR(50), form_type ENUM('base','mega','primal','regional','special'),
            type1 VARCHAR(20), type2 VARCHAR(20), total_stats INT, hp INT, attack INT,
            defense INT, sp_attack INT, sp_defense INT, speed INT, generation INT, legendary BOOLEAN,
            INDEX (pokedex_number), INDEX (base_name), INDEX(form_type)
        );""")
        
        print("🏗️ Creando tabla 'type_effectiveness'...")
        cursor.execute("""
        CREATE TABLE type_effectiveness (
            attacking_type VARCHAR(20), defending_type VARCHAR(20), effectiveness DECIMAL(2,1),
            PRIMARY KEY (attacking_type, defending_type)
        );""")
        
        # --- 2. Procesar Datos del CSV ---
        df = pd.read_csv('Pokemon.csv')
        
        def get_clean_info(name, all_base_names):
            name_lower = name.lower()
            base_name = next((bn for bn in all_base_names if name.startswith(bn)), name)
            
            form_type = 'base'
            if "mega" in name_lower: form_type = "mega"
            elif "primal" in name_lower: form_type = "primal"
            elif "alolan" in name_lower or "galarian" in name_lower or "hisui" in name_lower: form_type = "regional"
            elif name != base_name: form_type = "special"
            return pd.Series([base_name, form_type])

        base_names_list = df[~df['Name'].str.contains('Mega|Primal|Alolan|Galarian|Forme|Size')]['Name'].unique()
        df[['base_name', 'form_type']] = df['Name'].apply(lambda x: get_clean_info(x, base_names_list))
        df_clean = df.where(pd.notna(df), None)
        print(f"📊 {len(df_clean)} filas procesadas y clasificadas.")

        # --- 3. Insertar Datos de Pokémon ---
        print("Inserting Pokémon data...")
        poke_cols = ['#','Name','base_name','form_type','Type 1','Type 2','Total','HP','Attack','Defense','Sp. Atk','Sp. Def','Speed','Generation','Legendary']
        poke_data_to_insert = [tuple(row) for row in df_clean[poke_cols].itertuples(index=False)]
        poke_insert_query = """INSERT INTO pokemon (pokedex_number, name, base_name, form_type, type1, type2, total_stats, hp, attack, defense, sp_attack, sp_defense, speed, generation, legendary) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        cursor.executemany(poke_insert_query, poke_data_to_insert)
        print(f"✅ ¡{cursor.rowcount} Pokémon importados!")
        
        # --- 4. Insertar Datos de Efectividad de Tipos ---
        print("Inserting type effectiveness data...")
        # (Aquí iría la lista completa de efectividades, por simplicidad ponemos algunas clave)
        type_data = [('Fire', 'Grass', 2.0), ('Fire', 'Water', 0.5), ('Water', 'Fire', 2.0), ('Grass', 'Water', 2.0), ('Electric', 'Water', 2.0), ('Ice', 'Dragon', 2.0), ('Ground', 'Electric', 2.0), ('Fighting', 'Normal', 2.0), ('Poison', 'Grass', 2.0), ('Flying', 'Fighting', 2.0), ('Psychic', 'Fighting', 2.0), ('Bug', 'Grass', 2.0), ('Rock', 'Fire', 2.0), ('Ghost', 'Psychic', 2.0), ('Dragon', 'Dragon', 2.0), ('Steel', 'Fairy', 2.0), ('Fairy', 'Dragon', 2.0), ('Dark', 'Psychic', 2.0)]
        type_insert_query = "INSERT INTO type_effectiveness (attacking_type, defending_type, effectiveness) VALUES (%s, %s, %s)"
        cursor.executemany(type_insert_query, type_data)
        print(f"✅ ¡{cursor.rowcount} reglas de efectividad importadas!")

        conn.commit()

    except FileNotFoundError: print("❌ ERROR: No se encontró 'data/Pokemon.csv'.")
    except Error as e: print(f"❌ Error durante el setup: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_and_populate_db()