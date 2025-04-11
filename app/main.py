from flask import render_template, jsonify, request
from . import create_app
from .models import GpuUsage, GpuUser
from .db import db
from dotenv import load_dotenv
import subprocess
import re
import os
from collections import defaultdict
from datetime import datetime, timedelta


load_dotenv()
app = create_app()

def filter_grapich_24h(gpu_data):
    now = datetime.now()
    limite_inferior = now - timedelta(hours=24)

    result = {}

    for gpu_id, register in gpu_data.items():
        filter_register = []
        for r in register:
            ts = datetime.strptime(r['timestamp'], '%d/%m %H:%M')
            ts = ts.replace(year=now.year)
            if limite_inferior <= ts <= now:
                filter_register.append(r)

        result[gpu_id] = filter_register

    return result

def get_gpu_data():
    usuario = os.getenv("SSH_USER")
    ip = os.getenv("SSH_HOST")

    comando_nvidia = f"ssh -o StrictHostKeyChecking=no {usuario}@{ip} 'nvidia-smi'"
    comando_gpustat = f"ssh -o StrictHostKeyChecking=no {usuario}@{ip} 'gpustat --no-color'"

    output_nvidia = subprocess.check_output(comando_nvidia, shell=True, encoding="utf-8")
    output_gpustat = subprocess.check_output(comando_gpustat, shell=True, encoding="utf-8")

    lines_nvidia = output_nvidia.splitlines()
    lines_gpustat = output_gpustat.splitlines()

    data = []
    gpu_id = -1

    for line in lines_nvidia:
        if re.search(r'\d+W\s+/\s+\d+W', line) and re.search(r'\d+MiB\s+/\s+\d+MiB', line):
            gpu_id += 1
            match_power = re.search(r'(\d+)W\s+/\s+(\d+)W', line)
            match_mem = re.search(r'(\d+)MiB\s+/\s+(\d+)MiB', line)

            if match_power and match_mem:
                power_used, power_cap = map(int, match_power.groups())
                mem_used, mem_total = map(int, match_mem.groups())

                data.append({
                    "gpu": gpu_id,
                    "power_usage": power_used,
                    "power_cap": power_cap,
                    "mem_used": mem_used,
                    "mem_total": mem_total
                })

    for line in lines_gpustat:
        match = re.match(
            r'\[(\d+)\].*?\|\s+(\d+)[°\']C,\s+(\d+)\s%\s+\|\s+(\d+)\s/\s+(\d+)\s+MB\s+\|?(?:\s+([\w\.\-]+)?\((\d+)M\))?',
            line
        )
        if match:
            gpu_id = int(match.group(1))
            temp = int(match.group(2))
            usage = int(match.group(3))
            mem_used = int(match.group(4))
            mem_total = int(match.group(5))
            user = match.group(6) or "Desconhecido"
            user_mem = int(match.group(7)) if match.group(7) else 0

            if gpu_id < len(data):
                gpu = data[gpu_id]

                if "users" not in gpu:
                    gpu["users"] = []

                if user != "Desconhecido":
                    gpu["users"].append({
                        "name": user,
                        "mem": user_mem
                    })

                gpu.update({
                    "temperature": temp,
                    "gpu_usage": usage,
                    "memory_used": mem_used,
                    "memory_total": mem_total
                })
    
    save_to_db(data)
    return data

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

@app.route("/api/gpu-status")
def gpu_status():
    data = get_gpu_data()
    return jsonify(data)

@app.route("/api/gpu-history")
def gpu_history():
    limit = int(request.args.get("limit", 100))
    results = (
        db.session.query(GpuUsage)
        .order_by(GpuUsage.id.desc())
        .limit(limit * 4)
        .all()
    )

    grouped = defaultdict(lambda: defaultdict(list))

    for entry in results:
        gpu_id = entry.gpu_id
        hkey = entry.timestamp.replace(minute=0, second=0, microsecond=0)
        grouped[gpu_id][hkey].append(entry)

    history = {}

    for gpu_id, hours in grouped.items():
        history[gpu_id] = []
        for h_key, entries in sorted(hours.items()):
            count = len(entries)
            avg_mem_used = sum(e.mem_used for e in entries) / count
            avg_gpu_usage = sum(e.gpu_usage for e in entries) / count
            avg_temp = sum(e.temperature for e in entries) / count

            history[gpu_id].append({
                "mem_used": round(avg_mem_used, 2),
                "gpu_usage": round(avg_gpu_usage, 2),
                "temperature": round(avg_temp, 2),
                "timestamp": h_key.strftime("%d/%m %H:%M")
            })

    history_f = filter_grapich_24h(history)
    return jsonify(history_f)


@app.route("/")
def home():
    gpu_data = get_gpu_data()
    return render_template("index.html", gpu_data=gpu_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)