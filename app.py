from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, Professor
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phd_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/home')
def dashboard():
    professors = Professor.query.all()
    
    # Calculate statistics
    stats = {
        'total': len(professors),
        'contacted': len([p for p in professors if p.status != 'Not Contacted']),
        'responses': len([p for p in professors if p.status in ['Response', 'Interview', 'Accepted']]),
        'interviews': len([p for p in professors if p.status == 'Interview']),
        'accepted': len([p for p in professors if p.status == 'Accepted'])
    }
    
    # Get unique universities and research areas for filtering
    universities = list(set([p.university for p in professors]))
    research_areas = list(set([p.research_area for p in professors if p.research_area]))
    
    return render_template('dashboard.html', 
                         professors=professors, 
                         stats=stats,
                         universities=sorted(universities),
                         research_areas=sorted(research_areas))

@app.route('/add_professor', methods=['GET', 'POST'])
def add_professor():
    if request.method == 'POST':
        prof = Professor(
            name=request.form['name'],
            university=request.form['university'],
            department=request.form['department'],
            research_area=request.form['research_area'],
            email=request.form['email']
        )
        db.session.add(prof)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_professor.html')

@app.route('/edit_professor/<int:id>', methods=['GET', 'POST'])
def edit_professor(id):
    professor = Professor.query.get_or_404(id)
    
    if request.method == 'POST':
        professor.name = request.form['name']
        professor.university = request.form['university']
        professor.department = request.form['department']
        professor.research_area = request.form['research_area']
        professor.email = request.form['email']
        professor.status = request.form['status']
        professor.notes = request.form['notes']
        
        # Update contact date if status changes to 'Contacted'
        if professor.status == 'Contacted' and not professor.contact_date:
            professor.contact_date = datetime.now()
        elif professor.status in ['Response', 'Interview', 'Accepted', 'Rejected'] and not professor.response_date:
            professor.response_date = datetime.now()
        
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('edit_professor.html', professor=professor)

@app.route('/delete_professor/<int:id>')
def delete_professor(id):
    professor = Professor.query.get_or_404(id)
    db.session.delete(professor)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/api/stats')
def api_stats():
    professors = Professor.query.all()
    
    # Calculate weekly data
    start_date = datetime.now() - timedelta(days=60)
    weekly_data = []
    
    for i in range(9):  # Last 9 weeks
        week_start = start_date + timedelta(weeks=i)
        week_end = week_start + timedelta(weeks=1)
        
        contacted = Professor.query.filter(
            Professor.contact_date >= week_start,
            Professor.contact_date < week_end
        ).count()
        
        responded = Professor.query.filter(
            Professor.response_date >= week_start,
            Professor.response_date < week_end
        ).count()
        
        weekly_data.append({
            'week': week_start.strftime('%b %d'),
            'contacted': contacted,
            'responded': responded
        })
    
    return jsonify(weekly_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)