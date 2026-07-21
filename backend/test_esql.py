from elasticsearch import Elasticsearch
import urllib3
import json
urllib3.disable_warnings()

es = Elasticsearch('https://10.14.0.3:9200', verify_certs=False, api_key='WnkzaGZwOEJIb3B3a2tZYXhKS1E6QXhSVElyOThKM18tTnFtVFZGOUdXdw==')

query = """
from logs-system.security*, logs-windows.forwarded*, winlogbeat-*, logs-attackchain-*
| where event.category == "authentication" and host.os.type == "windows" and event.action == "logon-failed" and
  winlog.logon.type == "Network" and source.ip is not null and winlog.computer_name is not null and
  not cidr_match(TO_IP(source.ip), "127.0.0.0/8", "::1") and
  not user.name in ("ANONYMOUS LOGON", "-") and not user.name like "*$" and user.domain != "NT AUTHORITY" and
  not winlog.event_data.Status in ("0xc000015b", "0xc000005e", "0xc0000133", "0xc0000192", "0xc00000dc")
| eval Esql.time_window = date_trunc(60 seconds, @timestamp)
| stats Esql.failed_auth_count = COUNT(*),
        Esql.count_distinct_target_user_name = count_distinct(winlog.event_data.TargetUserName),
        Esql.target_user_name_values = VALUES(winlog.event_data.TargetUserName) by winlog.computer_name, source.ip, Esql.time_window, winlog.logon.type
"""

try:
    resp = es.esql.query(body={'query': query})
    print(json.dumps(resp, indent=2))
except Exception as e:
    print('Error:', e)
