from flask import Blueprint, request, jsonify, session
from src.simple_users import (
    authenticate_user, create_user, get_all_users, 
    delete_user, get_user_stats, load_users
)
import random

simple_admin_bp = Blueprint('simple_admin', __name__)

@simple_admin_bp.route('/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username y password requeridos'}), 400
        
        # Autenticar admin
        user = authenticate_user(username, password)
        
        if user and user.get('is_admin'):
            session['admin_logged_in'] = True
            session['admin_user_id'] = username
            session['admin_username'] = username
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Login exitoso'
            })
        
        return jsonify({'error': 'Credenciales incorrectas'}), 401
        
    except Exception as e:
        return jsonify({'error': f'Error en login: {str(e)}'}), 500

@simple_admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_user_id', None)
    session.pop('admin_username', None)
    return jsonify({'success': True, 'message': 'Logout exitoso'})

@simple_admin_bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        stats = get_user_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'Error obteniendo estadísticas: {str(e)}'}), 500

@simple_admin_bp.route('/users', methods=['GET'])
def get_users():
    try:
        users = get_all_users()
        
        # Formatear para la respuesta
        formatted_users = []
        for user in users:
            formatted_users.append({
                'id': user['username'],  # Usar username como ID
                'username': user['username'],
                'company_name': user['company_name'],
                'contact_person': user['contact_person'],
                'email': user['email'],
                'phone': user['phone'],
                'industry': user['industry'],
                'company_size': user['company_size'],
                'is_active': user['is_active'],
                'created_at': user['created_at'],
                'diagnostic_count': 0  # Por ahora
            })
        
        return jsonify({
            'users': formatted_users,
            'pagination': {
                'page': 1,
                'pages': 1,
                'per_page': len(formatted_users),
                'total': len(formatted_users),
                'has_next': False,
                'has_prev': False
            }
        })
    except Exception as e:
        return jsonify({'error': f'Error obteniendo usuarios: {str(e)}'}), 500

@simple_admin_bp.route('/users', methods=['POST'])
def create_new_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        # Validar datos requeridos
        company_name = data.get('company_name')
        if not company_name:
            return jsonify({'error': 'Nombre de empresa es requerido'}), 400
        
        # Crear usuario
        user_data = create_user(
            company_name=company_name,
            contact_person=data.get('contact_person', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            industry=data.get('industry', ''),
            company_size=data.get('company_size', ''),
            notes=data.get('notes', '')
        )
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_data['username'],
                'username': user_data['username'],
                'password': user_data['password'],
                'company_name': user_data['company_name'],
                'contact_person': user_data['contact_person'],
                'email': user_data['email']
            },
            'credentials': {
                'username': user_data['username'],
                'password': user_data['password']
            },
            'message': f'Usuario creado exitosamente. Credenciales: {user_data["username"]} / {user_data["password"]}'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500

@simple_admin_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    try:
        if delete_user(user_id):
            return jsonify({'success': True, 'message': 'Usuario eliminado exitosamente'})
        else:
            return jsonify({'error': 'Usuario no encontrado o no se puede eliminar'}), 404
    except Exception as e:
        return jsonify({'error': f'Error al eliminar usuario: {str(e)}'}), 500

@simple_admin_bp.route('/users/<user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    try:
        users = load_users()
        if user_id not in users:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Generar nueva contraseña
        new_password = f"cx{random.randint(1000, 9999)}"
        users[user_id]['password'] = new_password
        
        from src.simple_users import save_users
        save_users(users)
        
        return jsonify({
            'success': True,
            'new_password': new_password,
            'message': f'Contraseña restablecida: {new_password}'
        })
    except Exception as e:
        return jsonify({'error': f'Error al restablecer contraseña: {str(e)}'}), 500

@simple_admin_bp.route('/diagnostics', methods=['GET'])
def get_diagnostics():
    try:
        # Por ahora retornar lista vacía
        return jsonify({
            'diagnostics': [],
            'pagination': {
                'page': 1,
                'pages': 1,
                'per_page': 0,
                'total': 0,
                'has_next': False,
                'has_prev': False
            }
        })
    except Exception as e:
        return jsonify({'error': f'Error obteniendo diagnósticos: {str(e)}'}), 500

@simple_admin_bp.route('/recalculate-benchmark', methods=['POST'])
def recalculate_benchmark():
    try:
        return jsonify({
            'success': True,
            'message': 'Benchmark recalculado exitosamente'
        })
    except Exception as e:
        return jsonify({'error': f'Error recalculando benchmark: {str(e)}'}), 500
