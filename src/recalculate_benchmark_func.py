"""
Función para recalcular benchmark - para agregar a database_pg.py
"""
from collections import defaultdict

# Mapeo de preguntas a dimensiones
DIMENSION_MAPPING = {
    '1': 'estrategia_cx',
    '2': 'arquitectura_cx',
    '3': 'insights_cx',
    '4': 'cultura_cambio',
    '5': 'innovacion_cx',
    '6': 'governance_cx'
}

def extract_dimension_from_key(key):
    """Extraer el número de dimensión de una clave como '1.1.1' -> '1'"""
    if isinstance(key, str) and '.' in key:
        return key.split('.')[0]
    return None

def recalculate_benchmark_stats():
    """Recalcular estadísticas de benchmarking desde las respuestas reales"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Obtener todos los diagnósticos completos
        cursor.execute("""
            SELECT id, user_id, responses
            FROM diagnostics
            WHERE responses IS NOT NULL
        """)
        
        diagnostics = cursor.fetchall()
        
        if not diagnostics:
            cursor.close()
            conn.close()
            return {
                'success': False,
                'message': 'No hay diagnósticos para calcular benchmark'
            }
        
        # Calcular promedios por dimensión
        dimension_scores = defaultdict(list)
        
        for diag in diagnostics:
            responses = diag['responses']
            
            # Agrupar respuestas por dimensión
            dimension_responses = defaultdict(list)
            
            for key, value in responses.items():
                dim_id = extract_dimension_from_key(key)
                if dim_id and dim_id in DIMENSION_MAPPING:
                    dimension_responses[dim_id].append(value)
            
            # Calcular promedio por dimensión para este diagnóstico
            for dim_id, values in dimension_responses.items():
                if values:
                    avg = sum(values) / len(values)
                    dimension_scores[DIMENSION_MAPPING[dim_id]].append(avg)
        
        # Actualizar benchmark_stats
        for dim_name, scores in dimension_scores.items():
            if scores:
                global_avg = sum(scores) / len(scores)
                
                # Primero intentar actualizar
                cursor.execute("""
                    UPDATE benchmark_stats 
                    SET avg_score = %s, total_diagnostics = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE dimension = %s
                """, (global_avg, len(scores), dim_name))
                
                # Si no se actualizó ninguna fila, insertar
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO benchmark_stats (dimension, avg_score, total_diagnostics, updated_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """, (dim_name, global_avg, len(scores)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'Benchmark recalculado con {len(diagnostics)} diagnósticos',
            'total_diagnostics': len(diagnostics),
            'dimensions_updated': len(dimension_scores)
        }
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Error recalculando benchmark: {e}")
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }
