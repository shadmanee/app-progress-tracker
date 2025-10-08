from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_migrate import Migrate
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from models import db, Professor, University, Department, Program, ResearchArea
from models import HiringStatus, ContactThrough, professor_programs

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phd_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    # Explicitly load the relationships to avoid N+1 query problem
    professors = Professor.query.options(
        db.joinedload(Professor.university),
        db.joinedload(Professor.department),
        db.joinedload(Professor.programs),
        db.joinedload(Professor.research_areas)
    ).all()
    return render_template('index.html', professors=professors)

# Add a route to get professor data as JSON for editing
@app.route('/get_professor/<int:professor_id>')
def get_professor(professor_id):
    professor = Professor.query.options(
        db.joinedload(Professor.university),
        db.joinedload(Professor.department),
        db.joinedload(Professor.programs),
        db.joinedload(Professor.research_areas)
    ).get_or_404(professor_id)

    # Prepare data for JSON response
    data = {
        'id': professor.id,
        'name': professor.name,
        'title': professor.title,
        'university_name': professor.university.name if professor.university else '',
        'university_country': professor.university.country if professor.university else '',
        'university_state': professor.university.state if professor.university else '',
        'university_city': professor.university.city if professor.university else '',
        'university_ranking': professor.university.ranking_usnews if professor.university and professor.university.ranking_usnews else None,
        'department_name': professor.department.name if professor.department else '',
        'email': professor.email,
        'personal_website': professor.personal_website or '',
        'lab_group_name': professor.lab_group_name or '',
        'lab_website': professor.lab_website or '',
        'hiring_status': professor.hiring_status.value,
        'contact_through': professor.contact_through.value,
        'form_link': professor.form_link or '',
        'notes': professor.notes or '',
        'programs': [p.name for p in professor.programs],
        'research_areas': [ra.name for ra in professor.research_areas]
    }
    return jsonify(data)

