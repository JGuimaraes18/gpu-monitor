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
from .error import error
from app.zabbix.zabbix import connect_zabbix, get_HostsItems, get_hostgroup


load_dotenv()
app = create_app()

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

    if len(data) == 0:
        return error
    
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

def get_gpu_data_last_24h():
    now = datetime.utcnow()
    limite_inferior = now - timedelta(hours=24)

    registros = GpuUsage.query.filter(GpuUsage.timestamp >= limite_inferior).order_by(GpuUsage.timestamp).all()

    grouped = defaultdict(lambda: defaultdict(list))

    for entry in registros:
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

    return history

@app.route("/api/gpu-status")
def gpu_status():
    data = get_gpu_data()
    return jsonify(data)

@app.route("/api/gpu-history")
def gpu_history():
    history = get_gpu_data_last_24h()
    return jsonify(history)

@app.route("/")
def home():
    gpu_data = get_gpu_data()
    return render_template("cpu.html", gpu_data=gpu_data)

def get_disk_usage_data_zabbix(items):
    discos = {}

    for i in items:
        name = i['name']
        value = i['lastvalue']

        if 'Total space' in name or 'Used space' in name or 'Space utilization' in name:
            nome_disco = name.split(':')[0].strip()

            if nome_disco not in discos:
                discos[nome_disco] = {}

            if 'Total space' in name:
                discos[nome_disco]['total'] = int(value)
            elif 'Used space' in name:
                discos[nome_disco]['used'] = int(value)
            elif 'Space utilization' in name:
                discos[nome_disco]['percent'] = float(value)

    return discos

def get_cpu_status_data_zabbix(items):
    cpu_data = {
        "utilization": None,
        "idle_time": None,
        "system_time": None,
        "user_time": None,
        "iowait_time": None,
        "nice_time": None,
        "guest_time": None,
        "guest_nice_time": None,
        "interrupt_time": None,
        "softirq_time": None,
        "steal_time": None
    }

    for item in items:
        name = item["name"]
        value = item["lastvalue"]

        if name == "CPU utilization":
            cpu_data["utilization"] = value
        elif name == "CPU idle time":
            cpu_data["idle_time"] = value
        elif name == "CPU system time":
            cpu_data["system_time"] = value
        elif name == "CPU user time":
            cpu_data["user_time"] = value
        elif name == "CPU iowait time":
            cpu_data["iowait_time"] = value
        elif name == "CPU nice time":
            cpu_data["nice_time"] = value
        elif name == "CPU guest time":
            cpu_data["guest_time"] = value
        elif name == "CPU guest nice time":
            cpu_data["guest_nice_time"] = value
        elif name == "CPU interrupt time":
            cpu_data["interrupt_time"] = value
        elif name == "CPU softirq time":
            cpu_data["softirq_time"] = value
        elif name == "CPU steal time":
            cpu_data["steal_time"] = value

    return cpu_data


# def get_cpu_status_data_zabbix(items):
#     cpu_data = {
#         "total_usage": None,
#         "avg_freq": None,
#         "temperature": None,
#         "per_core_usage": {}
#     }

#     for item in items:
#         name = item["name"]
#         value = item["lastvalue"]

#         if "Total Usage" in name:
#             cpu_data["total_usage"] = float(value)
#         elif "Average Frequency" in name:
#             cpu_data["avg_freq"] = float(value)
#         elif "Temperature" in name:
#             cpu_data["temperature"] = float(value)
#         elif "Core" in name and "Usage" in name:
#             parts = name.split()
#             core_index = int(parts[2])
#             cpu_data["per_core_usage"][core_index] = float(value)

#     sorted_cores = sorted(cpu_data["per_core_usage"].items())
#     cpu_data["per_core_usage"] = [usage for _, usage in sorted_cores]

#     return cpu_data


# @app.route("/api/cpu-status")
# def api_cpu_status():
#     return jsonify({
#         "total_usage": 23.5,
#         "temperature": 65.0,
#         "avg_freq": 2500.0,
#         "per_core_usage": [20.1, 25.3, 22.7, 26.4]  # Exemplo com 4 núcleos
#     })


@app.route('/api/cpu-status')
def cpu_check():
    apt = connect_zabbix()
    hostgroup_name = "pomerode"
    hostgroup_info = get_hostgroup(hostgroup_name, apt)
    hostgroup_id = ''
    for gi in hostgroup_info:
        if gi['groupid'] == '30':
            hostgroup_id = gi['groupid']
    hostgroups,hosts,items=get_HostsItems(apt, hostgroup_id)
    i = get_cpu_status_data_zabbix(items)
    print(f'get_disk_usage_data_zabbix: {items}')
    return jsonify(i)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
