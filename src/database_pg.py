import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import random
import string

# PostgreSQL connection string from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

def get_connection():
    """Get a PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initialize the database with tables and admin user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            company_name VARCHAR(200) NOT NULL,
            contact_person VARCHAR(200),
            email VARCHAR(200),
            phone VARCHAR(50),
            industry VARCHAR(100),
            company_size VARCHAR(50),
            notes TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create diagnostics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnostics (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            responses JSONB,
            score FLOAT,
            level VARCHAR(50),
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if admin user exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # Create admin user
        cursor.execute('''
            INSERT INTO users (username, password, company_name, is_admin, is_active)
            VALUES (%s, %s, %s, %s, %s)
        ''', ('admin', 'clientship2024', 'Clientship', True, True))
    
    conn.commit()
    cursor.close()
    conn.close()

def authenticate_user(username, password):
    """Authenticate a user"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT id, username, company_name, is_admin, is_active
        FROM users
        WHERE username = %s AND password = %s
    ''', (username, password))
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        return dict(user)
    return None

def generate_username(company_name):
    """Generate a unique username from company name"""
    # Take first 6 letters of company name, remove spaces and special chars
    base = ''.join(c for c in company_name.lower() if c.isalnum())[:6]
    if not base:
        base = 'empres'
    
    # Add 3 random digits
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"{base}{suffix}"

def generate_password():
    """Generate a random password"""
    return 'cx' + ''.join(random.choices(string.digits, k=3))

def create_user(company_name, contact_person, email, phone, industry, company_size, notes=''):
    """Create a new user"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Generate unique username
    username = generate_username(company_name)
    password = generate_password()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password, company_name, contact_person, email, phone, industry, company_size, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (username, password, company_name, contact_person, email, phone, industry, company_size, notes))
        
        user_id = cursor.fetchone()['id']
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'username': username,
            'password': password,
            'user_id': user_id
        }
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return {
            'success': False,
            'error': str(e)
        }

def get_all_users():
    """Get all users"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT id, username, company_name, contact_person, email, phone, industry, company_size, is_active, created_at
        FROM users
        WHERE is_admin = FALSE
        ORDER BY created_at DESC
    ''')
    
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(user) for user in users]

def get_all_diagnostics():
    """Get all diagnostics with user information"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT d.id, d.score, d.level, d.completed_at,
               u.username, u.company_name
        FROM diagnostics d
        JOIN users u ON d.user_id = u.id
        ORDER BY d.completed_at DESC
    ''')
    
    diagnostics = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(diag) for diag in diagnostics]

def get_stats():
    """Get dashboard statistics"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Count users (excluding admin)
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_admin = FALSE")
    total_users = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as active FROM users WHERE is_admin = FALSE AND is_active = TRUE")
    active_users = cursor.fetchone()['active']
    
    # Count diagnostics
    cursor.execute("SELECT COUNT(*) as total FROM diagnostics")
    total_diagnostics = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as completed FROM diagnostics WHERE score IS NOT NULL")
    completed_diagnostics = cursor.fetchone()['completed']
    
    cursor.close()
    conn.close()
    
    completion_rate = 0
    if total_diagnostics > 0:
        completion_rate = (completed_diagnostics / total_diagnostics) * 100
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'total_diagnostics': total_diagnostics,
        'completion_rate': round(completion_rate, 1)
    }

def save_diagnostic(user_id, responses, score, level):
    """Save or update a diagnostic result"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if diagnostic exists for this user
        cursor.execute('SELECT id FROM diagnostics WHERE user_id = %s', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing diagnostic
            cursor.execute('''
                UPDATE diagnostics 
                SET responses = %s, score = %s, level = %s, completed_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            ''', (psycopg2.extras.Json(responses), score, level, user_id))
        else:
            # Insert new diagnostic
            cursor.execute('''
                INSERT INTO diagnostics (user_id, responses, score, level)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, psycopg2.extras.Json(responses), score, level))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Error saving diagnostic: {e}")
        return False

# Initialize database on import
init_db()

def delete_user(username):
    """Delete a user by username"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM users WHERE username = %s AND is_admin = FALSE', (username,))
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return deleted
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Error deleting user: {e}")
        return False

def reset_password(username):
    """Reset user password"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        new_password = generate_password()
        cursor.execute('UPDATE users SET password = %s WHERE username = %s AND is_admin = FALSE', (new_password, username))
        updated = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return new_password if updated else None
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Error resetting password: {e}")
        return None

def delete_diagnostic(diagnostic_id):
    """Delete a diagnostic by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM diagnostics WHERE id = %s', (diagnostic_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return deleted
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Error deleting diagnostic: {e}")
        return False

