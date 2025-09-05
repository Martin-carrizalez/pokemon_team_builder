# =====================================================
# SCRIPT DE IMPORTACIÓN MEJORADO - POKÉMON TEAM BUILDER
# VERSIÓN: 2.0 - COMPLETAMENTE FUNCIONAL
# =====================================================

import pandas as pd
import mysql.connector
from mysql.connector import Error
import numpy as np
import sys
import os

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '2076O8233e*',  # CAMBIAR POR TU PASSWORD
    'database': 'pokemon_team_builder'
}

def verificar_archivos():
    """Verificar que los archivos CSV existan"""
    archivos_requeridos = ['Pokemon.csv', 'Tabla de tipos.csv']
    archivos_faltantes = []
    
    for archivo in archivos_requeridos:
        if not os.path.exists(archivo):
            archivos_faltantes.append(archivo)
    
    if archivos_faltantes:
        print(f"❌ Archivos faltantes: {', '.join(archivos_faltantes)}")
        print("📁 Asegúrate de que los archivos estén en el directorio actual:")
        print("   - Pokemon.csv")
        print("   - Tabla de tipos.csv")
        return False
    
    print("✅ Todos los archivos CSV encontrados!")
    return True

def conectar_bd():
    """Establecer conexión con la base de datos"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ Conexión exitosa a MySQL")
        return connection
    except Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None

def ejecutar_sql_completo(connection):
    """Ejecutar todo el código SQL de estructura"""
    try:
        cursor = connection.cursor()
        
        print("🔧 Creando estructura de base de datos...")
        
        # Leer el archivo SQL si existe, o usar código embebido
        sql_commands = """
        -- Eliminar base de datos existente y crear nueva
        DROP DATABASE IF EXISTS pokemon_team_builder;
        CREATE DATABASE pokemon_team_builder;
        USE pokemon_team_builder;
        
        -- Crear todas las tablas
        CREATE TABLE pokemon (
            unique_id INT PRIMARY KEY AUTO_INCREMENT,
            pokedex_number INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            base_name VARCHAR(50) NOT NULL,
            form_type ENUM('base', 'mega', 'primal', 'regional', 'special') DEFAULT 'base',
            type1 VARCHAR(20) NOT NULL,
            type2 VARCHAR(20) NULL,
            total_stats INT NOT NULL,
            hp INT NOT NULL,
            attack INT NOT NULL,
            defense INT NOT NULL,
            sp_attack INT NOT NULL,
            sp_defense INT NOT NULL,
            speed INT NOT NULL,
            generation INT NOT NULL,
            legendary BOOLEAN NOT NULL DEFAULT FALSE,
            is_alternate BOOLEAN DEFAULT FALSE,
            origin_region VARCHAR(20) DEFAULT 'Kanto',
            
            INDEX idx_pokedex (pokedex_number),
            INDEX idx_base_name (base_name),
            INDEX idx_form_type (form_type),
            INDEX idx_type1 (type1),
            INDEX idx_generation (generation),
            INDEX idx_legendary (legendary)
        );
        
        CREATE TABLE type_effectiveness (
            id INT PRIMARY KEY AUTO_INCREMENT,
            attacking_type VARCHAR(20) NOT NULL,
            defending_type VARCHAR(20) NOT NULL,
            effectiveness DECIMAL(3,2) NOT NULL,
            
            INDEX idx_attacking (attacking_type),
            INDEX idx_defending (defending_type),
            UNIQUE KEY unique_type_combination (attacking_type, defending_type)
        );
        
        CREATE TABLE teams (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            allow_megas BOOLEAN DEFAULT TRUE,
            allow_legendaries BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_created (created_at),
            INDEX idx_name (name),
            CONSTRAINT chk_team_name_length CHECK (CHAR_LENGTH(name) >= 3)
        );
        
        CREATE TABLE team_members (
            id INT PRIMARY KEY AUTO_INCREMENT,
            team_id INT NOT NULL,
            pokemon_unique_id INT NOT NULL,
            position INT NOT NULL CHECK (position BETWEEN 1 AND 6),
            nickname VARCHAR(50),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
            FOREIGN KEY (pokemon_unique_id) REFERENCES pokemon(unique_id),
            UNIQUE KEY unique_team_position (team_id, position),
            
            INDEX idx_team (team_id),
            INDEX idx_pokemon (pokemon_unique_id)
        );
        
        CREATE TABLE activity_log (
            id INT PRIMARY KEY AUTO_INCREMENT,
            table_name VARCHAR(50) NOT NULL,
            action_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
            record_id INT NOT NULL,
            old_values JSON,
            new_values JSON,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX idx_table_action (table_name, action_type),
            INDEX idx_timestamp (timestamp)
        );
        """
        
        # Ejecutar comandos SQL uno por uno
        for command in sql_commands.split(';'):
            if command.strip():
                cursor.execute(command)
        
        connection.commit()
        print("✅ Estructura de base de datos creada exitosamente!")
        
    except Error as e:
        print(f"❌ Error creando estructura: {e}")
        return False
    
    return True

def crear_vistas_y_procedimientos(connection):
    """Crear vistas, triggers y procedimientos"""
    try:
        cursor = connection.cursor()
        
        print("🔧 Creando vistas, triggers y procedimientos...")
        
        # Vista 1: Mega Evoluciones
        cursor.execute("""
        CREATE VIEW vw_mega_evolutions AS
        SELECT 
            base.base_name,
            base.name as base_form,
            base.total_stats as base_stats,
            mega.name as mega_form,
            mega.total_stats as mega_stats,
            (mega.total_stats - base.total_stats) as power_increase,
            ROUND(((mega.total_stats - base.total_stats) / base.total_stats * 100), 2) as percentage_increase,
            base.type1 as base_type1,
            base.type2 as base_type2,
            mega.type1 as mega_type1,
            mega.type2 as mega_type2
        FROM pokemon base
        JOIN pokemon mega ON base.pokedex_number = mega.pokedex_number
        WHERE base.form_type = 'base' AND mega.form_type = 'mega'
        ORDER BY power_increase DESC;
        """)
        
        # Vista 2: Pokémon tipo fuego
        cursor.execute("""
        CREATE VIEW vw_fire_type_fighters AS
        SELECT 
            unique_id,
            name,
            form_type,
            type1,
            type2,
            attack,
            sp_attack,
            total_stats,
            generation,
            legendary,
            CASE 
                WHEN attack > sp_attack THEN 'Physical'
                WHEN sp_attack > attack THEN 'Special'
                ELSE 'Balanced'
            END as attack_style
        FROM pokemon 
        WHERE type1 = 'Fire' OR type2 = 'Fire'
        HAVING attack >= 80 OR sp_attack >= 80
        ORDER BY GREATEST(attack, sp_attack) DESC;
        """)
        
        # Función para calcular power level
        cursor.execute("DROP FUNCTION IF EXISTS fn_calculate_power_level;")
        cursor.execute("""
        CREATE FUNCTION fn_calculate_power_level(
            p_total_stats INT,
            p_legendary BOOLEAN,
            p_form_type VARCHAR(10)
        ) RETURNS DECIMAL(5,2)
        READS SQL DATA
        DETERMINISTIC
        BEGIN
            DECLARE power_level DECIMAL(5,2) DEFAULT 0.0;
            DECLARE base_multiplier DECIMAL(3,2) DEFAULT 1.0;
            
            SET power_level = p_total_stats / 10.0;
            
            IF p_legendary THEN
                SET base_multiplier = base_multiplier + 0.5;
            END IF;
            
            CASE p_form_type
                WHEN 'mega' THEN SET base_multiplier = base_multiplier + 0.8;
                WHEN 'primal' THEN SET base_multiplier = base_multiplier + 0.9;
                WHEN 'regional' THEN SET base_multiplier = base_multiplier + 0.2;
                WHEN 'special' THEN SET base_multiplier = base_multiplier + 0.3;
                ELSE SET base_multiplier = base_multiplier;
            END CASE;
            
            RETURN power_level * base_multiplier;
        END;
        """)
        
        # Vista 3: Ranking de power level
        cursor.execute("""
        CREATE VIEW vw_pokemon_power_ranking AS
        SELECT 
            unique_id,
            name,
            base_name,
            form_type,
            type1,
            type2,
            total_stats,
            legendary,
            generation,
            fn_calculate_power_level(total_stats, legendary, form_type) as power_level,
            RANK() OVER (ORDER BY fn_calculate_power_level(total_stats, legendary, form_type) DESC) as power_rank
        FROM pokemon
        ORDER BY power_level DESC;
        """)
        
        # Trigger
        cursor.execute("DROP TRIGGER IF EXISTS tr_team_activity_log;")
        cursor.execute("""
        CREATE TRIGGER tr_team_activity_log
            AFTER INSERT ON team_members
            FOR EACH ROW
        BEGIN
            DECLARE team_name VARCHAR(100);
            DECLARE pokemon_name VARCHAR(100);
            
            SELECT t.name INTO team_name FROM teams t WHERE t.id = NEW.team_id;
            SELECT p.name INTO pokemon_name FROM pokemon p WHERE p.unique_id = NEW.pokemon_unique_id;
            
            INSERT INTO activity_log (table_name, action_type, record_id, new_values)
            VALUES (
                'team_members',
                'INSERT',
                NEW.id,
                JSON_OBJECT(
                    'team_id', NEW.team_id,
                    'team_name', team_name,
                    'pokemon_unique_id', NEW.pokemon_unique_id,
                    'pokemon_name', pokemon_name,
                    'position', NEW.position,
                    'nickname', NEW.nickname
                )
            );
        END;
        """)
        
        # Procedimiento almacenado 1
        cursor.execute("DROP PROCEDURE IF EXISTS sp_find_pokemon_by_type;")
        cursor.execute("""
        CREATE PROCEDURE sp_find_pokemon_by_type(
            IN p_type VARCHAR(20),
            IN p_min_stats INT
        )
        BEGIN
            SELECT 
                unique_id,
                name,
                form_type,
                type1,
                type2,
                total_stats,
                attack,
                sp_attack,
                legendary,
                generation
            FROM pokemon 
            WHERE (type1 = p_type OR type2 = p_type) 
            AND total_stats >= p_min_stats
            ORDER BY total_stats DESC, name;
        END;
        """)
        
        # Procedimiento almacenado 2
        cursor.execute("DROP PROCEDURE IF EXISTS sp_team_analysis;")
        cursor.execute("""
        CREATE PROCEDURE sp_team_analysis(
            IN p_team_id INT
        )
        BEGIN
            DECLARE team_exists INT DEFAULT 0;
            
            SELECT COUNT(*) INTO team_exists FROM teams WHERE id = p_team_id;
            
            IF team_exists = 0 THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Equipo no encontrado';
            END IF;
            
            SELECT 
                t.name as team_name,
                t.description,
                COUNT(tm.id) as pokemon_count,
                t.created_at
            FROM teams t
            LEFT JOIN team_members tm ON t.id = tm.team_id
            WHERE t.id = p_team_id
            GROUP BY t.id, t.name, t.description, t.created_at;
            
            SELECT 
                tm.position,
                p.name,
                p.form_type,
                p.type1,
                p.type2,
                p.total_stats,
                p.legendary,
                tm.nickname
            FROM team_members tm
            JOIN pokemon p ON tm.pokemon_unique_id = p.unique_id
            WHERE tm.team_id = p_team_id
            ORDER BY tm.position;
        END;
        """)
        
        connection.commit()
        print("✅ Vistas, triggers y procedimientos creados exitosamente!")
        
    except Error as e:
        print(f"❌ Error creando objetos SQL: {e}")
        return False
    
    return True

def procesar_pokemon_data():
    """Procesar y categorizar los datos de Pokémon"""
    try:
        print("📂 Cargando datos de Pokémon...")
        df = pd.read_csv('Pokemon.csv')
        
        print(f"📊 Dataset original: {len(df)} filas")
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Renombrar columnas si es necesario
        column_mapping = {
            '#': 'pokedex_number',
            'Name': 'name',
            'Type 1': 'type1',
            'Type 2': 'type2',
            'Total': 'total_stats',
            'HP': 'hp',
            'Attack': 'attack',
            'Defense': 'defense',
            'Sp. Atk': 'sp_attack',
            'Sp. Def': 'sp_defense',
            'Speed': 'speed',
            'Generation': 'generation',
            'Legendary': 'legendary'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Procesar formas alternativas
        df['form_type'] = 'base'
        df['is_mega'] = df['name'].str.contains('Mega', na=False, case=False)
        df['is_primal'] = df['name'].str.contains('Primal', na=False, case=False)
        df['is_regional'] = df['name'].str.contains('Alolan|Galarian', na=False, case=False)
        df['is_alternate'] = df['name'].str.contains('|'.join([
            'Mega', 'Primal', 'Alolan', 'Galarian', 'Super Size', 
            'Confined', 'Unbound', 'Attack Forme', 'Defense Forme'
        ]), na=False, case=False)
        
        # Asignar tipos de forma
        df.loc[df['is_mega'], 'form_type'] = 'mega'
        df.loc[df['is_primal'], 'form_type'] = 'primal'
        df.loc[df['is_regional'], 'form_type'] = 'regional'
        df.loc[df['is_alternate'] & (df['form_type'] == 'base'), 'form_type'] = 'special'
        
        # Crear nombre base limpio
        df['base_name'] = df['name'].str.replace(
            r'Mega |Primal |Alolan |Galarian |Super Size|Confined|Unbound|Attack Forme|Defense Forme', 
            '', regex=True
        ).str.strip()
        
        # Asignar región por generación
        df['origin_region'] = df['generation'].map({
            1: 'Kanto', 2: 'Johto', 3: 'Hoenn', 4: 'Sinnoh',
            5: 'Unova', 6: 'Kalos', 7: 'Alola', 8: 'Galar'
        }).fillna('Unknown')
        
        # Estadísticas
        form_stats = df['form_type'].value_counts()
        print("\n📈 Distribución de formas:")
        for form, count in form_stats.items():
            print(f"   {form.title()}: {count}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error procesando datos Pokémon: {e}")
        return None

def importar_pokemon_data(connection, df):
    """Importar datos de Pokémon a la base de datos"""
    try:
        cursor = connection.cursor()
        
        print("📥 Importando datos de Pokémon...")
        
        insert_query = """
        INSERT INTO pokemon (pokedex_number, name, base_name, form_type, type1, type2,
                           total_stats, hp, attack, defense, sp_attack, sp_defense, speed,
                           generation, legendary, is_alternate, origin_region)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        successful_inserts = 0
        for _, row in df.iterrows():
            try:
                values = (
                    int(row['pokedex_number']),
                    str(row['name'])[:100],  # Truncar si es muy largo
                    str(row['base_name'])[:50],
                    row['form_type'],
                    str(row['type1']),
                    str(row['type2']) if pd.notna(row['type2']) else None,
                    int(row['total_stats']),
                    int(row['hp']),
                    int(row['attack']),
                    int(row['defense']),
                    int(row['sp_attack']),
                    int(row['sp_defense']),
                    int(row['speed']),
                    int(row['generation']),
                    bool(row['legendary']),
                    bool(row['is_alternate']),
                    str(row['origin_region'])
                )
                cursor.execute(insert_query, values)
                successful_inserts += 1
                
                if successful_inserts % 100 == 0:
                    print(f"   Procesados: {successful_inserts}")
                    
            except Exception as e:
                print(f"⚠️ Error insertando {row['name']}: {e}")
        
        connection.commit()
        print(f"✅ {successful_inserts} Pokémon importados exitosamente!")
        
        # Verificar resultados
        cursor.execute("SELECT form_type, COUNT(*) as count FROM pokemon GROUP BY form_type")
        results = cursor.fetchall()
        print("\n📊 Resumen final:")
        for form_type, count in results:
            print(f"   {form_type.title()}: {count} Pokémon")
        
        return successful_inserts > 0
        
    except Error as e:
        print(f"❌ Error en importación de Pokémon: {e}")
        return False

