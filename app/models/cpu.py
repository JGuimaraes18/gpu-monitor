from ..db import db
from datetime import datetime

class CpuMemoryUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_name = db.Column(db.String(100), nullable=False)
    
    cpu_usage = db.Column(db.Float, nullable=False)        
    memory_usage = db.Column(db.Float, nullable=False)     
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)