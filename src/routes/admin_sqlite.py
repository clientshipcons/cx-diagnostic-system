from flask import Blueprint, request, jsonify, session
from ..database import (
    authenticate_user, create_user, get_all_users, delete_user, 
    reset_password, get_user_stats, get_all_diagnostics, delete_diagnostic
)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Login de administrador"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Verificar credenciales hardcodeadas temporalmente
        if username == 'admin' and password == 'clientship2024':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return jsonify({'success': True, 'message': 'Login exitoso'})
        
        # También verificar en base de datos
        user = authenticate_user(username, password)
        if user and user.get('is_admin'):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return jsonify({'success': True, 'message': 'Login exitoso'})
        
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401
        
    except Exception as e:
        print(f"Error in admin login: {e}")
        return jsonify({'success': False, 'message': 'Error interno'}), 500

@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    """Logout de administrador"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return jsonify({'success': True, 'message': 'Logout exitoso'})

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas del dashboard"""
    try:
        stats = get_user_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': 'Error obteniendo estadísticas'}), 500

@admin_bp.route('/users', methods=['GET'])
def list_users():
    """Listar todos los usuarios"""
    try:
        users = get_all_users()
        return jsonify(users)
    except Exception as e:
        print(f"Error listing users: {e}")
        return jsonify({'error': 'Error obteniendo usuarios'}), 500

@admin_bp.route('/users', methods=['POST'])
def create_new_user():
    """Crear nuevo usuario"""
    try:
        data = request.get_json()
        
        company_name = data.get('company_name', '').strip()
        if not company_name:
            return jsonify({'error': 'El nombre de empresa es obligatorio'}), 400
        
        user = create_user(
            company_name=company_name,
            contact_person=data.get('contact_person', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            industry=data.get('industry', 'servicios'),
            company_size=data.get('company_size', 'startup'),
            notes=data.get('notes', '')
        )
        
        if user:
            return jsonify({
                'success': True,
                'message': 'Usuario creado exitosamente',
                'user': user
            })
        else:
            return jsonify({'error': 'Error creando usuario'}), 500
            
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({'error': 'Error interno'}), 500

@admin_bp.route('/users/<username>', methods=['DELETE'])
def delete_user_endpoint(username):
    """Eliminar usuario"""
    try:
        if delete_user(username):
            return jsonify({'success': True, 'message': 'Usuario eliminado'})
        else:
            return jsonify({'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'error': 'Error interno'}), 500

@admin_bp.route('/users/<username>/reset-password', methods=['POST'])
def reset_user_password(username):
    """Restablecer contraseña de usuario"""
    try:
        new_password = reset_password(username)
        if new_password:
            return jsonify({
                'success': True,
                'message': 'Contraseña restablecida',
                'new_password': new_password
            })
        else:
            return jsonify({'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        print(f"Error resetting password: {e}")
        return jsonify({'error': 'Error interno'}), 500

@admin_bp.route('/diagnostics', methods=['GET'])
def list_diagnostics():
    """Listar todos los diagnósticos"""
    try:
        diagnostics = get_all_diagnostics()
        return jsonify(diagnostics)
    except Exception as e:
        print(f"Error listing diagnostics: {e}")
        return jsonify({'error': 'Error obteniendo diagnósticos'}), 500

@admin_bp.route('/diagnostics/<int:diagnostic_id>', methods=['DELETE'])
def delete_diagnostic_endpoint(diagnostic_id):
    """Eliminar diagnóstico"""
    try:
        if delete_diagnostic(diagnostic_id):
            return jsonify({'success': True, 'message': 'Diagnóstico eliminado'})
        else:
            return jsonify({'error': 'Diagnóstico no encontrado'}), 404
    except Exception as e:
        print(f"Error deleting diagnostic: {e}")
        return jsonify({'error': 'Error interno'}), 500

@admin_bp.route('/recalculate-benchmark', methods=['POST'])
def recalculate_benchmark():
    """Recalcular estadísticas de benchmark"""
    try:
        # Por ahora solo retornamos éxito
        # En el futuro aquí se pueden hacer cálculos adicionales
        return jsonify({'success': True, 'message': 'Benchmark recalculado'})
    except Exception as e:
        print(f"Error recalculating benchmark: {e}")
        return jsonify({'error': 'Error interno'}), 500
