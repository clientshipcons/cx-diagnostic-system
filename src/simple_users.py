import json
import os
import random
from datetime import datetime

# Archivo para almacenar usuarios - usar ruta absoluta
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
DIAGNOSTICS_FILE = os.path.join(DATA_DIR, 'diagnostics.json')

def ensure_data_dir():
    """Asegurar que el directorio de datos existe"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"Data directory created/verified: {DATA_DIR}")
        return True
    except Exception as e:
        print(f"Error creating data directory: {e}")
        return False

def load_users():
    """Cargar usuarios desde archivo JSON"""
    ensure_data_dir()
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
                print(f"Loaded {len(users)} users from {USERS_FILE}")
                return users
        else:
            print(f"Users file not found, creating new: {USERS_FILE}")
            return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users(users):
    """Guardar usuarios en archivo JSON"""
    ensure_data_dir()
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(users)} users to {USERS_FILE}")
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def generate_username(company_name):
    """Generar nombre de usuario único"""
    # Limpiar nombre de empresa
    clean_name = ''.join(c.lower() for c in company_name if c.isalnum())[:6]
    if len(clean_name) < 3:
        clean_name = 'user'
    
    # Generar número único
    users = load_users()
    for _ in range(100):  # Máximo 100 intentos
        num = random.randint(100, 999)
        username = f"{clean_name}{num}"
        if username not in users:
            return username
    
    # Fallback con timestamp
    timestamp = str(int(datetime.now().timestamp()))[-4:]
    return f"{clean_name}{timestamp}"

def generate_password():
    """Generar contraseña simple"""
    return f"cx{random.randint(100, 999)}"

def create_user(company_name, contact_person='', email='', phone='', industry='servicios', company_size='startup', notes=''):
    """Crear un nuevo usuario"""
    try:
        users = load_users()
        
        # Generar credenciales únicas
        username = generate_username(company_name)
        password = generate_password()
        
        # Crear usuario
        user_data = {
            'username': username,
            'password': password,
            'company_name': company_name,
            'contact_person': contact_person,
            'email': email,
            'phone': phone,
            'industry': industry,
            'company_size': company_size,
            'notes': notes,
            'is_admin': False,
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        users[username] = user_data
        
        # Guardar en archivo
        if save_users(users):
            print(f"User created successfully: {username}")
            return user_data
        else:
            print(f"Failed to save user: {username}")
            return None
            
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def authenticate_user(username, password):
    """Autenticar usuario"""
    try:
        users = load_users()
        user = users.get(username)
        
        if user and user.get('password') == password and user.get('active', True):
            print(f"Authentication successful for: {username}")
            return user
        else:
            print(f"Authentication failed for: {username}")
            return None
            
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None

def get_all_users():
    """Obtener todos los usuarios"""
    try:
        users = load_users()
        return list(users.values())
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def delete_user(username):
    """Eliminar usuario"""
    try:
        users = load_users()
        if username in users:
            del users[username]
            if save_users(users):
                print(f"User deleted successfully: {username}")
                return True
        return False
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

def reset_password(username):
    """Restablecer contraseña de usuario"""
    try:
        users = load_users()
        if username in users:
            new_password = generate_password()
            users[username]['password'] = new_password
            if save_users(users):
                print(f"Password reset for user: {username}")
                return new_password
        return None
    except Exception as e:
        print(f"Error resetting password: {e}")
        return None

# Inicializar usuario admin al importar
def init_admin():
    """Inicializar usuario admin"""
    try:
        users = load_users()
        if 'admin' not in users:
            admin_user = {
                'username': 'admin',
                'password': 'clientship2024',
                'company_name': 'Clientship',
                'contact_person': 'Administrador',
                'email': 'admin@clientship.com',
                'phone': '',
                'industry': 'consultoria',
                'company_size': 'startup',
                'notes': 'Usuario administrador del sistema',
                'is_admin': True,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            users['admin'] = admin_user
            save_users(users)
            print("Admin user initialized")
    except Exception as e:
        print(f"Error initializing admin: {e}")

def get_user_stats():
    """Obtener estadísticas de usuarios"""
    try:
        users = load_users()
        total_users = len([u for u in users.values() if not u.get('is_admin', False)])
        active_users = len([u for u in users.values() if u.get('active', True) and not u.get('is_admin', False)])
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_diagnostics': 0,  # Por ahora
            'completion_rate': 0     # Por ahora
        }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'total_diagnostics': 0,
            'completion_rate': 0
        }

# Inicializar admin al importar el módulo
init_admin()
