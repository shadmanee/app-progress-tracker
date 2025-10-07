from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import CheckConstraint, Enum
import enum

db = SQLAlchemy()

class DegreeLevels(enum.Enum):
    BACHELORS = "Bachelor's"
    MASTERS = "Master's"
    DIPLOMA = "Diploma"
    
class EnglishProficiencyTest(enum.Enum):
    IELTS = "IELTS"
    TOEFL = "TOEFL"
    
class StandardizedTest(enum.Enum):
    GRE = "GRE"
    
class Term(enum.Enum):
    F26 = "Fall 2026"
    S27 = "Spring 2027"
    F27 = "Fall 2027"

class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    highest_degree = db.Column(Enum(DegreeLevels), default=DegreeLevels.BACHELORS)
    gpa_highest_degree = db.Column(db.Float, CheckConstraint("gpa_highest_degree <= 4.00", name="gpa_limit_check"))
    institution_highest_degree = db.Column(db.String(100))
    english_proficiency_test = db.Column(Enum(EnglishProficiencyTest), default=EnglishProficiencyTest.IELTS)
    toefl_score = db.Column(db.Integer, CheckConstraint("toefl_score <= 120", name="toefl_score_check"))
    ielts_score = db.Column(db.Float, CheckConstraint("ielts_score <= 9.0", name="ielts_score_check"))
    standardized_test = db.Column(Enum(StandardizedTest), default=StandardizedTest.GRE)
    gre_score = db.Column(db.Integer, CheckConstraint("gre_score <= 340", name="gre_score_check"))
    preferred_start_term = db.Column(Enum(Term), default=Term.F26)
    country_of_residence = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    country = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50)) # or province
    city = db.Column(db.String(50), nullable=False)
    ranking_usnews = db.Column(db.Integer)
    
    departments = db.relationship("Department", backref="university", lazy=True)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey('university.id'), nullable=False)
    
    # Add unique constraint for the combination of name and university
    __table_args__ = (db.UniqueConstraint('name', 'university_id', name='unique_dept_university'),)
    
    programs = db.relationship("Program", backref="department", lazy=True)

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    
    def __repr__(self):
        return f"PhD in {self.name}"

class ResearchArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)

# Many-to-many relationships
professor_programs = db.Table('professor_programs',
    db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'), primary_key=True),
    db.Column('program_id', db.Integer, db.ForeignKey('program.id'), primary_key=True)
)

professor_research_areas = db.Table('professor_research_areas',
    db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'), primary_key=True),
    db.Column('research_area_id', db.Integer, db.ForeignKey('research_area.id'), primary_key=True)
)

class HiringStatus(enum.Enum):
    NOT_HIRING = "Not Hiring"
    HIRING = "Hiring"
    UNAVAILABLE = "Information Unavailable"  # Fixed typo

class ContactThrough(enum.Enum):
    EMAIL = "Email"
    APPLICATION = "Application"
    FORM = "Form"

class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey('university.id'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False, index=True)
    email = db.Column(db.String(100), nullable=False)
    personal_website = db.Column(db.String(200))
    lab_group_name = db.Column(db.String(255))
    lab_website = db.Column(db.String(200))
    hiring_status = db.Column(Enum(HiringStatus), default=HiringStatus.UNAVAILABLE, index=True)
    contact_through = db.Column(Enum(ContactThrough), default=ContactThrough.EMAIL)
    form_link = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Define relationships explicitly
    university = db.relationship('University', backref='professors')
    department = db.relationship('Department', backref='professors')
    
    # Many-to-many relationships
    programs = db.relationship('Program', secondary=professor_programs, backref='professors')
    research_areas = db.relationship('ResearchArea', secondary=professor_research_areas, backref='professors')