from flask import Blueprint, request, jsonify, session
from ..database import authenticate_user, save_diagnostic, get_benchmark_stats

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
        
        diagnostic_id = save_diagnostic(
            user_id=user_data.get('id'),
            company_name=data.get('company_name', user_data.get('company_name', '')),
            contact_person=data.get('contact_person', user_data.get('contact_person', '')),
            email=data.get('email', user_data.get('email', '')),
            industry=data.get('industry', user_data.get('industry', 'servicios')),
            company_size=data.get('company_size', user_data.get('company_size', 'startup')),
            responses=data.get('responses', {}),
            scores=data.get('scores', {}),
            overall_score=data.get('overall_score', 0)
        )
        
        if diagnostic_id:
            return jsonify({
                'success': True,
                'message': 'Diagnóstico guardado exitosamente',
                'diagnostic_id': diagnostic_id
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
        stats = get_benchmark_stats()
        if stats:
            return jsonify(stats)
        else:
            # Retornar datos por defecto si no hay estadísticas
            return jsonify({
                'overall': {
                    'average': 3.0,
                    'min': 1.0,
                    'max': 5.0,
                    'count': 0
                },
                'dimensions': {
                    f'dimension_{i}': {
                        'average': 3.0,
                        'min': 1.0,
                        'max': 5.0,
                        'count': 0
                    } for i in range(1, 7)
                }
            })
    except Exception as e:
        print(f"Error getting benchmark stats: {e}")
        return jsonify({'error': 'Error obteniendo estadísticas'}), 500
