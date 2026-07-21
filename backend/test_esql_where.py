from elasticsearch import Elasticsearch
import urllib3
import json
urllib3.disable_warnings()

es = Elasticsearch('https://10.14.0.3:9200', verify_certs=False, api_key='WnkzaGZwOEJIb3B3a2tZYXhKS1E6QXhSVElyOThKM18tTnFtVFZGOUdXdw==')

queries = [
    '''from logs-attackchain-* | where source.ip == "192.168.5.155" | limit 1''',
    '''from logs-attackchain-* | where event.category == "authentication" and source.ip == "192.168.5.155" | limit 1''',
    '''from logs-attackchain-* | where host.os.type == "windows" and source.ip == "192.168.5.155" | limit 1''',
    '''from logs-attackchain-* | where winlog.logon.type == "Network" and source.ip == "192.168.5.155" | limit 1''',
    '''from logs-attackchain-* | where cidr_match(TO_IP(source.ip), "192.168.5.0/24") | limit 1''',
    '''from logs-attackchain-* | where source.ip == "192.168.5.155" | eval Esql.time_window = date_trunc(60 seconds, @timestamp) | stats Esql.failed_auth_count = COUNT(*) by Esql.time_window | limit 10'''
]

for i, q in enumerate(queries):
    print(f"Test {i}")
    try:
        resp = es.esql.query(body={'query': q})
        if resp.body['values']:
            print("  => MATCHED!")
            if i == 5:
                print(resp.body['values'])
        else:
            print("  => NO RESULTS")
    except Exception as e:
        print('  => Error:', e)
