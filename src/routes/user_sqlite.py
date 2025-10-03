from flask import Blueprint, request, jsonify, session
from ..database_pg import authenticate_user, save_diagnostic, calculate_benchmark, get_user_diagnostic

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

@user_bp.route('/logout', methods=['POST'])
def logout():
    """Logout de usuario"""
    session.pop('user_logged_in', None)
    session.pop('username', None)
    session.pop('user_data', None)
    return jsonify({'success': True, 'message': 'Logout exitoso'})

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
        benchmark = calculate_benchmark()
        
        if not benchmark or benchmark.get('total_diagnostics', 0) == 0:
            # Si no hay datos, retornar N/A
            return jsonify({
                'total_diagnostics': 0,
                'dimensions': {}
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
