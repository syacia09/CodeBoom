from extensions import db
from sqlalchemy.dialects.sqlite import JSON

class Problem(db.Model):
    __tablename__ = 'problems'

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    statement = db.Column(db.Text, nullable=False)
    input_format = db.Column(db.String, nullable=False)
    output_format = db.Column(db.String, nullable=False)
    samples = db.Column(JSON, nullable=False)  # pastikan tipe JSON

    def __repr__(self):
        return f"<Problem {self.id}: {self.title}>"
