from flask import Blueprint, request, jsonify, session
from src.simple_users import authenticate_user

simple_user_bp = Blueprint('simple_user', __name__)

@simple_user_bp.route('/login', methods=['POST'])
def user_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username y password requeridos'}), 400
        
        # Autenticar usuario
        user = authenticate_user(username, password)
        
        if user and not user.get('is_admin'):
            session['user_logged_in'] = True
            session['user_id'] = username
            session['username'] = username
            session.permanent = True
            
            return jsonify({
                'success': True,
                'user': {
                    'id': username,
                    'username': username,
                    'company_name': user.get('company_name', ''),
                    'contact_person': user.get('contact_person', ''),
                    'email': user.get('email', '')
                }
            })
        
        return jsonify({'error': 'Credenciales incorrectas'}), 401
        
    except Exception as e:
        return jsonify({'error': f'Error en login: {str(e)}'}), 500

@simple_user_bp.route('/logout', methods=['POST'])
def user_logout():
    session.pop('user_logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({'success': True, 'message': 'Logout exitoso'})

@simple_user_bp.route('/profile', methods=['GET'])
def get_profile():
    try:
        if 'user_logged_in' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        username = session.get('username')
        user = authenticate_user(username, '')  # Solo para obtener datos
        
        if user:
            return jsonify({
                'user': {
                    'id': username,
                    'username': username,
                    'company_name': user.get('company_name', ''),
                    'contact_person': user.get('contact_person', ''),
                    'email': user.get('email', '')
                }
            })
        
        return jsonify({'error': 'Usuario no encontrado'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Error obteniendo perfil: {str(e)}'}), 500
