"""
Endpoint simple y robusto para guardar progreso del cuestionario
"""
from flask import Blueprint, request, jsonify, session
import psycopg2
import psycopg2.extras
import os
import json

save_progress_bp = Blueprint('save_progress', __name__)

def get_connection():
    """Get a PostgreSQL database connection"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    return psycopg2.connect(DATABASE_URL)

@save_progress_bp.route('/api/save-progress', methods=['POST'])
def save_progress():
    """Guardar progreso del cuestionario - endpoint simple y robusto"""
    try:
        # Verificar sesión
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'No autenticado'}), 401
        
        # Obtener datos del request
        data = request.get_json()
        responses = data.get('responses', {})
        
        if not responses:
            return jsonify({'error': 'No hay respuestas para guardar'}), 400
        
        # Calcular score y level
        total_score = sum(responses.values())
        answered_count = len(responses)
        overall_score = total_score / answered_count if answered_count > 0 else 0
        
        # Determinar nivel
        if overall_score >= 4.5:
            level = 'optimizado'
        elif overall_score >= 3.5:
            level = 'avanzado'
        elif overall_score >= 2.5:
            level = 'intermedio'
        elif overall_score >= 1.5:
            level = 'básico'
        else:
            level = 'inicial'
        
        # Conectar a la base de datos
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existe un diagnóstico para este usuario
        cursor.execute('SELECT id FROM diagnostics WHERE user_id = %s', (user_id,))
        existing = cursor.fetchone()
        
        # Convertir responses a JSON string
        responses_json = json.dumps(responses)
        
        if existing:
            # UPDATE
            cursor.execute('''
                UPDATE diagnostics 
                SET responses = %s, score = %s, level = %s, completed_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            ''', (responses_json, overall_score, level, user_id))
        else:
            # INSERT
            cursor.execute('''
                INSERT INTO diagnostics (user_id, responses, score, level)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, responses_json, overall_score, level))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Progreso guardado correctamente',
            'progress': {
                'answered': answered_count,
                'score': round(overall_score, 2),
                'level': level
            }
        }), 200
        
    except Exception as e:
        print(f"Error en save_progress: {str(e)}")
        return jsonify({'error': f'Error guardando progreso: {str(e)}'}), 500
