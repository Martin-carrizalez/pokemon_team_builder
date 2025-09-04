# SOLUCIÓN COMPLETA: Manejo Inteligente de Duplicados Pokémon
# Este script maneja las formas alternativas (Mega, regionales, etc.) como ventaja del proyecto

import pandas as pd
import mysql.connector
from mysql.connector import Error

def analyze_duplicates():
    """Analizar y categorizar los duplicados del dataset"""
    df = pd.read_csv('Pokemon.csv')
    
    print(f"📊 Dataset original: {len(df)} filas")
    
    # Encontrar duplicados por número de Pokédex
    duplicates = df[df.duplicated(subset=['#'], keep=False)].sort_values('#')
    print(f"🔍 Filas con números repetidos: {len(duplicates)}")
    
    # Categorizar formas alternativas
    df['form_type'] = 'base'
    df['is_mega'] = df['Name'].str.contains('Mega', na=False, case=False)
    df['is_primal'] = df['Name'].str.contains('Primal', na=False, case=False)
    df['is_regional'] = df['Name'].str.contains('Alolan|Galarian', na=False, case=False)
    df['is_alternate'] = df['Name'].str.contains('|'.join([
        'Mega', 'Primal', 'Alolan', 'Galarian', 'Super Size', 
        'Confined', 'Unbound', 'Attack Forme', 'Defense Forme'
    ]), na=False, case=False)
    
    # Asignar tipos de forma
    df.loc[df['is_mega'], 'form_type'] = 'mega'
    df.loc[df['is_primal'], 'form_type'] = 'primal'
    df.loc[df['is_regional'], 'form_type'] = 'regional'
    df.loc[df['is_alternate'] & (df['form_type'] == 'base'), 'form_type'] = 'special'
    
    # Crear nombre base limpio
    df['base_name'] = df['Name'].str.replace(
        r'Mega |Primal |Alolan |Galarian |Super Size|Confined|Unbound|Attack Forme|Defense Forme', 
        '', regex=True
    ).str.strip()
    
    # Estadísticas
    form_stats = df['form_type'].value_counts()
    print("\n📈 Distribución de formas:")
    for form, count in form_stats.items():
        print(f"   {form.title()}: {count}")
    
    return df

