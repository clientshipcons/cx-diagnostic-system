from flask import Blueprint, request, jsonify, session
from ..database_pg import authenticate_user, save_diagnostic, calculate_benchmark, get_user_diagnostic, get_benchmark_stats

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    """Login de usuario"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Verificar credenciales demo hardcodeadas
        if username == 'demo' and password == 'demo123':
            session['user_logged_in'] = True
            session['username'] = username
            session['user_data'] = {
                'id': 0,
                'username': 'demo',
                'company_name': 'Clientship Demo',
                'contact_person': 'Usuario Demo',
                'email': 'demo@clientship.com',
                'industry': 'consultoria',
                'company_size': 'startup'
            }
            return jsonify({
                'success': True,
                'user': session['user_data']
            })
        
        # Verificar en base de datos
        user = authenticate_user(username, password)
        if user:
            session['user_logged_in'] = True
            session['username'] = username
            session['user_data'] = user
            return jsonify({
                'success': True,
                'user': user
            })
        
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401
        
    except Exception as e:
        print(f"Error in user login: {e}")
        return jsonify({'success': False, 'message': 'Error interno'}), 500

@user_bp.route('/register', methods=['POST'])
def register():
    """Registro temporal de usuarios para pruebas"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        company_name = data.get('company_name', 'Test Company')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username y password requeridos'}), 400
        
        # Importar aquí para evitar problemas circulares
        from werkzeug.security import generate_password_hash
        import psycopg2
        import os
        
        # Conectar a la base de datos
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # Verificar si el usuario ya existe
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Usuario ya existe'}), 400
        
        # Crear usuario (contraseña en texto plano como lo hace el sistema)
        cur.execute("""
            INSERT INTO users (username, password, company_name, is_active, is_admin)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (username, password, company_name, True, False))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Usuario creado exitosamente',
            'user_id': user_id,
            'username': username
        })
        
    except Exception as e:
        print(f"Error in user register: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/logout', methods=['POST'])
def logout():
    """Logout de usuario"""
    # Limpiar completamente la sesión
    session.clear()
    
    # Crear respuesta
    response = jsonify({'success': True, 'message': 'Logout exitoso'})
    
    # Eliminar la cookie de sesión explícitamente
    response.set_cookie('session', '', expires=0, path='/')
    
    return response

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """Obtener perfil del usuario logueado"""
    if not session.get('user_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    return jsonify(session.get('user_data', {}))

@user_bp.route('/save-diagnostic', methods=['POST'])
def save_user_diagnostic():
    """Guardar resultado de diagnóstico"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'error': 'No autorizado'}), 401
        
        data = request.get_json()
        user_data = session.get('user_data', {})
        
        # No guardar diagnósticos de usuario demo
        if user_data.get('username') == 'demo':
            return jsonify({'success': True, 'message': 'Diagnóstico demo no guardado'})
        
        # Usar los parámetros correctos de save_diagnostic
        success = save_diagnostic(
            user_id=user_data.get('id'),
            responses=data.get('responses', {}),
            score=data.get('overall_score', 0),
            level=data.get('level', 'inicial')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Diagnóstico guardado exitosamente'
            })
        else:
            return jsonify({'error': 'Error guardando diagnóstico'}), 500
            
    except Exception as e:
        print(f"Error saving diagnostic: {e}")
        return jsonify({'error': 'Error interno'}), 500

@user_bp.route('/benchmark-stats', methods=['GET'])
def get_benchmark():
    """Obtener estadísticas de benchmark"""
    try:
        benchmark = get_benchmark_stats()
        
        if not benchmark or benchmark.get('total_diagnostics', 0) == 0:
            # Si no hay datos, retornar N/A
            return jsonify({
                'dimensiones': [],
                'total_diagnostics': 0
            })
        
        return jsonify(benchmark)
    except Exception as e:
        print(f"Error getting benchmark stats: {e}")
        return jsonify({'error': 'Error obteniendo estadísticas'}), 500

@user_bp.route('/my-diagnostic', methods=['GET'])
def get_my_diagnostic():
    """Obtener el diagnóstico más reciente del usuario"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'error': 'No autorizado'}), 401
        
        user_data = session.get('user_data', {})
        user_id = user_data.get('id')
        
        if not user_id or user_data.get('username') == 'demo':
            return jsonify({'diagnostic': None})
        
        diagnostic = get_user_diagnostic(user_id)
        return jsonify({'diagnostic': diagnostic})
        
    except Exception as e:
        print(f"Error getting user diagnostic: {e}")
        return jsonify({'error': 'Error obteniendo diagnóstico'}), 500

@user_bp.route('/save-responses', methods=['POST'])
def save_responses():
    """Guardar respuestas del cuestionario"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'error': 'No autorizado'}), 401
        
        user_data = session.get('user_data', {})
        user_id = user_data.get('id')
        
        # Si es usuario demo, no guardar en BD
        if not user_id or user_data.get('username') == 'demo':
            return jsonify({'success': True, 'message': 'Demo user - not saved'})
        
        data = request.get_json()
        responses = data.get('responses', {})
        
        # Calcular score promedio
        if responses:
            total_score = sum(responses.values())
            avg_score = total_score / len(responses)
        else:
            avg_score = 0
        
        # Determinar nivel de madurez
        if avg_score >= 4.5:
            level = 'optimizado'
        elif avg_score >= 3.5:
            level = 'avanzado'
        elif avg_score >= 2.5:
            level = 'intermedio'
        elif avg_score >= 1.5:
            level = 'basico'
        else:
            level = 'inicial'
        
        # Guardar el diagnóstico con las respuestas actualizadas
        save_diagnostic(user_id, responses, avg_score, level)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error saving responses: {e}")
        return jsonify({'error': 'Error guardando respuestas'}), 500
