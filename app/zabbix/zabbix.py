from dotenv import load_dotenv
import os 
from pyzabbix import ZabbixAPI

load_dotenv()

def connect_zabbix():
   user = os.getenv("USER_ZABBIX")
   password = os.getenv("USER_PASSWORD_ZABBIX")
   server = os.getenv("SERVER_ZABBIX")
   zapi = ZabbixAPI(server)
   zapi.session.verify = False
   zapi.login(user, password)
    
   return zapi

def get_HostsItems(api,hostgroup_id):
    hostgroups = api.hostgroup.get(output=['id'],filter={'name': 'Linux servers GPU'},)
    hosts = api.host.get({"output": ['name', 'status'],"groupids": hostgroup_id,"filter": {"status": 0}})
    items = api.item.get(output=['name','lastvalue','hostid',], groupids=hostgroups[0]['groupid'],)
    return hostgroups, hosts, items


def get_hostgroup(hostgroup_name,api):
    hostgroup = api.hostgroup.get({"output": "extend", "filter": {"name": hostgroup_name}})
    return hostgroup


