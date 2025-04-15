from ..db import db
from datetime import datetime

class GpuUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gpu_id = db.Column(db.Integer, nullable=False)
    mem_used = db.Column(db.Integer, nullable=False)
    gpu_usage = db.Column(db.Integer, nullable=False)
    temperature = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("GpuUser", backref="gpu_usage", lazy=True)

class GpuUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gpu_usage_id = db.Column(db.Integer, db.ForeignKey('gpu_usage.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    mem = db.Column(db.Integer, nullable=False)