"""
EduPredict Pro - Flask Application
AI Degree Program Planning & Decision Intelligence Tool

No Streamlit. Pure Flask + HTML/CSS/JS.
Hosted on AWS EC2 with Gunicorn.
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import sys
import secrets
from io import BytesIO
from datetime import datetime


# Add models to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.forecasting import ForecastInput, EnrollmentForecaster, quick_forecast
from models.roi_calculator import ROIInput, ROICalculator, quick_roi
from models.job_market import JobMarketAnalyzer, quick_ai_report, AIOccupationDatabase

# PDF generation
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    print("Warning: FPDF not available. PDF export disabled.")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edupredict.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'

# Database Models
class User(UserMixin, db.Model):
    """User model for authentication."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ForecastHistory(db.Model):
    """Store forecast history for audit trail."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    program = db.Column(db.String(50), nullable=False)
    student_type = db.Column(db.String(20), nullable=False)
    term = db.Column(db.String(10), nullable=False)
    scenario = db.Column(db.String(20), nullable=False)
    state = db.Column(db.String(5), nullable=False)
    year1_enrollment = db.Column(db.Integer)
    projected_pool = db.Column(db.Integer)
    roi_ratio = db.Column(db.Float)
    confidence = db.Column(db.Float)
    recommendation = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='forecasts')

class ActivityLog(db.Model):
    """General activity logging."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activities')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize models
forecaster = EnrollmentForecaster()
roi_calc = ROICalculator()
job_analyzer = JobMarketAnalyzer()
ai_db = AIOccupationDatabase()

# Configuration
PROGRAMS = ["MS in AI", "BS in AI", "AI in Cybersecurity"]
STUDENT_TYPES = ["International", "Domestic"]
TERMS = ["SP26", "SU26", "FA26", "SP27", "SU27", "FA27", "SP28", "SU28", "FA28"]
SCENARIOS = ["Baseline", "Optimistic", "Conservative"]
STATES = ["CT", "NY", "MA"]


# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log activity
            log_activity(user.id, 'login', f'User logged in from {request.remote_addr}')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    log_activity(current_user.id, 'logout', 'User logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# Helper function for logging
def log_activity(user_id, action, details=None):
    """Log user activity."""
    try:
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except:
        db.session.rollback()


# Main Application Routes
@app.route('/')
@login_required
def index():
    """Main dashboard page."""
    return render_template('index.html',
                         programs=PROGRAMS,
                         student_types=STUDENT_TYPES,
                         terms=TERMS,
                         scenarios=SCENARIOS,
                         states=STATES)


@app.route('/api/forecast', methods=['POST'])
@login_required
def api_forecast():
    """API endpoint for enrollment forecast."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    term = data.get('term', 'FA26')
    scenario = data.get('scenario', 'Baseline')
    state = data.get('state', 'CT')
    
    # Get forecast
    forecast = quick_forecast(program, student_type, term, scenario, state)
    
    # Get ROI
    roi = quick_roi(program, state,
                   forecast.year1_enrollment,
                   forecast.year2_enrollment,
                   forecast.year3_enrollment,
                   student_type)
    
    # Get job market data
    job_signal = job_analyzer.get_signal(state, program)
    ai_exposure = ai_db.get_program_exposure(program)
    
    # Get recommendation
    rec = job_analyzer.get_program_recommendation(state, program)
    
    # Calculate overall recommendation
    if roi.roi_ratio >= 1.5 and forecast.confidence_score >= 0.75:
        recommendation = "STRONG GO"
        rec_class = "strong-go"
    elif roi.roi_ratio >= 1.0 and forecast.confidence_score >= 0.60:
        recommendation = "GO"
        rec_class = "go"
    elif roi.roi_ratio >= 0.7 or forecast.confidence_score >= 0.50:
        recommendation = "CONDITIONAL"
        rec_class = "conditional"
    else:
        recommendation = "RECONSIDER"
        rec_class = "reconsider"
    
    if roi.launch_recommendation == "delay":
        recommendation = "DO NOT LAUNCH"
        rec_class = "do-not-launch"
    
    # Log forecast to database
    try:
        history = ForecastHistory(
            user_id=current_user.id,
            program=program,
            student_type=student_type,
            term=term,
            scenario=scenario,
            state=state,
            year1_enrollment=forecast.year1_enrollment,
            projected_pool=forecast.projected_pool,
            roi_ratio=roi.roi_ratio,
            confidence=forecast.confidence_score,
            recommendation=recommendation
        )
        db.session.add(history)
        db.session.commit()
        
        # Log activity
        log_activity(current_user.id, 'forecast', 
                    f'{program} for {state} - {recommendation} (ROI: {roi.roi_ratio}x)')
    except:
        db.session.rollback()
    
    return jsonify({
        'success': True,
        'forecast': {
            'year1': forecast.year1_enrollment,
            'year2': forecast.year2_enrollment,
            'year3': forecast.year3_enrollment,
            'year1_low': forecast.year1_low,
            'year1_high': forecast.year1_high,
            'pool': forecast.projected_pool,
            'confidence': forecast.confidence_score,
            'confidence_pct': int(forecast.confidence_score * 100),
            'risk_level': forecast.risk_level,
            'recommendation_confidence': forecast.recommendation_confidence,
            'warning_flags': forecast.warning_flags
        },
        'roi': {
            'ratio': roi.roi_ratio,
            'starting_salary': roi.starting_salary,
            'salary_5year': roi.salary_5year,
            'revenue': roi.total_tuition_revenue,
            'costs': roi.program_cost_estimate,
            'payback_years': roi.payback_period_years,
            'break_even': roi.break_even_enrollment,
            'financial_warnings': roi.financial_warnings
        },
        'job_market': {
            'growth_rate': job_signal.job_growth_rate,
            'open_positions': job_signal.open_positions_estimate,
            'demand_level': job_signal.demand_level,
            'demand_score': job_analyzer.get_demand_score(state, program),
            'ai_exposure': ai_exposure.observed_exposure,
            'ai_exposure_pct': int(ai_exposure.observed_exposure * 100),
            'risk_level': ai_exposure.risk_level.value,
            'coverage_gap': ai_exposure.coverage_gap,
            'bls_impact': ai_exposure.bls_growth_projection_2034,
            'young_worker_impact': ai_exposure.young_worker_hiring_impact,
            'key_finding': ai_exposure.key_finding
        },
        'recommendation': {
            'text': recommendation,
            'class': rec_class,
            'demand_score': rec['demand_score'],
            'rationale': rec['rationale'],
            'warnings': rec['warnings'],
            'opportunities': rec['opportunities']
        },
        'inputs': {
            'program': program,
            'student_type': student_type,
            'term': term,
            'scenario': scenario,
            'state': state
        }
    })


@app.route('/api/scenarios', methods=['POST'])
@login_required
def api_scenarios():
    """Get all scenario comparisons."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    term = data.get('term', 'FA26')
    state = data.get('state', 'CT')
    
    scenarios_data = []
    for scen in SCENARIOS:
        forecast = quick_forecast(program, student_type, term, scen, state)
        scenarios_data.append({
            'scenario': scen,
            'year1': forecast.year1_enrollment,
            'pool': forecast.projected_pool,
            'confidence': forecast.confidence_score
        })
    
    return jsonify({'scenarios': scenarios_data})


@app.route('/api/states', methods=['POST'])
@login_required
def api_states():
    """Get state comparison data."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    scenario = data.get('scenario', 'Baseline')
    term = data.get('term', 'FA26')
    
    states_data = []
    for st in STATES:
        forecast = quick_forecast(program, student_type, term, scenario, st)
        job_signal = job_analyzer.get_signal(st, program)
        states_data.append({
            'state': st,
            'year1': forecast.year1_enrollment,
            'year2': forecast.year2_enrollment,
            'year3': forecast.year3_enrollment,
            'pool': forecast.projected_pool,
            'growth_rate': job_signal.job_growth_rate,
            'demand_score': job_analyzer.get_demand_score(st, program)
        })
    
    return jsonify({'states': states_data})


@app.route('/api/validate')
@login_required
def api_validate():
    """Validate all 162 combinations."""
    results = []
    passed = 0
    failed = 0
    
    for program in PROGRAMS:
        for student_type in STUDENT_TYPES:
            for term in TERMS:
                for scenario in SCENARIOS:
                    for state in STATES:
                        try:
                            forecast = quick_forecast(program, student_type, term, scenario, state)
                            roi = quick_roi(program, state,
                                          forecast.year1_enrollment,
                                          forecast.year2_enrollment,
                                          forecast.year3_enrollment,
                                          student_type)
                            
                            # Basic sanity checks
                            assert forecast.year1_enrollment >= 0
                            assert forecast.year2_enrollment >= forecast.year1_enrollment * 0.8
                            assert roi.roi_ratio >= 0
                            
                            passed += 1
                        except Exception as e:
                            failed += 1
                            results.append({
                                'combination': f"{program} + {student_type} + {term} + {scenario} + {state}",
                                'error': str(e)
                            })
    
    return jsonify({
        'total': passed + failed,
        'passed': passed,
        'failed': failed,
        'success_rate': passed / (passed + failed) * 100,
        'errors': results[:10]  # First 10 errors only
    })


@app.route('/api/ai-report/<program>')
@login_required
def api_ai_report(program):
    """Get AI exposure report for a program."""
    report = quick_ai_report(program)
    return jsonify(report)


@app.route('/health')
def health():
    """Health check endpoint for AWS."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/report', methods=['POST'])
@login_required
def api_report():
    """Generate and download PDF report."""
    if not FPDF_AVAILABLE:
        return jsonify({'success': False, 'error': 'PDF generation not available'}), 503
    
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    term = data.get('term', 'FA26')
    scenario = data.get('scenario', 'Baseline')
    state = data.get('state', 'CT')
    
    # Get all data
    forecast = quick_forecast(program, student_type, term, scenario, state)
    roi = quick_roi(program, state,
                   forecast.year1_enrollment,
                   forecast.year2_enrollment,
                   forecast.year3_enrollment,
                   student_type)
    job_signal = job_analyzer.get_signal(state, program)
    ai_exposure = ai_db.get_program_exposure(program)
    rec = job_analyzer.get_program_recommendation(state, program)
    
    # Determine recommendation
    if roi.roi_ratio >= 1.5 and forecast.confidence_score >= 0.75:
        recommendation = "STRONG GO"
    elif roi.roi_ratio >= 1.0 and forecast.confidence_score >= 0.60:
        recommendation = "GO"
    elif roi.roi_ratio >= 0.7 or forecast.confidence_score >= 0.50:
        recommendation = "CONDITIONAL"
    else:
        recommendation = "RECONSIDER"
    
    if roi.launch_recommendation == "delay":
        recommendation = "DO NOT LAUNCH"
    
    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(236, 72, 153)
    pdf.cell(0, 20, 'EduPredict Pro', 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, 'AI Degree Program Planning Report', 0, 1, 'C')
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Executive Summary Box
    pdf.set_fill_color(253, 242, 248)
    pdf.rect(10, pdf.get_y(), 190, 35, 'F')
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(131, 24, 67)
    pdf.cell(0, 10, 'EXECUTIVE SUMMARY', 0, 1)
    pdf.set_xy(15, pdf.get_y())
    pdf.set_font('Arial', '', 11)
    pdf.cell(95, 8, f'Program: {program}', 0, 0)
    pdf.cell(95, 8, f'State: {state}', 0, 1)
    pdf.set_xy(15, pdf.get_y())
    pdf.cell(95, 8, f'Student Type: {student_type}', 0, 0)
    pdf.cell(95, 8, f'Scenario: {scenario}', 0, 1)
    pdf.set_xy(15, pdf.get_y())
    pdf.cell(95, 8, f'Launch Term: {term}', 0, 1)
    pdf.ln(20)
    
    # Recommendation
    pdf.set_font('Arial', 'B', 16)
    if recommendation == "STRONG GO":
        pdf.set_text_color(16, 185, 129)
    elif recommendation == "GO":
        pdf.set_text_color(236, 72, 153)
    elif recommendation == "CONDITIONAL":
        pdf.set_text_color(245, 158, 11)
    else:
        pdf.set_text_color(239, 68, 68)
    pdf.cell(0, 15, f'Recommendation: {recommendation}', 0, 1, 'C')
    pdf.ln(5)
    
    # Key Metrics
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Key Metrics', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    metrics = [
        ("Year 1 Enrollment", f"{forecast.year1_enrollment} students (range: {forecast.year1_low}-{forecast.year1_high})"),
        ("3-Year Student Pool", f"{forecast.projected_pool} students"),
        ("Forecast Confidence", f"{int(forecast.confidence_score * 100)}% ({forecast.recommendation_confidence.upper()} confidence)"),
        ("ROI Ratio", f"{roi.roi_ratio}x"),
        ("Starting Salary", f"${roi.starting_salary:,}"),
        ("Program Revenue (3yr)", f"${roi.total_tuition_revenue:,}"),
        ("Break-Even Enrollment", f"{roi.break_even_enrollment} students"),
        ("Payback Period", f"{roi.payback_period_years} years"),
    ]
    
    for label, value in metrics:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 8, label + ':', 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(110, 8, value, 0, 1)
    
    pdf.ln(10)
    
    # AI Labor Market Analysis
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'AI Labor Market Analysis', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(80, 8, 'AI Exposure:', 0, 0)
    pdf.cell(110, 8, f"{int(ai_exposure.observed_exposure * 100)}% ({ai_exposure.risk_level.value.upper()} risk)", 0, 1)
    pdf.cell(80, 8, 'Coverage Gap:', 0, 0)
    pdf.cell(110, 8, f"{int(ai_exposure.coverage_gap * 100)}% (theory vs. reality)", 0, 1)
    pdf.cell(80, 8, 'BLS 2034 Impact:', 0, 0)
    pdf.cell(110, 8, f"{ai_exposure.bls_growth_projection_2034:.1f} percentage points", 0, 1)
    pdf.cell(80, 8, 'Job Market Growth:', 0, 0)
    pdf.cell(110, 8, f"{job_signal.job_growth_rate}% annually", 0, 1)
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 9)
    pdf.multi_cell(0, 5, f"Key Finding: {ai_exposure.key_finding}")
    pdf.ln(10)
    
    # 3-Year Enrollment Projection
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3-Year Enrollment Projection', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(60, 10, 'Year', 1, 0, 'C')
    pdf.cell(65, 10, 'Enrollment', 1, 0, 'C')
    pdf.cell(65, 10, 'Confidence Range', 1, 1, 'C')
    
    pdf.set_font('Arial', '', 11)
    years = [
        ("Year 1", forecast.year1_enrollment, f"{forecast.year1_low}-{forecast.year1_high}"),
        ("Year 2", forecast.year2_enrollment, "-"),
        ("Year 3", forecast.year3_enrollment, f"{forecast.year3_low}-{forecast.year3_high}"),
    ]
    for year, enrollment, range_str in years:
        pdf.cell(60, 10, year, 1, 0, 'C')
        pdf.cell(65, 10, f"{enrollment} students", 1, 0, 'C')
        pdf.cell(65, 10, range_str, 1, 1, 'C')
    pdf.ln(10)
    
    # Warnings and Opportunities
    if forecast.warning_flags or roi.financial_warnings:
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(220, 38, 38)
        pdf.cell(0, 10, 'Warnings & Considerations', 0, 1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)
        for warning in forecast.warning_flags[:3]:
            pdf.cell(10, 6, '-', 0, 0)
            pdf.multi_cell(180, 6, warning)
        for warning in roi.financial_warnings[:3]:
            pdf.cell(10, 6, '-', 0, 0)
            pdf.multi_cell(180, 6, warning)
        pdf.ln(10)
    
    if rec['opportunities']:
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(22, 163, 74)
        pdf.cell(0, 10, 'Opportunities', 0, 1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)
        for opp in rec['opportunities'][:3]:
            pdf.cell(10, 6, '+', 0, 0)
            pdf.multi_cell(180, 6, opp)
        pdf.ln(10)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, f'EduPredict Pro | Data: BLS 2023, Anthropic Economic Index 2026, IPEDS 2023-2024 | Report generated {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')
    
    # Save to buffer
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'EduPredict_Report_{state}_{term}_{program.replace(" ", "_")}.pdf'
    )


def init_db():
    """Initialize database and create default admin user."""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if none exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                is_admin=True,
                last_login=datetime.utcnow()
            )
            admin_password = os.environ.get('ADMIN_PASSWORD')

            if not admin_password:
                raise RuntimeError("ADMIN_PASSWORD environment variable is required.")

            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin")
            print("IMPORTANT: Change default password after first login!")


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=False)
