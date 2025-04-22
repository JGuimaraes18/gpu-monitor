import time
from datetime import datetime
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

# def get_cpu_history(machine_name):
#     # machine_name = 'argentina.coids.inpe.br'
#     zapi = connect_zabbix()

#     # Opcional: ajuste conforme seu hostgroup
#     hostgroup = get_hostgroup("Linux servers GPU", zapi)
#     if not hostgroup:
#         return []

#     # Busca o host
#     host = zapi.host.get(filter={"host": machine_name})
#     print('HOST: ', host)
#     if not host:
#         return []

#     hostid = host[0]["hostid"]

#     # Busca item de CPU
#     items = zapi.item.get(hostids=hostid, filter={"name": "CPU usage"}, output=["itemid", "name"])
#     if not items:
#         return []

#     itemid = items[0]["itemid"]

#     # Pega últimos 24h
#     time_till = int(time.time())
#     time_from = time_till - 86400  # 24 horas

#     history = zapi.history.get(
#         itemids=itemid,
#         time_from=time_from,
#         time_till=time_till,
#         output='extend',
#         history=0,  # float
#         sortfield='clock',
#         sortorder='ASC',
#         limit=1000
#     )

#     result = []
#     for h in history:
#         result.append({
#             "timestamp": datetime.fromtimestamp(int(h["clock"])).strftime('%Y-%m-%d %H:%M:%S'),
#             "value": float(h["value"])
#         })

#     return result



def get_cpu_history(machine_name):
    zapi = connect_zabbix()

    all_hosts = zapi.host.get(output=["hostid", "host"])

    matched_host = next((h for h in all_hosts if machine_name in h["host"]), None)
    
    if not matched_host:
        print(f"[WARN] Host '{machine_name}' não encontrado no Zabbix.")
        return []

    hostid = matched_host["hostid"]

    items = zapi.item.get(hostids=hostid, filter={"name": "CPU utilization"}, output=["itemid", "name"])
    # for item in items:
    #     print(item["name"])

    if not items:
        print("[ERRO] Item não encontrado.")
        return []

    item = items[0]
    itemid = item["itemid"]
    value_type = int(item["value_type"])

    print(f"Item: {item['name']}, Tipo: {value_type}")

    
    if not items:
        return []

    itemid = items[0]["itemid"]

    # Pega últimos 24h
    time_till = int(time.time())
    time_from = time_till - 86400

    history = zapi.history.get(
        itemids=itemid,
        time_from=time_from,
        time_till=time_till,
        output='extend',
        history=0,  
        sortfield='clock',
        sortorder='ASC',
        limit=1000
    )

    print('aquiiiiiiiiiii: ', history)
    result = []
    for h in history:
        result.append({
            "timestamp": datetime.fromtimestamp(int(h["clock"])).strftime('%Y-%m-%d %H:%M:%S'),
            "value": float(h["value"])
        })

    return result