import sjcl
from Crypto.Hash import SHA256

def doPbkdf2NotCoded(passwd, saltLocal):
    derivedKey = sjcl.sjcl.PBKDF2(passwd, saltLocal, hmac_hash_module=SHA256)
    hexdevkey = derivedKey.hex()
    return hexdevkey


def get_router_data(host, username, password):
    import requests

    s = requests.Session()

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'de',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'PHPSESSID=e8cf047f0844ea48dd255a6b58c8a146',
        'DNT': '1',
        'Origin': 'http://' + host + '',
        'Referer': 'http://' + host + '/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'X-CSRF-TOKEN': '',
        'X-Requested-With': 'XMLHttpRequest',
    }

    data = {
        'username': username,
        'password': 'seeksalthash',
        'logout': "true"
    }

    response = s.post('http://' + host + '/api/v1/session/login',
                      data=data, headers=headers, verify=False)
    salt = response.json()["salt"]
    saltwebui = response.json()["saltwebui"]

    h1 = doPbkdf2NotCoded(password, salt)
    pwd = doPbkdf2NotCoded(h1, saltwebui)

    data = {
        'username': username,
        'password': pwd
    }
    response = s.post('http://' + host + '/api/v1/session/login',
                      data=data, headers=headers, verify=False)
    #response.cookies["cwd"] = "No"
    s.cookies = response.cookies
    s.cookies["cwd"] = "No"

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'de',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Referer': 'http://' + host + '/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        "Accept-Language": "de,en-GB;q=0.9,en;q=0.8,de-DE;q=0.7,en-US;q=0.6",
    }

    response = s.get(
        'http://' + host + '/api/v1/session/menu?_=1667331451901', headers=headers, verify=False)
    response = s.get(
        'http://' + host + '/api/v1/sta_status?_=1667331451904', headers=headers, verify=False)
    response = s.get(
        'http://' + host + '/api/v1/CheckTimeOut?_=1667331451907', headers=headers, verify=False)
    response = s.get('http://' + host + '/api/v1/host/hostTbl,WPSEnable1,WPSEnable2,RadioEnable1,RadioEnable2,SSIDEnable1,SSIDEnable2,SSIDEnable3,operational,call_no,call_no2,LineStatus1,LineStatus2,DeviceMode,ScheduleEnable,dhcpLanTbl,dhcpV4LanTbl,lpspeed_1,lpspeed_2,lpspeed_3,lpspeed_4,AdditionalInfos1,AdditionalInfos2?_=1667331451911', headers=headers, verify=False)
    return response.text

