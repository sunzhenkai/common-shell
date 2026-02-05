#!/usr/bin/env python3
"""
检查 registry-1.docker.io 的所有 IP 地址和连通性
"""

import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple


def get_all_ips(hostname: str) -> List[str]:
    """
    获取指定主机名的所有 IP 地址
    """
    try:
        # 获取所有 IPv4 地址
        ipv4_addresses = []
        try:
            # 使用 getaddrinfo 获取所有地址
            results = socket.getaddrinfo(hostname, None, socket.AF_INET)
            for result in results:
                ip = result[4][0]
                if ip not in ipv4_addresses:
                    ipv4_addresses.append(ip)
        except socket.gaierror as e:
            print(f"DNS 解析错误: {e}", file=sys.stderr)
            return []

        # 尝试获取 IPv6 地址
        ipv6_addresses = []
        try:
            results = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            for result in results:
                ip = result[4][0]
                if ip not in ipv6_addresses:
                    ipv6_addresses.append(ip)
        except socket.gaierror:
            pass

        return ipv4_addresses + ipv6_addresses
    except Exception as e:
        print(f"获取 IP 地址时出错: {e}", file=sys.stderr)
        return []


def check_ping(ip: str, timeout: int = 3) -> Tuple[str, bool, str]:
    """
    检查 IP 地址的 ping 连通性
    返回: (ip, 是否连通, 响应时间或错误信息)
    """
    try:
        # 使用 ping 命令检查连通性
        # -c 1: 只发送 1 个包
        # -W timeout: 超时时间（秒）
        # -q: 安静模式
        if ':' in ip:  # IPv6
            cmd = ['ping6', '-c', '1', '-W', str(timeout), '-q', ip]
        else:  # IPv4
            cmd = ['ping', '-c', '1', '-W', str(timeout), '-q', ip]
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 1
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            return (ip, True, f"{elapsed*1000:.2f}ms")
        else:
            return (ip, False, "超时或不可达")
    except subprocess.TimeoutExpired:
        return (ip, False, "超时")
    except FileNotFoundError:
        # 如果没有 ping 命令，尝试使用 socket 连接
        return check_socket_connectivity(ip, timeout)
    except Exception as e:
        return (ip, False, f"错误: {str(e)}")


def check_socket_connectivity(ip: str, timeout: int = 3) -> Tuple[str, bool, str]:
    """
    使用 socket 检查 IP 地址的连通性（检查 443 端口）
    """
    try:
        is_ipv6 = ':' in ip
        sock = socket.socket(socket.AF_INET6 if is_ipv6 else socket.AF_INET)
        sock.settimeout(timeout)
        
        start_time = time.time()
        # IPv6 地址需要用方括号包裹
        addr = (ip, 443) if not is_ipv6 else (ip, 443, 0, 0)
        result = sock.connect_ex(addr)
        elapsed = time.time() - start_time
        sock.close()
        
        if result == 0:
            return (ip, True, f"{elapsed*1000:.2f}ms")
        else:
            return (ip, False, "端口不可达")
    except socket.timeout:
        return (ip, False, "连接超时")
    except Exception as e:
        return (ip, False, f"错误: {str(e)}")


def check_connectivity_with_fallback(ip: str, timeout: int = 3) -> Tuple[str, bool, str]:
    """
    检查连通性，优先使用 ping，如果失败则尝试 HTTP
    """
    # 先尝试 ping
    ping_result = check_ping(ip, timeout=timeout)
    if ping_result[1]:
        return ping_result
    
    # 如果 ping 失败，尝试 HTTP（针对 Docker Registry）
    http_result = check_http_connectivity(ip, timeout=timeout)
    if http_result[1]:
        return http_result
    
    # 如果都失败，返回 ping 的结果（包含错误信息）
    return ping_result


def check_http_connectivity(ip: str, timeout: int = 5) -> Tuple[str, bool, str]:
    """
    检查 HTTP/HTTPS 连通性（针对 Docker Registry）
    """
    try:
        import urllib.request
        import urllib.error
        
        # IPv6 地址需要用方括号包裹
        if ':' in ip:
            url = f"https://[{ip}]/v2/"
        else:
            url = f"https://{ip}/v2/"
        
        req = urllib.request.Request(url)
        req.add_header('Host', 'registry-1.docker.io')
        
        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                elapsed = time.time() - start_time
                status = response.getcode()
                if status in [200, 401, 403]:  # 401/403 表示服务可达
                    return (ip, True, f"{elapsed*1000:.2f}ms (HTTP {status})")
                else:
                    return (ip, True, f"{elapsed*1000:.2f}ms (HTTP {status})")
        except urllib.error.HTTPError as e:
            elapsed = time.time() - start_time
            # HTTP 错误也表示服务可达
            return (ip, True, f"{elapsed*1000:.2f}ms (HTTP {e.code})")
        except urllib.error.URLError as e:
            elapsed = time.time() - start_time
            # 如果 HTTP 失败，尝试使用 ping 或 socket
            ping_result = check_ping(ip, timeout=2)
            if ping_result[1]:
                return (ip, True, f"ping 可达 ({ping_result[2]})")
            return (ip, False, f"连接失败: {str(e)}")
    except Exception as e:
        # 如果 HTTP 检查失败，回退到 ping
        ping_result = check_ping(ip, timeout=2)
        if ping_result[1]:
            return ping_result
        return (ip, False, f"错误: {str(e)}")


def main():
    hostname = "registry-1.docker.io"
    
    print(f"正在解析 {hostname} 的所有 IP 地址...")
    print("=" * 80)
    
    # 获取所有 IP
    ips = get_all_ips(hostname)
    
    if not ips:
        print(f"❌ 无法获取 {hostname} 的 IP 地址")
        sys.exit(1)
    
    print(f"✅ 找到 {len(ips)} 个 IP 地址:")
    for ip in ips:
        print(f"  - {ip}")
    print()
    
    print("正在检查连通性...")
    print("=" * 80)
    
    # 并发检查连通性
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有检查任务
        futures = []
        for ip in ips:
            # 优先使用 ping 检查（更快），如果失败再尝试 HTTP
            futures.append(executor.submit(check_connectivity_with_fallback, ip))
        
        # 收集结果
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    # 按 IP 地址排序
    results.sort(key=lambda x: (
        ':' not in x[0],  # IPv4 在前
        socket.inet_aton(x[0]) if ':' not in x[0] else x[0]
    ))
    
    # 输出结果
    print(f"\n{'IP 地址':<45} {'状态':<10} {'详情'}")
    print("-" * 80)
    
    reachable_count = 0
    unreachable_count = 0
    
    for ip, is_reachable, detail in results:
        status = "✅ 可达" if is_reachable else "❌ 不可达"
        print(f"{ip:<45} {status:<10} {detail}")
        
        if is_reachable:
            reachable_count += 1
        else:
            unreachable_count += 1
    
    print("-" * 80)
    print(f"\n统计:")
    print(f"  总 IP 数: {len(ips)}")
    print(f"  可达: {reachable_count}")
    print(f"  不可达: {unreachable_count}")
    
    if unreachable_count > 0:
        print(f"\n⚠️  有 {unreachable_count} 个 IP 地址不可达")
        print(f"   注意: 某些 IP 可能因为防火墙策略不允许 ping，但不影响实际使用")
    else:
        print(f"\n✅ 所有 IP 地址均可达")
    
    # 即使有不可达的 IP，也正常退出（因为可能是防火墙策略）
    # 如果需要严格检查，可以取消下面的注释
    # if unreachable_count > 0:
    #     sys.exit(1)


if __name__ == "__main__":
    main()