def importar_efectividad_tipos(connection):
    """Importar datos de efectividad de tipos"""
    try:
        cursor = connection.cursor()
        
        print("📥 Importando efectividad de tipos...")
        
        # Verificar si existe el archivo
        if not os.path.exists('Tabla de tipos.csv'):
            print("⚠️ Archivo 'Tabla de tipos.csv' no encontrado.")
            print("📝 Insertando datos básicos de efectividad...")
            
            # Datos básicos de efectividad
            basic_effectiveness = [
                # Súper efectivo (2.0)
                ('Water', 'Fire', 2.0), ('Fire', 'Grass', 2.0), ('Grass', 'Water', 2.0),
                ('Electric', 'Water', 2.0), ('Electric', 'Flying', 2.0),
                ('Ice', 'Grass', 2.0), ('Ice', 'Flying', 2.0), ('Ice', 'Dragon', 2.0),
                ('Fighting', 'Normal', 2.0), ('Fighting', 'Rock', 2.0), ('Fighting', 'Steel', 2.0),
                ('Rock', 'Fire', 2.0), ('Rock', 'Ice', 2.0), ('Rock', 'Flying', 2.0),
                ('Flying', 'Grass', 2.0), ('Flying', 'Fighting', 2.0), ('Flying', 'Bug', 2.0),
                ('Psychic', 'Fighting', 2.0), ('Psychic', 'Poison', 2.0),
                ('Bug', 'Grass', 2.0), ('Bug', 'Psychic', 2.0), ('Bug', 'Dark', 2.0),
                ('Ghost', 'Psychic', 2.0), ('Ghost', 'Ghost', 2.0),
                ('Dragon', 'Dragon', 2.0), ('Dark', 'Psychic', 2.0), ('Dark', 'Ghost', 2.0),
                ('Steel', 'Ice', 2.0), ('Steel', 'Rock', 2.0), ('Steel', 'Fairy', 2.0),
                
                # Resistente (0.5)
                ('Fire', 'Water', 0.5), ('Water', 'Grass', 0.5), ('Grass', 'Fire', 0.5),
                ('Electric', 'Grass', 0.5), ('Flying', 'Electric', 0.5),
                ('Steel', 'Fire', 0.5), ('Steel', 'Water', 0.5), ('Steel', 'Electric', 0.5),
                ('Fire', 'Fire', 0.5), ('Water', 'Water', 0.5), ('Grass', 'Grass', 0.5),
                ('Psychic', 'Psychic', 0.5), ('Fighting', 'Flying', 0.5),
                
                # Inmune (0.0)
                ('Electric', 'Ground', 0.0), ('Ground', 'Flying', 0.0),
                ('Psychic', 'Dark', 0.0), ('Normal', 'Ghost', 0.0),
                ('Fighting', 'Ghost', 0.0), ('Ghost', 'Normal', 0.0)
            ]
            
            insert_query = "INSERT IGNORE INTO type_effectiveness (attacking_type, defending_type, effectiveness) VALUES (%s, %s, %s)"
            cursor.executemany(insert_query, basic_effectiveness)
            
        else:
            # Procesar archivo CSV
            df_types = pd.read_csv('Tabla de tipos.csv', encoding='latin1')
            
            type_effectiveness_data = []
            for _, row in df_types.iterrows():
                defending_type = row['Tipo']
                
                if pd.notna(row.get('Debil', '')):
                    for attacking_type in str(row['Debil']).replace(' ', '').split(','):
                        if attacking_type.strip():
                            type_effectiveness_data.append((attacking_type.strip(), defending_type, 2.0))
                
                if pd.notna(row.get('Resistente', '')):
                    for attacking_type in str(row['Resistente']).replace(' ', '').split(','):
                        if attacking_type.strip():
                            type_effectiveness_data.append((attacking_type.strip(), defending_type, 0.5))
                
                if pd.notna(row.get('Inmune', '')):
                    for attacking_type in str(row['Inmune']).replace(' ', '').split(','):
                        if attacking_type.strip():
                            type_effectiveness_data.append((attacking_type.strip(), defending_type, 0.0))
            
            insert_query = "INSERT IGNORE INTO type_effectiveness (attacking_type, defending_type, effectiveness) VALUES (%s, %s, %s)"
            cursor.executemany(insert_query, type_effectiveness_data)
        
        connection.commit()
        
        # Verificar resultados
        cursor.execute("SELECT COUNT(*) FROM type_effectiveness")
        count = cursor.fetchone()[0]
        print(f"✅ {count} reglas de efectividad importadas!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importando efectividad: {e}")
        return False

