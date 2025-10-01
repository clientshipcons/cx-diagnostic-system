from flask import Blueprint, request, jsonify
from src.models.diagnostic import db, DiagnosticResult, BenchmarkStats
from datetime import datetime, date
import json
import statistics

diagnostic_bp = Blueprint('diagnostic', __name__)

@diagnostic_bp.route('/submit-diagnostic', methods=['POST'])
def submit_diagnostic():
    """Enviar un diagnóstico completado"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['companyInfo', 'responses', 'dimensionStats', 'overallScore', 'maturityLevel']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        company_info = data['companyInfo']
        responses = data['responses']
        dimension_stats = data['dimensionStats']
        overall_score = data['overallScore']
        maturity_level = data['maturityLevel']
        
        # Crear nuevo registro de diagnóstico
        diagnostic = DiagnosticResult(
            company_name=company_info.get('companyName', ''),
            industry=company_info.get('industry', ''),
            company_size=company_info.get('companySize', ''),
            responsible_name=company_info.get('responsibleName', ''),
            responsible_position=company_info.get('responsiblePosition', ''),
            responsible_email=company_info.get('responsibleEmail', ''),
            objectives=company_info.get('objectives', ''),
            diagnostic_date=datetime.strptime(company_info.get('date'), '%Y-%m-%d').date() if company_info.get('date') else date.today(),
            dimension_scores=json.dumps(dimension_stats),
            overall_score=overall_score,
            maturity_level=maturity_level,
            responses=json.dumps(responses),
            is_complete=True
        )
        
        db.session.add(diagnostic)
        db.session.commit()
        
        # Actualizar estadísticas de benchmarking
        update_benchmark_stats()
        
        return jsonify({
            'success': True,
            'message': 'Diagnóstico guardado exitosamente',
            'diagnostic_id': diagnostic.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/benchmark-stats', methods=['GET'])
def get_benchmark_stats():
    """Obtener estadísticas de benchmarking"""
    try:
        stats = BenchmarkStats.query.first()
        
        if not stats:
            # Si no hay estadísticas, calcularlas por primera vez
            update_benchmark_stats()
            stats = BenchmarkStats.query.first()
        
        if not stats:
            return jsonify({
                'total_diagnostics': 0,
                'dimension_averages': {},
                'dimension_minimums': {},
                'dimension_maximums': {},
                'overall_average': 0.0,
                'overall_minimum': 0.0,
                'overall_maximum': 0.0
            }), 200
        
        return jsonify(stats.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/benchmark-comparison/<int:diagnostic_id>', methods=['GET'])
def get_benchmark_comparison(diagnostic_id):
    """Obtener comparación de benchmarking para un diagnóstico específico"""
    try:
        diagnostic = DiagnosticResult.query.get_or_404(diagnostic_id)
        benchmark_stats = BenchmarkStats.query.first()
        
        if not benchmark_stats:
            return jsonify({'error': 'No hay datos de benchmarking disponibles'}), 404
        
        comparison = {
            'diagnostic': diagnostic.to_dict(),
            'benchmark': benchmark_stats.to_dict(),
            'comparison': {
                'overall_vs_average': diagnostic.overall_score - benchmark_stats.overall_average,
                'percentile_rank': calculate_percentile_rank(diagnostic.overall_score),
                'dimension_comparisons': {}
            }
        }
        
        # Comparar cada dimensión
        dimension_scores = json.loads(diagnostic.dimension_scores)
        dimension_averages = json.loads(benchmark_stats.dimension_averages) if benchmark_stats.dimension_averages else {}
        
        for dimension_id, score in dimension_scores.items():
            if dimension_id in dimension_averages:
                comparison['comparison']['dimension_comparisons'][dimension_id] = {
                    'score': score,
                    'average': dimension_averages[dimension_id],
                    'difference': score - dimension_averages[dimension_id]
                }
        
        return jsonify(comparison), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_benchmark_stats():
    """Actualizar estadísticas de benchmarking"""
    try:
        # Obtener todos los diagnósticos completos
        diagnostics = DiagnosticResult.query.filter_by(is_complete=True).all()
        
        if not diagnostics:
            return
        
        # Calcular estadísticas generales
        overall_scores = [d.overall_score for d in diagnostics]
        total_diagnostics = len(diagnostics)
        overall_average = statistics.mean(overall_scores)
        overall_minimum = min(overall_scores)
        overall_maximum = max(overall_scores)
        
        # Calcular estadísticas por dimensión
        dimension_data = {}
        for diagnostic in diagnostics:
            dimension_scores = json.loads(diagnostic.dimension_scores)
            for dim_id, score in dimension_scores.items():
                if dim_id not in dimension_data:
                    dimension_data[dim_id] = []
                dimension_data[dim_id].append(score)
        
        dimension_averages = {}
        dimension_minimums = {}
        dimension_maximums = {}
        
        for dim_id, scores in dimension_data.items():
            dimension_averages[dim_id] = statistics.mean(scores)
            dimension_minimums[dim_id] = min(scores)
            dimension_maximums[dim_id] = max(scores)
        
        # Calcular estadísticas por industria
        industry_stats = {}
        for diagnostic in diagnostics:
            industry = diagnostic.industry or 'No especificado'
            if industry not in industry_stats:
                industry_stats[industry] = []
            industry_stats[industry].append(diagnostic.overall_score)
        
        for industry, scores in industry_stats.items():
            industry_stats[industry] = {
                'count': len(scores),
                'average': statistics.mean(scores),
                'minimum': min(scores),
                'maximum': max(scores)
            }
        
        # Calcular estadísticas por tamaño de empresa
        company_size_stats = {}
        for diagnostic in diagnostics:
            size = diagnostic.company_size or 'No especificado'
            if size not in company_size_stats:
                company_size_stats[size] = []
            company_size_stats[size].append(diagnostic.overall_score)
        
        for size, scores in company_size_stats.items():
            company_size_stats[size] = {
                'count': len(scores),
                'average': statistics.mean(scores),
                'minimum': min(scores),
                'maximum': max(scores)
            }
        
        # Actualizar o crear registro de estadísticas
        stats = BenchmarkStats.query.first()
        if not stats:
            stats = BenchmarkStats()
            db.session.add(stats)
        
        stats.total_diagnostics = total_diagnostics
        stats.last_updated = datetime.utcnow()
        stats.dimension_averages = json.dumps(dimension_averages)
        stats.dimension_minimums = json.dumps(dimension_minimums)
        stats.dimension_maximums = json.dumps(dimension_maximums)
        stats.overall_average = overall_average
        stats.overall_minimum = overall_minimum
        stats.overall_maximum = overall_maximum
        stats.industry_stats = json.dumps(industry_stats)
        stats.company_size_stats = json.dumps(company_size_stats)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating benchmark stats: {e}")

def calculate_percentile_rank(score):
    """Calcular el percentil de una puntuación"""
    try:
        all_scores = [d.overall_score for d in DiagnosticResult.query.filter_by(is_complete=True).all()]
        if not all_scores:
            return 50  # Si no hay datos, devolver percentil 50
        
        scores_below = len([s for s in all_scores if s < score])
        percentile = (scores_below / len(all_scores)) * 100
        return round(percentile, 1)
        
    except Exception:
        return 50

@diagnostic_bp.route('/diagnostics', methods=['GET'])
def get_diagnostics():
    """Obtener lista de diagnósticos (para administración)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        diagnostics = DiagnosticResult.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'diagnostics': [d.to_anonymous_dict() for d in diagnostics.items],
            'total': diagnostics.total,
            'pages': diagnostics.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