@app.route('/add_professor', methods=['GET', 'POST'])
def add_professor():
    professor_to_edit = None
    if request.method == 'GET' and 'id' in request.args:
        # Editing existing professor
        professor_id = request.args.get('id', type=int)
        if professor_id:
            professor_to_edit = Professor.query.options(
                db.joinedload(Professor.university),
                db.joinedload(Professor.department),
                db.joinedload(Professor.programs),
                db.joinedload(Professor.research_areas)
            ).get_or_404(professor_id)

    if request.method == 'POST':
        professor_id = request.form.get('professor_id') # Get the hidden ID field
        if professor_id: # Editing existing
            professor = Professor.query.get_or_404(int(professor_id))
            # Update existing professor's fields
            professor.name = request.form['name']
            professor.title = request.form['title']
            # Handle university update - for simplicity, we'll recreate the university if name changes
            # In a real app, you might want a more sophisticated approach
            if request.form.get('university_name') != professor.university.name:
                # Find existing university or create new one
                university = University.query.filter_by(name=request.form['university_name']).first()
                if not university:
                    university = University(
                        name=request.form['university_name'],
                        country=request.form.get('university_country', ''),
                        state=request.form.get('university_state', ''),
                        city=request.form.get('university_city', ''),
                        ranking_usnews=request.form.get('university_ranking', type=int)
                    )
                    db.session.add(university)
                    db.session.flush() # Get ID without committing
                professor.university = university
            else:
                # Update university details if they were changed
                if professor.university:
                    professor.university.country = request.form.get('university_country', '')
                    professor.university.state = request.form.get('university_state', '')
                    professor.university.city = request.form.get('university_city', '')
                    professor.university.ranking_usnews = request.form.get('university_ranking', type=int)

            # Handle department update - similar approach
            if request.form.get('department_name') != professor.department.name:
                # Check if department exists for this university
                university_id = professor.university.id
                department = Department.query.filter_by(name=request.form['department_name'], university_id=university_id).first()
                if not department:
                    department = Department(
                        name=request.form['department_name'],
                        university_id=university_id
                    )
                    db.session.add(department)
                    db.session.flush() # Get ID without committing
                professor.department = department

            professor.email = request.form['email']
            professor.personal_website = request.form.get('personal_website', '')
            professor.lab_group_name = request.form.get('lab_group_name', '')
            professor.lab_website = request.form.get('lab_website', '')
            professor.hiring_status = HiringStatus(request.form['hiring_status'])
            professor.contact_through = ContactThrough(request.form['contact_through'])
            professor.form_link = request.form.get('form_link', '')
            professor.notes = request.form.get('notes', '')
        else: # Adding new professor
            # Handle university
            if request.form.get('university_name'):
                # Check if university already exists
                university = University.query.filter_by(name=request.form['university_name']).first()
                if not university:
                    university = University(
                        name=request.form['university_name'],
                        country=request.form.get('university_country', ''),
                        state=request.form.get('university_state', ''),
                        city=request.form.get('university_city', ''),
                        ranking_usnews=request.form.get('university_ranking', type=int)
                    )
                    db.session.add(university)
                    db.session.flush()  # Get ID without committing
                    university_id = university.id
                else:
                    university_id = university.id
            else:
                university_id = int(request.form['university_id'])

            # Handle department
            if request.form.get('department_name'):
                # Check if department already exists for this university
                department = Department.query.filter_by(name=request.form['department_name'], university_id=university_id).first()
                if not department:
                    department = Department(
                        name=request.form['department_name'],
                        university_id=university_id
                    )
                    db.session.add(department)
                    db.session.flush()  # Get ID without committing
                    department_id = department.id
                else:
                    department_id = department.id
            else:
                department_id = int(request.form['department_id'])

            # Create professor
            professor = Professor(
                name=request.form['name'],
                title=request.form['title'],
                university_id=university_id,
                department_id=department_id,
                email=request.form['email'],
                personal_website=request.form.get('personal_website', ''),
                lab_group_name=request.form.get('lab_group_name', ''),
                lab_website=request.form.get('lab_website', ''),
                hiring_status=HiringStatus(request.form['hiring_status']),
                contact_through=ContactThrough(request.form['contact_through']),
                form_link=request.form.get('form_link', ''),
                notes=request.form.get('notes', '')
            )
            db.session.add(professor)

        # Handle programs (both for new and existing professors)
        # Clear existing relationships first
        professor.programs.clear()
        # Add new ones
        if request.form.get('program_names'):
            program_names = [name.strip() for name in request.form['program_names'].split(',') if name.strip()]
            for name in program_names:
                # Check if program exists, create if not
                program = Program.query.filter_by(name=name, department_id=professor.department_id).first()
                if not program:
                    program = Program(name=name, department_id=professor.department_id)
                    db.session.add(program)
                    db.session.flush()
                professor.programs.append(program)

        # Handle research areas (both for new and existing professors)
        # Clear existing relationships first
        professor.research_areas.clear()
        # Add new ones
        if request.form.get('research_area_names'):
            area_names = [name.strip() for name in request.form['research_area_names'].split(',') if name.strip()]
            for name in area_names:
                area = ResearchArea.query.filter_by(name=name).first()
                if not area:
                    area = ResearchArea(name=name)
                    db.session.add(area)
                    db.session.flush()
                professor.research_areas.append(area)

        db.session.commit()
        return redirect(url_for('index'))

    # For GET request - show the form
    universities = University.query.all()
    departments = Department.query.all()
    programs = Program.query.all()
    research_areas = ResearchArea.query.all()

    # Pass the professor data if editing
    return render_template('add_professor.html',
                         professor=professor_to_edit, # Pass the professor object for editing
                         universities=universities,
                         departments=departments,
                         programs=programs,
                         research_areas=research_areas,
                         hiring_statuses=HiringStatus,
                         contact_methods=ContactThrough)

@app.route('/delete_professor/<int:professor_id>', methods=['DELETE'])
def delete_professor(professor_id):
    professor = Professor.query.get_or_404(professor_id)
    try:
        db.session.delete(professor)
        db.session.commit()
        return '', 204  # No content response for successful deletion
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@app.route('/programs')
def programs_list():
    programs = (
        db.session.query(
            Program,
            func.count(professor_programs.c.professor_id).label('professor_count')
        )
        .options(
            joinedload(Program.department).joinedload(Department.university)
        )
        .join(Department)
        .join(University)
        .outerjoin(professor_programs, Program.id == professor_programs.c.program_id)
        .group_by(Program.id, Department.id, University.id)
        .order_by(University.name.asc(), Department.name.asc(), Program.name.asc())
        .all()
    )
    return render_template("programs_list.html", programs=programs)
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)