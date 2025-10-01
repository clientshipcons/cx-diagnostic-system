import sqlite3
import os
import json
import random
from datetime import datetime
from contextlib import contextmanager

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

def init_database():
    """Inicializar la base de datos con las tablas necesarias"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    contact_person TEXT,
                    email TEXT,
                    phone TEXT,
                    industry TEXT DEFAULT 'servicios',
                    company_size TEXT DEFAULT 'startup',
                    notes TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de diagnósticos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS diagnostics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    company_name TEXT NOT NULL,
                    contact_person TEXT,
                    email TEXT,
                    industry TEXT,
                    company_size TEXT,
                    responses TEXT NOT NULL,
                    scores TEXT NOT NULL,
                    overall_score REAL,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            print(f"Database initialized at: {DB_PATH}")
            
            # Crear usuario admin si no existe
            create_admin_user()
            
    except Exception as e:
        print(f"Error initializing database: {e}")

def create_admin_user():
    """Crear usuario administrador si no existe"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Verificar si admin existe
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            if cursor.fetchone() is None:
                cursor.execute('''
                    INSERT INTO users (username, password, company_name, contact_person, 
                                     email, industry, company_size, notes, is_admin, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', ('admin', 'clientship2024', 'Clientship', 'Administrador',
                      'admin@clientship.com', 'consultoria', 'startup',
                      'Usuario administrador del sistema', 1, 1))
                conn.commit()
                print("Admin user created")
                
    except Exception as e:
        print(f"Error creating admin user: {e}")

@contextmanager
def get_db_connection():
    """Context manager para conexiones a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    try:
        yield conn
    finally:
        conn.close()

def generate_username(company_name):
    """Generar nombre de usuario único"""
    # Limpiar nombre de empresa
    clean_name = ''.join(c.lower() for c in company_name if c.isalnum())[:6]
    if len(clean_name) < 3:
        clean_name = 'user'
    
    # Generar número único
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for _ in range(100):  # Máximo 100 intentos
            num = random.randint(100, 999)
            username = f"{clean_name}{num}"
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone() is None:
                return username
    
    # Fallback con timestamp
    timestamp = str(int(datetime.now().timestamp()))[-4:]
    return f"{clean_name}{timestamp}"

def generate_password():
    """Generar contraseña simple"""
    return f"cx{random.randint(100, 999)}"

def create_user(company_name, contact_person='', email='', phone='', 
                industry='servicios', company_size='startup', notes=''):
    """Crear un nuevo usuario"""
    try:
        username = generate_username(company_name)
        password = generate_password()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, company_name, contact_person,
                                 email, phone, industry, company_size, notes, is_admin, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, company_name, contact_person, email, phone,
                  industry, company_size, notes, 0, 1))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            print(f"User created successfully: {username}")
            return {
                'id': user_id,
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
                'active': True,
                'created_at': datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def authenticate_user(username, password):
    """Autenticar usuario"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE username = ? AND password = ? AND active = 1
            ''', (username, password))
            
            row = cursor.fetchone()
            if row:
                user = dict(row)
                user['is_admin'] = bool(user['is_admin'])
                user['active'] = bool(user['active'])
                print(f"Authentication successful for: {username}")
                return user
            else:
                print(f"Authentication failed for: {username}")
                return None
                
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None

def get_all_users():
    """Obtener todos los usuarios (excepto admin)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE is_admin = 0 ORDER BY created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                user = dict(row)
                user['is_admin'] = bool(user['is_admin'])
                user['active'] = bool(user['active'])
                users.append(user)
            
            return users
            
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def delete_user(username):
    """Eliminar usuario"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ? AND is_admin = 0", (username,))
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"User deleted successfully: {username}")
                return True
            return False
            
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

def reset_password(username):
    """Restablecer contraseña de usuario"""
    try:
        new_password = generate_password()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET password = ? 
                WHERE username = ? AND is_admin = 0
            ''', (new_password, username))
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"Password reset for user: {username}")
                return new_password
            return None
            
    except Exception as e:
        print(f"Error resetting password: {e}")
        return None

def save_diagnostic(user_id, company_name, contact_person, email, industry, 
                   company_size, responses, scores, overall_score):
    """Guardar resultado de diagnóstico"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO diagnostics (user_id, company_name, contact_person, email,
                                       industry, company_size, responses, scores, overall_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, company_name, contact_person, email, industry, company_size,
                  json.dumps(responses), json.dumps(scores), overall_score))
            
            diagnostic_id = cursor.lastrowid
            conn.commit()
            
            print(f"Diagnostic saved successfully: {diagnostic_id}")
            return diagnostic_id
            
    except Exception as e:
        print(f"Error saving diagnostic: {e}")
        return None

def get_all_diagnostics():
    """Obtener todos los diagnósticos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM diagnostics ORDER BY completed_at DESC
            ''')
            
            diagnostics = []
            for row in cursor.fetchall():
                diagnostic = dict(row)
                diagnostic['responses'] = json.loads(diagnostic['responses'])
                diagnostic['scores'] = json.loads(diagnostic['scores'])
                diagnostics.append(diagnostic)
            
            return diagnostics
            
    except Exception as e:
        print(f"Error getting diagnostics: {e}")
        return []

def delete_diagnostic(diagnostic_id):
    """Eliminar diagnóstico"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM diagnostics WHERE id = ?", (diagnostic_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"Diagnostic deleted successfully: {diagnostic_id}")
                return True
            return False
            
    except Exception as e:
        print(f"Error deleting diagnostic: {e}")
        return False

def get_benchmark_stats():
    """Obtener estadísticas para benchmarking"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT scores, overall_score FROM diagnostics 
                WHERE overall_score IS NOT NULL
            ''')
            
            all_scores = []
            dimension_scores = {f'dimension_{i}': [] for i in range(1, 7)}
            
            for row in cursor.fetchall():
                overall_score = row['overall_score']
                all_scores.append(overall_score)
                
                try:
                    scores = json.loads(row['scores'])
                    for i in range(1, 7):
                        dim_key = f'dimension_{i}'
                        if dim_key in scores:
                            dimension_scores[dim_key].append(scores[dim_key])
                except:
                    continue
            
            if not all_scores:
                return None
            
            # Calcular estadísticas
            stats = {
                'overall': {
                    'average': sum(all_scores) / len(all_scores),
                    'min': min(all_scores),
                    'max': max(all_scores),
                    'count': len(all_scores)
                },
                'dimensions': {}
            }
            
            for dim, scores in dimension_scores.items():
                if scores:
                    stats['dimensions'][dim] = {
                        'average': sum(scores) / len(scores),
                        'min': min(scores),
                        'max': max(scores),
                        'count': len(scores)
                    }
            
            return stats
            
    except Exception as e:
        print(f"Error getting benchmark stats: {e}")
        return None

def get_user_stats():
    """Obtener estadísticas de usuarios"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total usuarios (sin admin)
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
            total_users = cursor.fetchone()[0]
            
            # Usuarios activos
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0 AND active = 1")
            active_users = cursor.fetchone()[0]
            
            # Total diagnósticos
            cursor.execute("SELECT COUNT(*) FROM diagnostics")
            total_diagnostics = cursor.fetchone()[0]
            
            # Tasa de completitud (diagnósticos / usuarios)
            completion_rate = (total_diagnostics / total_users * 100) if total_users > 0 else 0
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_diagnostics': total_diagnostics,
                'completion_rate': round(completion_rate, 1)
            }
            
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'total_diagnostics': 0,
            'completion_rate': 0
        }

# Inicializar la base de datos al importar el módulo
init_database()
