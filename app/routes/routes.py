from app.services.cpu import get_status_data_zabbix
from app.services.gpu import get_gpu_data, get_gpu_data_last_24h
from flask import Blueprint, render_template, jsonify
from app.zabbix.zabbix import connect_zabbix, get_HostsItems, get_hostgroup

routes_bp = Blueprint("routes", __name__)

@routes_bp.route('/api/cpu-status')
def cpu_check():
    apt = connect_zabbix()
    hostgroup_info = get_hostgroup("pomerode", apt)
    hostgroup_id = next((g['groupid'] for g in hostgroup_info if g['groupid'] == '30'), '')

    _, _, items = get_HostsItems(apt, hostgroup_id)
    data_raw = get_status_data_zabbix(items)

    cpu_utilization = float(data_raw.get("utilization", 0.0)) 
    cpu_total = cpu_utilization * 100

    memory_available = data_raw.get("memory_available", 0.0)
    memory_total = data_raw.get("memory_total", 1.0)
    memory_usage = (1 - memory_available / memory_total) * 100

    return jsonify({
        "total_usage": round(cpu_total, 2),
        "memory_usage": round(memory_usage, 2)
    })

@routes_bp.route("/api/gpu-status")
def gpu_status():
    return jsonify(get_gpu_data())

@routes_bp.route("/api/gpu-history")
def gpu_history():
    return jsonify(get_gpu_data_last_24h())

@routes_bp.route("/")
def home():
    gpu_data = get_gpu_data()
    return render_template("index.html", gpu_data=gpu_data)
