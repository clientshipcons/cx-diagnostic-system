from flask import Flask, send_from_directory, session
from flask_cors import CORS
import os
from datetime import timedelta

# Importar las rutas simplificadas
from src.routes.simple_admin import simple_admin_bp
from src.routes.simple_user import simple_user_bp

def create_app():
    app = Flask(__name__, static_folder='static')
    
    # Configuración
    app.config['SECRET_KEY'] = 'clientship-cx-diagnostic-2024-super-secret-key'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # CORS
    CORS(app, supports_credentials=True, origins=['*'])
    
    # Registrar blueprints
    app.register_blueprint(simple_admin_bp, url_prefix='/api/admin')
    app.register_blueprint(simple_user_bp, url_prefix='/api/user')
    
    # Ruta para servir archivos estáticos
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        if path.startswith('api/'):
            return {'error': 'API endpoint not found'}, 404
        
        # Intentar servir el archivo
        try:
            return send_from_directory(app.static_folder, path)
        except:
            # Si no existe, servir index.html para SPA routing
            return send_from_directory(app.static_folder, 'index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
