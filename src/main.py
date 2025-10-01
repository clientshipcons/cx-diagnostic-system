from flask import Flask, send_from_directory, session
import os
from datetime import timedelta

# Importar rutas
from .routes.admin_sqlite import admin_bp
from .routes.user_sqlite import user_bp

# Importar inicialización de base de datos
from .database import init_database

def create_app():
    app = Flask(__name__)
    
    # Configuración de la aplicación
    app.config['SECRET_KEY'] = 'clientship-cx-diagnostic-2024-secret-key-very-secure'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Inicializar base de datos
    init_database()
    
    # Registrar blueprints
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    
    # Servir archivos estáticos del frontend
    @app.route('/')
    def serve_index():
        return send_from_directory('static', 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        try:
            return send_from_directory('static', path)
        except:
            # Si el archivo no existe, servir index.html (para SPA routing)
            return send_from_directory('static', 'index.html')
    
    # Ruta de salud
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'database': 'sqlite'}
    
    return app

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
