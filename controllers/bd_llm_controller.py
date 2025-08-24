import json
import os
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, MetaData, Table
from sqlalchemy.orm import sessionmaker
from orchestator_controller import init_llm
from partial_json_parser import loads

# --- Configuración de la Base de Datos ---
# Es una buena práctica cargar esto desde variables de entorno o un archivo de configuración.
# Usará una base de datos SQLite en memoria para este ejemplo.
DATABASE_URL = "sqlite:///bd/chilecompra.db" 

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
llm = init_llm()

def get_db_schema(engine_instance):
    """
    Obtiene el esquema de la base de datos (tablas y columnas).
    Esta información se le pasará al LLM para que entienda la estructura de los datos.
    """
    inspector = inspect(engine_instance)
    schema = {}
    for table_name in inspector.get_table_names():
        columns = [column['name'] for column in inspector.get_columns(table_name)]
        schema[table_name] = columns
    return schema

def generate_query_params_from_llm(user_question: str, db_schema: dict):
    """
    Utiliza un LLM para interpretar la pregunta del usuario y generar parámetros para la consulta.
    IMPORTANTE: Esta función NO genera SQL. Solo extrae la información necesaria.
    
    Args:
        user_question: La pregunta en lenguaje natural del usuario.
        db_schema: El esquema de la base de datos.

    Returns:
        Un diccionario con los parámetros para construir la consulta.
    """
    # --- Aquí iría la llamada a tu LLM (ej. OpenAI, Anthropic, etc.) ---
    # El prompt al LLM debería ser algo como:
    # "Dado el siguiente esquema de base de datos {db_schema} y la pregunta '{user_question}',
    # extrae la tabla, las columnas y los filtros necesarios en formato JSON.
    # Las columnas pueden incluir funciones de agregación como SUM, AVG, COUNT.
    # Los filtros deben ser un diccionario de 'columna': 'valor'."

    db_query = f"""Tu tarea es actuar como un experto analista de datos y SQL. Dada una pregunta de usuario y un esquema de base de datos, tu objetivo es generar un objeto JSON con los parámetros necesarios para construir una consulta SQL que responda a la pregunta.

### Esquema de la Base de Datos:
```json
{json.dumps(db_schema, indent=4)}
```

### Pregunta del Usuario:
'{user_question}'

### Instrucciones Detalladas:
1.  **Analiza la Pregunta:** Comprende qué información está pidiendo el usuario. Identifica las métricas clave (ej. suma de montos, conteo de items), las dimensiones (ej. por unidad de compra, por proveedor) y los filtros (ej. solo de una región, en un rango de fechas).
2.  **Examina el Esquema:** Localiza las tablas y columnas que contienen la información necesaria. Presta especial atención a las columnas que parecen ser claves foráneas para conectar tablas (ej. `ordenes_de_compra.CodigoUnidadCompra` probablemente se conecta con `unidades.Codigo`).
3.  **Planifica la Consulta (Paso a Paso):**
    -   ¿Qué tabla es la principal (FROM)?
    -   ¿Necesito unir (JOIN) con otras tablas? ¿Cuáles y usando qué columnas?
    -   ¿Qué columnas necesito seleccionar (SELECT)? ¿Necesito aplicar funciones de agregación (SUM, COUNT, AVG)?
    -   ¿Qué filtros necesito aplicar (WHERE)?
    -   ¿Necesito agrupar los resultados (GROUP BY)?
    -   ¿Necesito ordenar los resultados (ORDER BY)?
    -   ¿Necesito limitar el número de resultados (LIMIT)?
4.  **Genera el JSON:** Basado en tu plan, construye el objeto JSON. El JSON debe tener la siguiente estructura:
    -   `table`: (string) La tabla principal de la cláusula FROM.
    -   `joins`: (opcional, array de objetos) Lista de tablas a unir. Cada objeto debe tener `type` (ej. "INNER JOIN"), `target_table` (la tabla a unir) y `on` (la condición de unión, ej. "ordenes_de_compra.CodigoUnidadCompra = unidades.Codigo").
    -   `columns`: (array de strings) Las columnas a seleccionar. Usa el formato `tabla.columna` si hay joins. Puedes incluir alias (ej. "SUM(ordenes_de_compra.MontoTotalOC_PesosChilenos) as GastoTotal").
    -   `filters`: (opcional, objeto) Pares clave-valor para la cláusula WHERE.
    -   `group_by`: (opcional, array de strings) Columnas para la cláusula GROUP BY.
    -   `order_by`: (opcional, string) La cláusula ORDER BY completa (ej. "GastoTotal DESC").
    -   `limit`: (opcional, integer) El número de filas a devolver.
    rellena los datos en este json """+""" {"table": "", "joins": [], "columns": [], "filters": [], "group_by": [], "order_by": "", "limit": 0}
Ahora, sigue estos pasos y genera únicamente el objeto JSON para la pregunta del usuario."""
    
    response = llm.invoke(db_query)
    print(f"Pregunta del usuario: {user_question}")
    print(f"Esquema de BD: {db_schema}\n\n")
    print(f"Respuesta del LLM (Objeto): {response.content}")

    return loads(response.content)


def build_and_execute_query(query_params: dict):
    """
    Construye y ejecuta una consulta SQL de forma segura utilizando SQLAlchemy.
    Maneja joins, group by, order by, y limit.
    """
    table = query_params.get("table")
    if not table:
        raise ValueError("El LLM no proporcionó una tabla ('table') para la consulta.")

    columns = query_params.get("columns")
    if not columns or not isinstance(columns, list):
        raise ValueError("El LLM debe proporcionar una lista de 'columns'.")

    joins = query_params.get("joins", [])
    filters = query_params.get("filters", {})
    group_by = query_params.get("group_by", [])
    order_by = query_params.get("order_by")
    limit = query_params.get("limit")

    # --- Construcción de la consulta --- 
    cols_str = ", ".join(columns)
    query_str = f"SELECT {cols_str} FROM {table}"

    # Joins
    if joins:
        for join in joins:
            join_type = join.get("type", "INNER JOIN")
            target_table = join.get("target_table")
            on_clause = join.get("on")
            if not target_table or not on_clause:
                continue # Ignorar joins malformados
            query_str += f" {join_type} {target_table} ON {on_clause}"

    # Where
    params = {}
    if filters:
        filter_clauses = []
        for i, (key, value) in enumerate(filters.items()):
            param_name = f"param_{i}"
            filter_clauses.append(f"{key} = :{param_name}")
            params[param_name] = value
        query_str += " WHERE " + " AND ".join(filter_clauses)

    # Group By
    if group_by:
        group_by_str = ", ".join(group_by)
        query_str += f" GROUP BY {group_by_str}"

    # Order By
    if order_by:
        query_str += f" ORDER BY {order_by}"

    # Limit
    if limit:
        if not isinstance(limit, int):
            raise ValueError("El límite debe ser un número entero.")
        query_str += f" LIMIT :limit"
        params["limit"] = limit

    print(f"\n--- Consulta SQL a ejecutar ---")
    print(f"Query: {query_str}")
    print(f"Params: {params}")

    with SessionLocal() as session:
        query = text(query_str)
        result = session.execute(query, params)
        return result.fetchall()

# --- Ejemplo de uso ---
if __name__ == "__main__":
    
    # 2. Obtener el esquema de la base de datos
    db_schema = get_db_schema(engine)

    # 3. Simular una pregunta del usuario
    pregunta = "Muéstrame el nombre y el monto de las 10 últimas licitaciones publicadas"

    # 4. Usar el LLM (simulado) para obtener los parámetros de la consulta
    params_from_llm = generate_query_params_from_llm(pregunta, db_schema)

    # 5. Construir y ejecutar la consulta de forma segura
    try:
        resultados = build_and_execute_query(params_from_llm)
        print("\n--- Resultados de la Consulta ---")
        if resultados:
            for row in resultados:
                print(row)
        else:
            print("No se encontraron resultados.")
    except (ValueError, Exception) as e:
        print(f"Error: {e}")
