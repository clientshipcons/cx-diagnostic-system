#!/usr/bin/env python3
"""
Script de migración para agregar ON DELETE CASCADE a la restricción de clave foránea
entre diagnostics y users.

Esto permitirá que cuando se elimine un usuario, automáticamente se eliminen
todos sus diagnósticos asociados.
"""

import os
import sys
from sqlalchemy import create_engine, text

def migrate_database():
    """Modifica la restricción de clave foránea para agregar ON DELETE CASCADE"""
    
    # Obtener DATABASE_URL del entorno
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("Error: DATABASE_URL no está definida en las variables de entorno")
        sys.exit(1)
    
    print(f"Conectando a la base de datos...")
    
    try:
        # Crear engine de SQLAlchemy
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("Conexión exitosa")
            
            # Paso 1: Eliminar la restricción existente
            print("\n1. Eliminando restricción de clave foránea existente...")
            conn.execute(text("""
                ALTER TABLE diagnostics 
                DROP CONSTRAINT IF EXISTS diagnostics_user_id_fkey;
            """))
            conn.commit()
            print("   ✓ Restricción eliminada")
            
            # Paso 2: Agregar la nueva restricción con ON DELETE CASCADE
            print("\n2. Agregando nueva restricción con ON DELETE CASCADE...")
            conn.execute(text("""
                ALTER TABLE diagnostics 
                ADD CONSTRAINT diagnostics_user_id_fkey 
                FOREIGN KEY (user_id) 
                REFERENCES users(id) 
                ON DELETE CASCADE;
            """))
            conn.commit()
            print("   ✓ Restricción agregada con ON DELETE CASCADE")
            
            # Paso 3: Verificar que la restricción se creó correctamente
            print("\n3. Verificando la nueva restricción...")
            result = conn.execute(text("""
                SELECT 
                    conname AS constraint_name,
                    confdeltype AS delete_action
                FROM pg_constraint
                WHERE conname = 'diagnostics_user_id_fkey';
            """))
            
            row = result.fetchone()
            if row and row[1] == 'c':  # 'c' significa CASCADE
                print("   ✓ Restricción verificada correctamente")
                print(f"   - Nombre: {row[0]}")
                print(f"   - Acción al eliminar: CASCADE")
            else:
                print("   ⚠ No se pudo verificar la restricción")
            
        print("\n✅ Migración completada exitosamente")
        print("\nAhora puedes eliminar usuarios desde el panel de administración")
        print("y sus diagnósticos se eliminarán automáticamente.")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()
