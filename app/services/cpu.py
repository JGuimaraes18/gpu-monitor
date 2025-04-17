from flask import jsonify
from app.zabbix.zabbix import connect_zabbix, get_HostsItems, get_hostgroup

def get_cpu_data(machine_name):
    apt = connect_zabbix()
    hostgroup_info = get_hostgroup(machine_name, apt)
    hostgroup_id = next((g['groupid'] for g in hostgroup_info if g['groupid'] == '30'), '')

    _, _, items = get_HostsItems(apt, hostgroup_id)
    data_raw = get_status_data_zabbix(items)

    cpu_utilization = float(data_raw.get("utilization", 0.0)) 
    cpu_total = cpu_utilization * 100

    memory_available = data_raw.get("memory_available", 0.0)
    memory_total = data_raw.get("memory_total", 1.0)
    memory_usage = (1 - memory_available / memory_total) * 100

    return {
        "total_usage": round(cpu_total, 2),
        "memory_usage": round(memory_usage, 2)
    }

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

def get_status_data_zabbix(items):
    data = {
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
        "steal_time": None,
        "memory_total": None,
        "memory_available": None
    }

    for item in items:
        name = item["name"]
        value = item["lastvalue"]

        if name == "CPU utilization":
            data["utilization"] = value
        elif name == "CPU idle time":
            data["idle_time"] = value
        elif name == "CPU system time":
            data["system_time"] = value
        elif name == "CPU user time":
            data["user_time"] = value
        elif name == "CPU iowait time":
            data["iowait_time"] = value
        elif name == "CPU nice time":
            data["nice_time"] = value
        elif name == "CPU guest time":
            data["guest_time"] = value
        elif name == "CPU guest nice time":
            data["guest_nice_time"] = value
        elif name == "CPU interrupt time":
            data["interrupt_time"] = value
        elif name == "CPU softirq time":
            data["softirq_time"] = value
        elif name == "CPU steal time":
            data["steal_time"] = value
        elif name == "Available memory":
            data["memory_available"] = float(value)
        elif name == "Total memory":
            data["memory_total"] = float(value)

    return data

# def cpu_check():
#     apt = connect_zabbix()
#     hostgroup_name = "pomerode"
#     hostgroup_info = get_hostgroup(hostgroup_name, apt)
#     hostgroup_id = ''
#     for gi in hostgroup_info:
#         if gi['groupid'] == '30':
#             hostgroup_id = gi['groupid']
#     hostgroups,hosts,items=get_HostsItems(apt, hostgroup_id)