def create_enhanced_database():
    """Crear esquema de BD optimizado para formas alternativas"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='pokemon_team_builder',
            user='root',
            password='2076O8233e*'  # CAMBIAR POR TU PASSWORD
        )
        cursor = connection.cursor()
        
        # Eliminar tablas existentes
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS team_members, teams, type_effectiveness, pokemon")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Tabla principal mejorada
        cursor.execute("""
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
            
            -- Índices para optimización
            INDEX idx_pokedex (pokedex_number),
            INDEX idx_base_name (base_name),
            INDEX idx_form_type (form_type),
            INDEX idx_type1 (type1),
            INDEX idx_generation (generation),
            INDEX idx_legendary (legendary)
        )
        """)
        
        # Tabla de efectividad de tipos (BONUS para consultas complejas)
        cursor.execute("""
        CREATE TABLE type_effectiveness (
            id INT PRIMARY KEY AUTO_INCREMENT,
            attacking_type VARCHAR(20) NOT NULL,
            defending_type VARCHAR(20) NOT NULL,
            effectiveness DECIMAL(3,2) NOT NULL,
            
            INDEX idx_attacking (attacking_type),
            INDEX idx_defending (defending_type)
        )
        """)
        
        # Tabla de equipos
        cursor.execute("""
        CREATE TABLE teams (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            allow_megas BOOLEAN DEFAULT TRUE,
            allow_legendaries BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX idx_created (created_at)
        )
        """)
        
        # Tabla de miembros de equipo
        cursor.execute("""
        CREATE TABLE team_members (
            id INT PRIMARY KEY AUTO_INCREMENT,
            team_id INT NOT NULL,
            pokemon_unique_id INT NOT NULL,
            position INT NOT NULL CHECK (position BETWEEN 1 AND 6),
            nickname VARCHAR(50),
            
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
            FOREIGN KEY (pokemon_unique_id) REFERENCES pokemon(unique_id),
            UNIQUE KEY unique_team_position (team_id, position)
        )
        """)
        
        # Datos básicos de efectividad de tipos
        # --- 4. Insertar Datos de Efectividad Completos desde el CSV ---
        print("➡️ Insertando datos de efectividad completos desde el archivo...")

        # Asegúrate de que tus archivos CSV están en una carpeta llamada 'data'
        # Si no es así, cambia la ruta aquí.
        df_types = pd.read_csv('Tabla de tipos.csv', encoding='latin1')

        type_effectiveness_data = []
        for _, row in df_types.iterrows():
            defending_type = row['Tipo']
            if pd.notna(row['Debil']):
                for attacking_type in row['Debil'].replace(' ','').split(','):
                    type_effectiveness_data.append((attacking_type, defending_type, 2.0))
            if pd.notna(row['Resistente']):
                for attacking_type in row['Resistente'].replace(' ','').split(','):
                    type_effectiveness_data.append((attacking_type, defending_type, 0.5))
            if pd.notna(row['Inmune']):
                for attacking_type in row['Inmune'].replace(' ','').split(','):
                    type_effectiveness_data.append((attacking_type, defending_type, 0.0))

        # TRUNCATE asegura que la tabla esté vacía antes de insertar los nuevos datos
        cursor.execute("TRUNCATE TABLE type_effectiveness;")

        type_insert_query = "INSERT INTO type_effectiveness (attacking_type, defending_type, effectiveness) VALUES (%s, %s, %s)"
        cursor.executemany(type_insert_query, type_effectiveness_data)
        print(f"✅ ¡{cursor.rowcount} reglas de efectividad completas insertadas!")
        
        connection.commit()
        print("✅ Base de datos mejorada creada exitosamente!")
        
    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def import_pokemon_data():
    """Importar datos con manejo inteligente de duplicados"""
    df = analyze_duplicates()
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='pokemon_team_builder',
            user='root',
            password='2076O8233e*'  # CAMBIAR
        )
        cursor = connection.cursor()
        
        # Preparar datos para inserción
        insert_query = """
        INSERT INTO pokemon (pokedex_number, name, base_name, form_type, type1, type2,
                           total_stats, hp, attack, defense, sp_attack, sp_defense, speed,
                           generation, legendary, is_alternate)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        successful_inserts = 0
        for _, row in df.iterrows():
            try:
                values = (
                    int(row['#']),                           # pokedex_number
                    row['Name'],                             # name
                    row['base_name'],                        # base_name
                    row['form_type'],                        # form_type
                    row['Type 1'],                           # type1
                    row['Type 2'] if pd.notna(row['Type 2']) else None,  # type2
                    int(row['Total']),                       # total_stats
                    int(row['HP']),                          # hp
                    int(row['Attack']),                      # attack
                    int(row['Defense']),                     # defense
                    int(row['Sp. Atk']),                     # sp_attack
                    int(row['Sp. Def']),                     # sp_defense
                    int(row['Speed']),                       # speed
                    int(row['Generation']),                  # generation
                    bool(row['Legendary']),                  # legendary
                    bool(row['is_alternate'])                # is_alternate
                )
                cursor.execute(insert_query, values)
                successful_inserts += 1
            except Exception as e:
                print(f"⚠️ Error insertando {row['Name']}: {e}")
        
        connection.commit()
        print(f"✅ {successful_inserts} Pokémon importados exitosamente!")
        
        # Verificar resultados
        cursor.execute("SELECT form_type, COUNT(*) as count FROM pokemon GROUP BY form_type")
        results = cursor.fetchall()
        print("\n📊 Resumen final:")
        for form_type, count in results:
            print(f"   {form_type.title()}: {count} Pokémon")
            
    except Error as e:
        print(f"❌ Error en importación: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def create_advanced_queries():
    """Consultas SQL complejas que aprovechan las formas alternativas"""
    queries = {
        "mega_power_boost": """
        -- Top 10 Pokémon con mayor incremento de stats por Mega Evolución
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
        LIMIT 10;
        """,
        
        "pokemon_with_most_forms": """
        -- Pokémon con más formas alternativas
        SELECT 
            base_name,
            COUNT(*) as total_formas,
            GROUP_CONCAT(DISTINCT form_type ORDER BY form_type) as tipos_formas,
            MAX(total_stats) as stats_maximas,
            MIN(total_stats) as stats_minimas
        FROM pokemon 
        GROUP BY base_name 
        HAVING total_formas > 1
        ORDER BY total_formas DESC, stats_maximas DESC;
        """,
        
        "type_distribution_by_form": """
        -- Distribución de tipos por forma
        SELECT 
            form_type,
            type1,
            COUNT(*) as cantidad,
            AVG(total_stats) as promedio_stats
        FROM pokemon 
        GROUP BY form_type, type1
        ORDER BY form_type, cantidad DESC;
        """,
        
        "legendary_analysis": """
        -- Análisis de Pokémon legendarios por forma
        SELECT 
            form_type,
            COUNT(*) as total,
            SUM(CASE WHEN legendary = 1 THEN 1 ELSE 0 END) as legendarios,
            ROUND(SUM(CASE WHEN legendary = 1 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as porcentaje_legendarios,
            AVG(total_stats) as promedio_stats
        FROM pokemon 
        GROUP BY form_type
        ORDER BY porcentaje_legendarios DESC;
        """
    }
    
    print("\n🔍 CONSULTAS SQL AVANZADAS GENERADAS:")
    for name, query in queries.items():
        print(f"\n--- {name.upper().replace('_', ' ')} ---")
        print(query)
    
    return queries

# FUNCIÓN PRINCIPAL
def main():
    """Ejecutar todo el proceso de manejo inteligente de duplicados"""
    print("🚀 INICIANDO MANEJO INTELIGENTE DE DUPLICADOS POKÉMON")
    print("=" * 60)
    
    # Paso 1: Analizar duplicados
    print("\n1️⃣ ANALIZANDO DUPLICADOS...")
    df = analyze_duplicates()
    
    # Paso 2: Crear base de datos mejorada
    print("\n2️⃣ CREANDO BASE DE DATOS MEJORADA...")
    create_enhanced_database()
    
    # Paso 3: Importar datos
    print("\n3️⃣ IMPORTANDO DATOS...")
    import_pokemon_data()
    
    # Paso 4: Generar consultas avanzadas
    print("\n4️⃣ GENERANDO CONSULTAS AVANZADAS...")
    queries = create_advanced_queries()
    
    print("\n🎉 ¡PROCESO COMPLETADO!")
    print("✅ Tu dataset ahora incluye:")
    print("   - Formas base y alternativas")
    print("   - Mega Evoluciones")
    print("   - Formas regionales")
    print("   - Estructura optimizada para consultas complejas")
    print("   - Consultas SQL avanzadas listas")
    
    return queries

if __name__ == "__main__":
    # EJECUTAR TODO EL PROCESO
    main()