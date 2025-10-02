import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import random
import string

# PostgreSQL connection string (using pooler with channel_binding)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Clientship2024!CX#Diagnostic@db.sgjgvfbzrhcifqflfyln.supabase.co:5432/postgres')

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
    """Save a diagnostic result"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
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