def calculate_benchmark():
    """Calculate benchmark statistics from all completed diagnostics"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all completed diagnostics with their dimension scores
        cursor.execute('''
            SELECT responses
            FROM diagnostics
            WHERE responses IS NOT NULL
        ''')
        
        diagnostics = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not diagnostics:
            return {
                'total_diagnostics': 0,
                'dimensions': {}
            }
        
        # Calculate average scores per dimension
        dimension_scores = {}
        dimension_counts = {}
        
        for diag in diagnostics:
            responses = diag['responses']
            if isinstance(responses, dict) and 'dimensions' in responses:
                for dim_name, dim_data in responses['dimensions'].items():
                    if 'score' in dim_data:
                        if dim_name not in dimension_scores:
                            dimension_scores[dim_name] = 0
                            dimension_counts[dim_name] = 0
                        dimension_scores[dim_name] += dim_data['score']
                        dimension_counts[dim_name] += 1
        
        # Calculate averages
        benchmark = {
            'total_diagnostics': len(diagnostics),
            'dimensions': {}
        }
        
        for dim_name in dimension_scores:
            if dimension_counts[dim_name] > 0:
                avg_score = dimension_scores[dim_name] / dimension_counts[dim_name]
                benchmark['dimensions'][dim_name] = round(avg_score, 2)
        
        return benchmark
        
    except Exception as e:
        cursor.close()
        conn.close()
        print(f"Error calculating benchmark: {e}")
        return {
            'total_diagnostics': 0,
            'dimensions': {},
            'error': str(e)
        }

def get_user_diagnostic(user_id):
    """Get the most recent diagnostic for a user"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT id, responses, score, level, completed_at
        FROM diagnostics
        WHERE user_id = %s
        ORDER BY completed_at DESC
        LIMIT 1
    ''', (user_id,))
    
    diagnostic = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if diagnostic:
        return dict(diagnostic)
    return None

def get_benchmark_stats():
    """Get benchmark statistics from benchmark_stats table"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all benchmark stats
        cursor.execute('''
            SELECT dimension, avg_score, total_diagnostics
            FROM benchmark_stats
            ORDER BY dimension
        ''')
        
        stats = cursor.fetchall()
        
        # Get total diagnostics count
        cursor.execute('SELECT COUNT(*) as total FROM diagnostics WHERE responses IS NOT NULL')
        total = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        # Format response
        dimensions = []
        for stat in stats:
            dimensions.append({
                'dimension': stat['dimension'],
                'avg_score': float(stat['avg_score'])
            })
        
        return {
            'dimensiones': dimensions,
            'total_diagnostics': total
        }
        
    except Exception as e:
        cursor.close()
        conn.close()
        print(f"Error getting benchmark stats: {e}")
        return {
            'dimensiones': [],
            'total_diagnostics': 0
        }


# ==================== BENCHMARK RECALCULATION ====================

from collections import defaultdict

# Mapeo de preguntas a dimensiones
DIMENSION_MAPPING = {
    '1': 'estrategia_cx',
    '2': 'arquitectura_cx',
    '3': 'insights_cx',
    '4': 'cultura_cambio',
    '5': 'innovacion_cx',
    '6': 'governance_cx'
}

def extract_dimension_from_key(key):
    """Extraer el número de dimensión de una clave como '1.1.1' -> '1'"""
    if isinstance(key, str) and '.' in key:
        return key.split('.')[0]
    return None

def recalculate_benchmark_stats():
    """Recalcular estadísticas de benchmarking desde las respuestas reales"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Obtener todos los diagnósticos completos
        cursor.execute("""
            SELECT id, user_id, responses
            FROM diagnostics
            WHERE responses IS NOT NULL
        """)
        
        diagnostics = cursor.fetchall()
        
        if not diagnostics:
            cursor.close()
            conn.close()
            return {
                'success': False,
                'message': 'No hay diagnósticos para calcular benchmark'
            }
        
        # Calcular promedios por dimensión
        dimension_scores = defaultdict(list)
        
        for diag in diagnostics:
            responses = diag['responses']
            
            # Agrupar respuestas por dimensión
            dimension_responses = defaultdict(list)
            
            for key, value in responses.items():
                dim_id = extract_dimension_from_key(key)
                if dim_id and dim_id in DIMENSION_MAPPING:
                    dimension_responses[dim_id].append(value)
            
            # Calcular promedio por dimensión para este diagnóstico
            for dim_id, values in dimension_responses.items():
                if values:
                    avg = sum(values) / len(values)
                    dimension_scores[DIMENSION_MAPPING[dim_id]].append(avg)
        
        # Actualizar benchmark_stats
        for dim_name, scores in dimension_scores.items():
            if scores:
                global_avg = sum(scores) / len(scores)
                
                # Primero intentar actualizar
                cursor.execute("""
                    UPDATE benchmark_stats 
                    SET avg_score = %s, total_diagnostics = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE dimension = %s
                """, (global_avg, len(scores), dim_name))
                
                # Si no se actualizó ninguna fila, insertar
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO benchmark_stats (dimension, avg_score, total_diagnostics, updated_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """, (dim_name, global_avg, len(scores)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'Benchmark recalculado con {len(diagnostics)} diagnósticos',
            'total_diagnostics': len(diagnostics),
            'dimensions_updated': len(dimension_scores)
        }
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Error recalculando benchmark: {e}")
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }
