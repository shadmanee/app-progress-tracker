from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# class User(db.Model):

class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    university = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    research_area = db.Column(db.String(200))
    email = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Not Contacted')
    contact_date = db.Column(db.DateTime)
    response_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'university': self.university,
            'department': self.department,
            'research_area': self.research_area,
            'email': self.email,
            'status': self.status,
            'contact_date': self.contact_date.strftime('%Y-%m-%d') if self.contact_date else None,
            'response_date': self.response_date.strftime('%Y-%m-%d') if self.response_date else None,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d')
        }

class University():
    pass

class Department():
    pass

class Program():
    pass

class ResearchArea():
    pass