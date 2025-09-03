import pandas as pd

print("--- Verificando duplicados en el archivo pokemon.csv ---")

try:
    # Cargar el archivo CSV
    df = pd.read_csv('Pokemon.csv')

    # El dataset de Kaggle usa '#' como la columna del número de Pokedex.
    # Si en tu archivo se llama diferente, solo cambia el nombre aquí.
    columna_id = '#'

    # Busca todos los valores en la columna ID que aparecen más de una vez
    duplicados = df[df.duplicated(subset=[columna_id], keep=False)]

    if not duplicados.empty:
        print("\n¡ALERTA! SE ENCONTRARON DUPLICADOS EN EL ARCHIVO CSV.")
        print("Estas son todas las filas con números de Pokédex repetidos:")
        # Ordenamos por el ID para ver los duplicados juntos
        print(duplicados.sort_values(by=columna_id))
    else:
        print("\n¡Éxito! No se encontraron IDs duplicados en el archivo CSV.")

except FileNotFoundError:
    print("\nERROR: No se encontró el archivo en 'data/pokemon.csv'. Asegúrate de que la ruta sea correcta.")
except KeyError:
    print(f"\nERROR: No se encontró la columna '{columna_id}'. Revisa el nombre de la columna en tu archivo CSV.")