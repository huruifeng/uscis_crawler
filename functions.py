import requests
import json

def get_response(url):
    headers = {
        "Content-Type": "application/json"
    }
    resp = requests.get(url,headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        return "error"

def get_token(dir):
    N = 0
    while True:
        N = N + 1
        url = "https://egov.uscis.gov/csol-api/ui-auth"
        x = get_response(url)
        if len(x["JwtResponse"]["accessToken"])>50:
            x_token = {"x_token":"Bearer " + x["JwtResponse"]["accessToken"]}
            with open(dir+'/auth_token.json', 'w') as fp:
                json.dump(x_token, fp)
            break
        else:
            if N >= 10000:
                break

    return x_token
