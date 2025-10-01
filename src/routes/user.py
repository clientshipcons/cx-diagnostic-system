from flask import Blueprint, request, jsonify, session
from src.models.user_real import User, db
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username y password requeridos'}), 400
    
    # Buscar usuario en la base de datos
    user = User.query.filter_by(username=username, is_active=True).first()
    
    if user and user.password == password:
        # Actualizar último login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Guardar en sesión
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'company': user.company_name or 'Sin empresa',
                'name': user.contact_person or user.username
            }
        })
    
    # Fallback para usuario demo (mantener compatibilidad)
    if username == 'demo' and password == 'demo123':
        session['user_id'] = 'demo'
        session['username'] = 'demo'
        return jsonify({
            'success': True,
            'user': {
                'id': 'demo',
                'username': 'demo',
                'company': 'Clientship Demo',
                'name': 'Usuario Demo'
            }
        })
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@user_bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    user_id = session['user_id']
    
    # Usuario demo
    if user_id == 'demo':
        return jsonify({
            'user': {
                'id': 'demo',
                'username': 'demo',
                'company': 'Clientship Demo',
                'name': 'Usuario Demo'
            }
        })
    
    # Usuario real
    from src.models.user_real import User as RealUser
    user = RealUser.query.get(user_id)
    
    if user and user.is_active:
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'company': user.company_name or 'Sin empresa',
                'name': user.contact_person or user.username
            }
        })
    
    return jsonify({'error': 'Usuario no encontrado'}), 404

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    
    data = request.json
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
