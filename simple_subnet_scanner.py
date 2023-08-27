修改绝对路径为/root/logs

import requests
import datetime
from concurrent.futures import ThreadPoolExecutor
from netaddr import IPNetwork, AddrFormatError
import logging
import os
import subprocess
import threading

# 删除IP地址的代码
api_url = 'http://127.0.0.1:8000/api/ipam/ip-addresses/'
api_token = 'EdqsTh3nU+E+Ni0.hpov:~sV2^32qnKXUj~.Wwq!'

headers = {
    'Authorization': f'Token {api_token}',
    'Content-Type': 'application/json',
}

start_time = datetime.datetime.now()

try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status() 

    current_datetime = datetime.datetime.now()

    log_filename = current_datetime.strftime('%Y-%m-%d_%H-%M-%S') + '_deleted.log'  

    log_file_path = os.path.join('/root/logs', log_filename)

    with open(log_file_path, 'w') as log_file:
        ip_addresses = response.json()['results']

        lock = threading.Lock()  # 创建线程锁

        def delete_ip_address(ip_address):
            delete_url = f"{api_url}{ip_address['id']}/"
            try_count = 0
            while try_count < 2:  # 最多重试两次
                try:
                    delete_response = requests.delete(delete_url, headers=headers)
                    delete_response.raise_for_status()
                    with lock:
                        log_file.write(f"Deleted IP address with ID {ip_address['id']}\n")
                    break  # 成功删除，退出重试循环
                except requests.exceptions.RequestException as e:
                    with lock:
                        log_file.write(f"Failed to delete IP address with ID {ip_address['id']}: {str(e)}\n")
                    try_count += 1
            else:
                with lock:
                    log_file.write(f"Failed to delete IP address with ID {ip_address['id']} after 2 retries\n")

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = [executor.submit(delete_ip_address, ip_address) for ip_address in ip_addresses]
            for result in results:
                result.result()

        end_time = datetime.datetime.now()
        elapsed_time = end_time - start_time
        log_file.write(f"Program execution time: {elapsed_time}\n")

        print(f'删除日志记录到了 {log_file_path}')

except requests.exceptions.RequestException as e:
    error_message = f'Error: {str(e)}'
    logging.error(error_message)
    print(error_message)

except Exception as e:
    error_message = f'Error: {str(e)}'
    logging.error(error_message)
    print(error_message)

print('删除完成')

# 扫描和写入IP地址的代码
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_new.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_url = "http://localhost:8000/api"
api_token = "EdqsTh3nU+E+Ni0.hpov:~sV2^32qnKXUj~.Wwq!"

second_program_start_time = datetime.datetime.now()  # 记录程序开始时间

def check_address(address):
    data = {
        "address": str(address),
        "status": "reserved",
        "description": "可用地址"
    }

    for _ in range(2):
        response_ping = subprocess.run(["ping", "-c", "1", "-W", "1", str(address)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if response_ping.returncode == 0:
            data["status"] = "active"
            data["description"] = "已被使用"
            break

    response = requests.post(f"{api_url}/ipam/ip-addresses/", json=data, headers={"Authorization": f"Token {api_token}"})
    if response.status_code == 201:
        logging.info(f"地址 {address} 写入成功")
    else:
        logging.error(f"地址 {address} 写入失败：{response.text}")

with open('network.txt', 'r') as f:
    networks = f.read().splitlines()

for network_str in networks:
    try:
        network = IPNetwork(network_str)
    except AddrFormatError as e:
        logging.error(f"Invalid network address '{network_str}': {e}")
        continue

    ip_addresses = []
    for ip in network:
        if ip not in (network.network, network.broadcast) and not ip.is_reserved():
            ip_addresses.append(ip)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = [executor.submit(check_address, ip) for ip in ip_addresses]
        for result in results:
            result.result()

second_program_end_time = datetime.datetime.now()  # 记录程序结束时间
elapsed_time = second_program_end_time - second_program_start_time  # 计算程序运行时间
logging.info(f"扫描和写入消耗时间： {elapsed_time}")
print(f'扫描和写入记录到了 {log_file}')

print("扫描和写入完成")  # 输出 "扫描和写入完成"
