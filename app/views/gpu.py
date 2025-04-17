from app import db
from app.models.gpu import GpuUsage, GpuUser

def save_to_db(data):
    for gpu in data:
        usage = GpuUsage(
            gpu_id=gpu["gpu"],
            mem_used=gpu["mem_used"],
            gpu_usage=gpu.get("gpu_usage", 0),
            temperature=gpu.get("temperature", 0)
        )
        db.session.add(usage)
        db.session.flush()

        for user in gpu.get("users", []):
            user_entry = GpuUser(
                gpu_usage_id=usage.id,
                name=user["name"],
                mem=user["mem"]
            )
            db.session.add(user_entry)

    db.session.commit()
    
