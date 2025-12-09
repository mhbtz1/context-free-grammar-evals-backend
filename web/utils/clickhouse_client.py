import clickhouse_connect

def get_client(host: str, port: int, username: str, password: str):
    if isinstance(host, str):
        host = host.strip('"').strip("'")
    if isinstance(port, str):
        port = int(port.strip('"').strip("'"))
    if isinstance(username, str):
        username = username.strip('"').strip("'")
    if isinstance(password, str):
        password = password.strip('"').strip("'")
    
    if host.startswith('https://'):
        host = host.replace('https://', '')
    elif host.startswith('http://'):
        host = host.replace('http://', '')
    
    secure = '.clickhouse.cloud' in host or int(port) == 8443
    
    client = clickhouse_connect.get_client(
        host=host,
        port=int(port),
        username=username,
        password=password,
        secure=secure
    )
    return client