import requests
import json

URL = "http://192.168.111.133:8080"
EMAIL = "nodir.atamatov@followmars.com"
PASSWORD = "Zxcvbn12345@"

session = requests.Session()

# Get the login page to extract any potential CSRF tokens or just to set initial cookies
resp = session.get(f"{URL}/")
print("Initial get status:", resp.status_code)

# OpenCTI typically uses a GraphQL endpoint.
# Let's see what happens if we POST to the graphql endpoint directly with a login mutation, or if it's a standard REST endpoint for login.
# Often in OpenCTI it's /graphql with an authenticate mutation, or /auth/local/login

login_data = {
    "username": EMAIL,
    "password": PASSWORD
}

# Try /auth/local
res_auth = session.post(f"{URL}/auth/local", data=login_data)
print("Auth local status:", res_auth.status_code)
# print(res_auth.text[:200])

# Now let's try querying GraphQL to see what we have
query = """
query {
    threatActors {
        edges {
            node {
                name
            }
        }
    }
}
"""
res_gql = session.post(f"{URL}/graphql", json={"query": query})
print("GraphQL status:", res_gql.status_code)
if res_gql.status_code == 200:
    print(res_gql.json())
else:
    print(res_gql.text[:500])
