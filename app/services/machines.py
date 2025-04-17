import os
from app.zabbix.zabbix import connect_zabbix, get_HostsItems, get_hostgroup
from dotenv import load_dotenv


load_dotenv()

def get_all_machines():
    
    apt = connect_zabbix()
    hostgroup_name = ""
    hostgroup_info = get_hostgroup(hostgroup_name, apt)
    hostgroup_id = []
    for gi in hostgroup_info:
        hostgroup_id.append(gi['groupid'])
    hostgroups,hosts,items=get_HostsItems(apt, hostgroup_id)
    hosts_accounts = [{'name': host['name']} for host in hosts]
    return sorted(hosts_accounts, key=lambda m: m["name"].lower())