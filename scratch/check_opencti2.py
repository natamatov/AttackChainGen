import requests
import json

URL = "http://192.168.111.133:8080"
EMAIL = "nodir.atamatov@followmars.com"
PASSWORD = "Zxcvbn12345@"

session = requests.Session()

login_data = {
    "username": EMAIL,
    "password": PASSWORD
}

# Try POST /auth/local
res_auth = session.post(f"{URL}/auth/local", data=login_data)
print("Auth local status:", res_auth.status_code)
print(res_auth.text[:200])

if res_auth.status_code == 200:
    # See if there's an API token in the response or if we can query now
    query = """
    query {
        about {
            version
        }
        me {
            id
            name
            user_email
            api_token
        }
    }
    """
    res_gql = session.post(f"{URL}/graphql", json={"query": query})
    print("GraphQL me status:", res_gql.status_code)
    if res_gql.status_code == 200:
        print(res_gql.json())
