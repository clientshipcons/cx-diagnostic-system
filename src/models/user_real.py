from src.models.user import db
from datetime import datetime
import secrets
import string

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    company_name = db.Column(db.String(200), nullable=True)
    contact_person = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    company_size = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relación con diagnósticos (comentada para evitar problemas de FK)
    # diagnostics = db.relationship('DiagnosticResult', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'company_name': self.company_name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'industry': self.industry,
            'company_size': self.company_size,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'diagnostic_count': 0  # Simplificado para evitar problemas de FK
        }
    
    @staticmethod
    def generate_password(length=8):
        """Generar contraseña aleatoria segura"""
        characters = string.ascii_letters + string.digits
        # Asegurar que tenga al menos una mayúscula, una minúscula y un número
        password = (
            secrets.choice(string.ascii_uppercase) +
            secrets.choice(string.ascii_lowercase) +
            secrets.choice(string.digits) +
            ''.join(secrets.choice(characters) for _ in range(length - 3))
        )
        # Mezclar los caracteres
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        return ''.join(password_list)
    
    @staticmethod
    def generate_username(company_name):
        """Generar username basado en el nombre de la empresa"""
        if not company_name:
            return f"user_{secrets.token_hex(4)}"
        
        # Limpiar el nombre de la empresa
        clean_name = ''.join(c.lower() for c in company_name if c.isalnum())
        if len(clean_name) > 15:
            clean_name = clean_name[:15]
        
        # Agregar sufijo aleatorio para evitar duplicados
        suffix = secrets.token_hex(2)
        return f"{clean_name}_{suffix}"

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<AdminUser {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }
