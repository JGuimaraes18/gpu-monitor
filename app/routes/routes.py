from app.services.cpu import get_cpu_data, get_cpu_history
from app.services.gpu import get_gpu_data, get_gpu_data_last_24h
from app.services.machines import get_all_machines
from flask import Blueprint, render_template, jsonify, request

from app.views.cpu import save_cpu_data

routes_bp = Blueprint("routes", __name__)

@routes_bp.route('/api/cpu-status')
def cpu_status():
    machine_name = request.args.get("machine")
    data = get_cpu_data(machine_name)
    # save_cpu_data(machine_name, data)
    return jsonify(data)

@routes_bp.route("/api/cpu-history")
def cpu_history():
    machine_name = request.args.get("machine")
    data = get_cpu_history(machine_name)
    print(f'data: ', data)
    return jsonify(data)

@routes_bp.route("/api/gpu-status")
def gpu_status():
    return jsonify(get_gpu_data())

@routes_bp.route("/api/gpu-history")
def gpu_history():
    return jsonify(get_gpu_data_last_24h())

@routes_bp.route("/")
def home():
    get_machines = get_all_machines()
    return render_template("index.html", machines=get_machines)

@routes_bp.route("/host")
def host():
    machine_name_full = request.args.get("name")
    machine_name = machine_name_full.split(".")[0]
    return render_template("index-cpu-gpu.html", machine_name=machine_name)