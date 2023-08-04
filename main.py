import random
import time
from loguru import logger
import requests
import json
import csv
from web3.auto import w3
from eth_account.messages import encode_defunct
import datetime


def get_nonce(address, proxy=None):
    headers = {
        'authority': 'api.cyberconnect.dev',
        'accept': '*/*',
        'accept-language': 'ru,en;q=0.9',
        'authorization': '',
        'content-type': 'application/json',
        'origin': 'https://cyber.co',
        'referer': 'https://cyber.co/',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "YaBrowser";v="23"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 YaBrowser/23.7.1.1140 Yowser/2.5 Safari/537.36'}
    json_data = {
        'query': '\n    mutation nonce($address: EVMAddress!) {\n  nonce(request: {address: $address}) {\n    status\n    message\n    data\n  }\n}\n    ',
        'variables': {
            'address': address.lower(),
        },
        'operationName': 'nonce',
    }
    try:
        response = requests.post('https://api.cyberconnect.dev/profile/', headers=headers, json=json_data,
                                 proxies=proxy)
        if response.status_code == 200:
            nonce = json.loads(response.text)['data']['nonce']['data']
            return nonce, headers
        time.sleep(5)
        return get_nonce(address, proxy)
    except Exception as e:
        logger.error(f'{address} - {e}, пробую еще раз')
        time.sleep(2)
        return get_nonce(address, proxy)


def auth(address, key, proxy=None):
    nonce, headers = get_nonce(address)
    now = datetime.datetime.utcnow()
    timenow = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'
    futuredate = now + datetime.timedelta(days=14)
    timefuture = futuredate.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'
    msg = f'cyber.co wants you to sign in with your Ethereum account:\n{address}\n\n\nURI: https://cyber.co\nVersion: 1\nChain ID: 1\nNonce: {nonce}\nIssued At: {timenow}\nExpiration Time: {timefuture}\nNot Before: {timenow}'
    msg_ = w3.eth.account.sign_message(encode_defunct(text=msg), key)
    signature = msg_.signature.hex()
    json_data = {
        'query': '\n    mutation login($request: LoginRequest!) {\n  login(request: $request) {\n    status\n    message\n    data {\n      id\n      privateInfo {\n        accessToken\n      }\n    }\n  }\n}\n    ',
        'variables': {
            'request': {
                'address': address,
                'signature': signature,
                'signedMessage': f'cyber.co wants you to sign in with your Ethereum account:\n{address}\n\n\nURI: https://cyber.co\nVersion: 1\nChain ID: 1\nNonce: {nonce}\nIssued At: {timenow}\nExpiration Time: {timefuture}\nNot Before: {timenow}',
            },
        },
        'operationName': 'login',
    }
    try:
        response = requests.post('https://api.cyberconnect.dev/profile/', headers=headers, json=json_data,
                                 proxies=proxy)
        if response.status_code == 200:
            logger.success(f'{address} - успешно авторизовался...')
            token = json.loads(response.text)['data']['login']['data']['privateInfo']['accessToken']
            headers['authorization'] = token
            return headers
        time.sleep(5)
        return auth(address, key, proxy)
    except Exception as e:
        logger.error(f'{address} - {e}, пробую еще раз')
        time.sleep(2)
        return False


def get_reward(key, proxy=None):
    address = w3.eth.account.from_key(key).address
    headers = auth(address, key, proxy)
    if not headers:
        return key, address, 'error with auth'
    json_data = {
        'query': '\n    query checkSeason1Eligibility {\n  cyberRewardEligibility {\n    total\n    eligibility {\n      type\n      count\n      detail {\n        value\n        amount\n        chainId\n        type\n      }\n    }\n  }\n}\n    ',
        'operationName': 'checkSeason1Eligibility',
    }

    try:
        response = requests.post('https://api.cyberconnect.dev/profile/', headers=headers, json=json_data,
                                 proxies=proxy)
        if response.status_code == 200:
            text = json.loads(response.text)
            reward = text['data']['cyberRewardEligibility']['total']
            if reward:
                logger.success(f'{address} - {reward} CYBER')
                return key, address, f'{reward} CYBER'
            else:
                logger.debug(f'{address} - на кошельке нет раварда CYBER')
                return key, address, f'0 CYBER'
        time.sleep(5)
        return get_reward(key, proxy)
    except Exception as e:
        logger.error(f'{address} - {e}, пробую еще раз')
        time.sleep(2)
        return get_reward(key, proxy)


def write_to_csv(key, address, result):
    with open('result.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(['key', 'address', 'reward'])
        writer.writerow([key, address, result])


def main():
    print(f'\n{" " * 32}автор - https://t.me/iliocka{" " * 32}\n')
    with open("keys.txt", "r") as f:
        keys = [row.strip() for row in f]
    with open("proxies.txt", "r") as f:
        proxies = [row.strip() for row in f]

    for key in keys:
        if proxies:
            proxy_ = random.choice(proxies)
            proxy = {'http': f'http://{proxy_}', 'https': f'http://{proxy_}'}
        else:
            proxy = None

        res = get_reward(key, proxy)
        write_to_csv(*res)
        time_ = random.randint(5, 30)
        logger.info(f'cплю {time_} cекунд...')
        time.sleep(time_)

    logger.success(f'Успешно проверил {len(keys)} кошельков...')
    logger.success(f'muнетинг закончен...')
    print(f'\n{" " * 32}автор - https://t.me/iliocka{" " * 32}\n')
    print(f'\n{" " * 32}donate - EVM 0xFD6594D11b13C6b1756E328cc13aC26742dBa868{" " * 32}\n')
    print(f'\n{" " * 32}donate - trc20 TMmL915TX2CAPkh9SgF31U4Trr32NStRBp{" " * 32}\n')


if __name__ == '__main__':
    main()
