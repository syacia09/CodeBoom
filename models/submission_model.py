from extensions import db
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), nullable=False, default='python')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    verdicts = db.Column(JSON)
    runtime = db.Column(db.String(20))
    memory = db.Column(db.String(20))
    
    # Tambahkan relasi
    user = db.relationship('User', backref='submissions')
    problem = db.relationship('Problem', backref='submissions')

    @property
    def is_accepted(self):
        return self.verdicts and all(v['status']=='Passed' for v in self.verdicts)

    @property
    def verdict_status(self):
        return 'Accepted' if self.is_accepted else 'Wrong Answer'