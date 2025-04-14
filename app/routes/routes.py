from app.zabbix.zabbix import connect_zabbix, get_HostsItems, get_hostgroup



def cpu_check():
    apt = connect_zabbix()
    hostgroup_name = "pomerode"
    hostgroup_info = get_hostgroup(hostgroup_name, apt)
    hostgroup_id = ''
    for gi in hostgroup_info:
        if gi['groupid'] == '30':
            hostgroup_id = gi['groupid']
    hostgroups,hosts,items=get_HostsItems(apt, hostgroup_id)