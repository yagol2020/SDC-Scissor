import subprocess
import socket
import json

import numpy

from sdc_scissor.cli import my_extract_features_fun
import time


def kill_process_using_port(port):
    try:
        # Linux命令找到监听特定端口的进程ID
        cmd = f"lsof -t -i:{port}"
        pid = subprocess.check_output(cmd, shell=True).decode().strip()
        if pid:
            print(f"Killing process on port {port} with PID {pid}")
            subprocess.check_call(["kill", "-9", pid])
    except subprocess.CalledProcessError as e:
        print(f"No process found running on port {port}. Error: {e}")
    except Exception as e:
        print(f"Error killing process: {e}")


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def start_server():
    port = 12555
    if is_port_in_use(port):
        print(f"Port {port} is already in use. Attempting to kill the process using it...")
        kill_process_using_port(port)
    time.sleep(1)  # 等待一秒，确保进程已经被杀死

    # 创建套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 设置socket选项，以便地址和端口可以被重用
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 绑定地址和端口
    server_socket.bind(("localhost", port))

    # 开始监听
    server_socket.listen()
    print(f"Server is listening on localhost:{port}")

    try:
        while True:  # 主循环，不断接受新的连接
            print("Waiting for a new connection...")
            conn, addr = server_socket.accept()  # 接受新的连接
            print(f"Connected by {addr}")
            with conn:
                while True:  # 通信循环，处理当前连接的数据
                    data = conn.recv(999999)
                    if not data:
                        break  # 如果客户端关闭连接，退出循环
                    recv_data = data.decode()
                    recv_data = json.load(open(recv_data, "r"))
                    # 用于存储去重后的行
                    unique_rows = []
                    # 用于记录已出现的行
                    seen = set()

                    # 遍历每一行
                    for row in recv_data:
                        # 将行转换为元组，以便可哈希，并判断是否已出现
                        row_tuple = tuple(row)
                        if row_tuple not in seen:
                            # 如果行没有出现过，添加到结果和记录中
                            unique_rows.append(row)
                            seen.add(row_tuple)
                    try:
                        res = my_extract_features_fun(unique_rows)
                        conn.sendall(json.dumps(res.to_dict()).encode())  # 发送响应数据
                    except Exception as e:
                        print(f"Error extracting features: {e}")
                        conn.sendall(json.dumps({"error": "Error extracting features"}).encode())

    except KeyboardInterrupt:
        print("\nServer is shutting down.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
