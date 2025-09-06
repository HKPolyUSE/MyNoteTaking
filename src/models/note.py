from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db
import json


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # New optional fields
    tags = db.Column(db.Text, nullable=True)  # stored as JSON list
    event_date = db.Column(db.String(20), nullable=True)  # YYYY-MM-DD
    event_time = db.Column(db.String(20), nullable=True)  # HH:MM or similar

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Note {self.title}>'

    def get_tags_list(self):
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except Exception:
            # fallback: comma-separated
            return [t.strip() for t in str(self.tags).split(',') if t.strip()]

    def set_tags_list(self, tags_list):
        if not tags_list:
            self.tags = None
        else:
            # ensure list of strings
            self.tags = json.dumps([str(t) for t in tags_list])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': self.get_tags_list(),
            'event_date': self.event_date,
            'event_time': self.event_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

