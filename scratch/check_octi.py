import requests

URL = "http://192.168.111.133:8080/graphql"
TOKEN = "flgrn_octi_tkn_RlxuWvRFLqzwVMQoxRjX1H3uwY9mpAIMz7_LB9wbuthn2V45L6mkfE6YQQSrHf47"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# We'll query counts and a few Intrusion Sets
query = """
query {
  intrusionSets(first: 5) {
    pageInfo {
      globalCount
    }
    edges {
      node {
        name
      }
    }
  }
  malwares(first: 5) {
    pageInfo {
      globalCount
    }
    edges {
      node {
        name
      }
    }
  }
  attackPatterns(first: 5) {
    pageInfo {
      globalCount
    }
  }
}
"""

res = requests.post(URL, json={"query": query}, headers=headers)
if res.status_code == 200:
    data = res.json().get('data', {})
    print("Intrusion Sets count:", data.get('intrusionSets', {}).get('pageInfo', {}).get('globalCount'))
    print("Intrusion Sets sample:", [e['node']['name'] for e in data.get('intrusionSets', {}).get('edges', [])])
    
    print("Malwares count:", data.get('malwares', {}).get('pageInfo', {}).get('globalCount'))
    print("Malwares sample:", [e['node']['name'] for e in data.get('malwares', {}).get('edges', [])])
    
    print("Attack Patterns (MITRE TTPs) count:", data.get('attackPatterns', {}).get('pageInfo', {}).get('globalCount'))
else:
    print(res.status_code, res.text)