def crear_datos_ejemplo(connection):
    """Crear equipos y datos de ejemplo"""
    try:
        cursor = connection.cursor()
        
        print("📝 Creando datos de ejemplo...")
        
        # Insertar equipos de ejemplo
        teams_data = [
            ('Equipo Campeón', 'Mi equipo principal para competitivo', True, False),
            ('Solo Legendarios', 'Equipo de Pokémon legendarios', True, True),
            ('Equipo Inicial', 'Mi primer equipo', False, False),
            ('Equipo Fuego', 'Especialistas en tipo Fuego', True, True),
            ('Equipo Agua', 'Maestros del agua', True, False)
        ]
        
        cursor.executemany(
            "INSERT IGNORE INTO teams (name, description, allow_megas, allow_legendaries) VALUES (%s, %s, %s, %s)",
            teams_data
        )
        
        connection.commit()
        print("✅ Datos de ejemplo creados!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando datos de ejemplo: {e}")
        return False

def verificar_instalacion(connection):
    """Verificar que todo esté funcionando correctamente"""
    try:
        cursor = connection.cursor()
        
        print("\n🔍 VERIFICANDO INSTALACIÓN...")
        
        # Verificar tablas
        cursor.execute("""
            SELECT TABLE_NAME, TABLE_ROWS 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = 'pokemon_team_builder'
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        print("\n📋 Tablas creadas:")
        for table_name, rows in tables:
            print(f"   ✅ {table_name}: {rows if rows else 0} registros")
        
        # Verificar vistas
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM information_schema.VIEWS 
            WHERE TABLE_SCHEMA = 'pokemon_team_builder'
        """)
        
        views = cursor.fetchall()
        print("\n👁️ Vistas creadas:")
        for (view_name,) in views:
            print(f"   ✅ {view_name}")
        
        # Verificar procedimientos
        cursor.execute("""
            SELECT ROUTINE_NAME, ROUTINE_TYPE 
            FROM information_schema.ROUTINES 
            WHERE ROUTINE_SCHEMA = 'pokemon_team_builder'
        """)
        
        routines = cursor.fetchall()
        print("\n⚙️ Procedimientos y Funciones:")
        for routine_name, routine_type in routines:
            print(f"   ✅ {routine_name} ({routine_type})")
        
        # Verificar triggers
        cursor.execute("""
            SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE 
            FROM information_schema.TRIGGERS 
            WHERE TRIGGER_SCHEMA = 'pokemon_team_builder'
        """)
        
        triggers = cursor.fetchall()
        print("\n🔥 Triggers creados:")
        for trigger_name, event, table in triggers:
            print(f"   ✅ {trigger_name} ({event} on {table})")
        
        # Probar una consulta básica
        cursor.execute("SELECT COUNT(*) FROM pokemon WHERE legendary = true")
        legendary_count = cursor.fetchone()[0]
        print(f"\n📊 Prueba rápida: {legendary_count} Pokémon legendarios encontrados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 INICIANDO IMPORTACIÓN COMPLETA DE POKÉMON TEAM BUILDER")
    print("=" * 70)
    
    # Verificar archivos
    if not verificar_archivos():
        print("\n❌ Proceso detenido. Corrige los archivos faltantes.")
        return
    
    # Conectar a la base de datos
    connection = conectar_bd()
    if not connection:
        print("\n❌ No se pudo conectar a la base de datos.")
        return
    
    try:
        # Paso 1: Crear estructura
        if not ejecutar_sql_completo(connection):
            print("❌ Error creando estructura básica")
            return
        
        # Paso 2: Crear vistas y procedimientos
        if not crear_vistas_y_procedimientos(connection):
            print("❌ Error creando objetos SQL avanzados")
            return
        
        # Paso 3: Procesar datos Pokémon
        df_pokemon = procesar_pokemon_data()
        if df_pokemon is None:
            print("❌ Error procesando datos Pokémon")
            return
        
        # Paso 4: Importar datos Pokémon
        if not importar_pokemon_data(connection, df_pokemon):
            print("❌ Error importando datos Pokémon")
            return
        
        # Paso 5: Importar efectividad de tipos
        if not importar_efectividad_tipos(connection):
            print("❌ Error importando efectividad")
            return
        
        # Paso 6: Crear datos de ejemplo
        if not crear_datos_ejemplo(connection):
            print("❌ Error creando datos de ejemplo")
            return
        
        # Paso 7: Verificar instalación
        if not verificar_instalacion(connection):
            print("❌ Error en verificación final")
            return
        
        print("\n" + "🎉" * 20)
        print("🎉 ¡IMPORTACIÓN COMPLETADA EXITOSAMENTE! 🎉")
        print("🎉" * 20)
        print("\n✅ Tu base de datos está lista para:")
        print("   🔸 Ejecutar la aplicación Streamlit")
        print("   🔸 Realizar consultas complejas")
        print("   🔸 Analizar equipos Pokémon")
        print("   🔸 Demostrar funcionalidades avanzadas")
        print("\n💡 Para ejecutar la app: streamlit run app.py")
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\n🔌 Conexión cerrada.")

if __name__ == "__main__":
    main()