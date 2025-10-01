from src.models.user import db
from datetime import datetime
import json

class DiagnosticResult(db.Model):
    __tablename__ = 'diagnostic_results'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Información de la empresa (anonimizada para benchmarking)
    company_name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))
    responsible_name = db.Column(db.String(255))
    responsible_position = db.Column(db.String(255))
    responsible_email = db.Column(db.String(255))
    objectives = db.Column(db.Text)
    
    # Metadatos del diagnóstico
    diagnostic_date = db.Column(db.Date, nullable=False)
    completion_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Resultados por dimensión (JSON)
    dimension_scores = db.Column(db.Text, nullable=False)  # JSON con puntuaciones por dimensión
    
    # Puntuación general
    overall_score = db.Column(db.Float, nullable=False)
    maturity_level = db.Column(db.String(100), nullable=False)
    
    # Respuestas completas (JSON)
    responses = db.Column(db.Text, nullable=False)  # JSON con todas las respuestas
    
    # Flags para análisis
    is_complete = db.Column(db.Boolean, default=True)
    is_anonymous = db.Column(db.Boolean, default=False)  # Para benchmarking anónimo
    
    def __init__(self, **kwargs):
        super(DiagnosticResult, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'industry': self.industry,
            'company_size': self.company_size,
            'responsible_name': self.responsible_name,
            'responsible_position': self.responsible_position,
            'responsible_email': self.responsible_email,
            'objectives': self.objectives,
            'diagnostic_date': self.diagnostic_date.isoformat() if self.diagnostic_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'dimension_scores': json.loads(self.dimension_scores) if self.dimension_scores else {},
            'overall_score': self.overall_score,
            'maturity_level': self.maturity_level,
            'responses': json.loads(self.responses) if self.responses else {},
            'is_complete': self.is_complete,
            'is_anonymous': self.is_anonymous
        }
    
    def to_anonymous_dict(self):
        """Versión anonimizada para benchmarking"""
        return {
            'id': self.id,
            'industry': self.industry,
            'company_size': self.company_size,
            'diagnostic_date': self.diagnostic_date.isoformat() if self.diagnostic_date else None,
            'dimension_scores': json.loads(self.dimension_scores) if self.dimension_scores else {},
            'overall_score': self.overall_score,
            'maturity_level': self.maturity_level,
            'is_complete': self.is_complete
        }

class BenchmarkStats(db.Model):
    __tablename__ = 'benchmark_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Estadísticas generales
    total_diagnostics = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Promedios por dimensión (JSON)
    dimension_averages = db.Column(db.Text)  # JSON con promedios
    dimension_minimums = db.Column(db.Text)  # JSON con mínimos
    dimension_maximums = db.Column(db.Text)  # JSON con máximos
    
    # Promedio general
    overall_average = db.Column(db.Float, default=0.0)
    overall_minimum = db.Column(db.Float, default=0.0)
    overall_maximum = db.Column(db.Float, default=0.0)
    
    # Estadísticas por industria (JSON)
    industry_stats = db.Column(db.Text)
    
    # Estadísticas por tamaño de empresa (JSON)
    company_size_stats = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'total_diagnostics': self.total_diagnostics,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'dimension_averages': json.loads(self.dimension_averages) if self.dimension_averages else {},
            'dimension_minimums': json.loads(self.dimension_minimums) if self.dimension_minimums else {},
            'dimension_maximums': json.loads(self.dimension_maximums) if self.dimension_maximums else {},
            'overall_average': self.overall_average,
            'overall_minimum': self.overall_minimum,
            'overall_maximum': self.overall_maximum,
            'industry_stats': json.loads(self.industry_stats) if self.industry_stats else {},
            'company_size_stats': json.loads(self.company_size_stats) if self.company_size_stats else {}
        }
