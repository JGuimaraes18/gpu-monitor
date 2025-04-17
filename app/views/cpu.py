from app import db
from app.models.cpu import CpuMemoryUsage


def save_cpu_data(machine_name, cpu_data):
    usage = CpuMemoryUsage(
        machine_name=machine_name,
        cpu_usage=cpu_data["total_usage"],
        memory_usage=cpu_data["memory_usage"]
    )
    db.session.add(usage)
    db.session.commit()