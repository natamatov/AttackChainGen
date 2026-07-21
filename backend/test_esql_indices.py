from elasticsearch import Elasticsearch
import urllib3
import json
urllib3.disable_warnings()

es = Elasticsearch('https://10.14.0.3:9200', verify_certs=False, api_key='WnkzaGZwOEJIb3B3a2tZYXhKS1E6QXhSVElyOThKM18tTnFtVFZGOUdXdw==')

q = """
from logs-attackchain-default
| where source.ip == "192.168.5.155"
| eval Esql.time_window = date_trunc(60 seconds, @timestamp)
| stats Esql.failed_auth_count = COUNT(*) by Esql.time_window
"""
try:
    resp = es.esql.query(body={'query': q})
    print('logs-attackchain-default:', resp.body['values'])
except Exception as e:
    print('Error:', e)

q = """
from logs-system.security-attackchain
| where source.ip == "192.168.5.155"
| eval Esql.time_window = date_trunc(60 seconds, @timestamp)
| stats Esql.failed_auth_count = COUNT(*) by Esql.time_window
"""
try:
    resp = es.esql.query(body={'query': q})
    print('logs-system.security-attackchain:', resp.body['values'])
except Exception as e:
    pass
