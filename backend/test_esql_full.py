from elasticsearch import Elasticsearch
import urllib3
import json
urllib3.disable_warnings()

es = Elasticsearch('https://10.14.0.3:9200', verify_certs=False, api_key='WnkzaGZwOEJIb3B3a2tZYXhKS1E6QXhSVElyOThKM18tTnFtVFZGOUdXdw==')

q = """
from logs-attackchain-*
| where source.ip == "192.168.5.155" and
  not user.name in ("ANONYMOUS LOGON", "-") and not user.name like "*$" and user.domain != "NT AUTHORITY" and
  not winlog.event_data.Status in ("0xc000015b", "0xc000005e", "0xc0000133", "0xc0000192", "0xc00000dc")
| eval Esql.time_window = date_trunc(60 seconds, @timestamp)
| stats Esql.failed_auth_count = COUNT(*), Esql.count_distinct_target_user_name = count_distinct(winlog.event_data.TargetUserName) by winlog.computer_name, source.ip, Esql.time_window, winlog.logon.type
"""

try:
    resp = es.esql.query(body={'query': q})
    print(resp.body['values'])
except Exception as e:
    print('Error:', e)
