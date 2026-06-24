from jinja2 import Template

# Docker Compose ファイルのテンプレート
# サービスの部分には、各ノードの情報を入れる
docker_compose_template = Template('''\
version: "3"
services:
{{ services }}
networks:
  ndn-network:
    driver: bridge
''')

# docker compose ファイルにおけるサービス部分単体のテンプレート
# node_name にはノード名、enviroments には環境変数の辞書、command にはコマンドを入れる
service_template = Template('''\
  {{ node_name }}:
    build:
      context: .
    working_dir: /workspaces
    networks:
      ndn-network:
    volumes:
      - ..:/workspaces
    tty: true
    stdin_open: true
    command: {{ command }}
    environment:
      {%- for env_name, env_value in enviroments.items() %}
      - {{ env_name }}={{ env_value }}
      {%- endfor -%}
''')


# 以上のような構造の、ノード名、環境変数の辞書とコマンドを持つデータ構造
class NodeInfoForDockerCompose:
    def __init__(self, node_name: str, environments: dict[str, str], command: str):
        self.node_name = node_name
        self.environments = environments
        self.command = command


# ノードの情報を受け取り、Docker Compose の内容の文字列を生成する関数
def docker_compose_generator(node_infos: list[NodeInfoForDockerCompose]) -> str:
    """
    ノードの情報を受け取り、Docker Compose の内容の文字列を生成する関数。

    Args:
        node_infos (list[NodeInfo]): ノードの情報

    Returns:
        str: Docker Compose の内容
    """
    services = ''
    for node_info in node_infos:
        service = service_template.render(
            node_name=node_info.node_name, 
            enviroments=node_info.environments,
            command=node_info.command
        )
        services += service + '\n'
    return docker_compose_template.render(services=services)


if __name__ == '__main__':
    # ノードの情報を作成
    node_infos = [
        NodeInfoForDockerCompose(node_name='ndn-node-1', environments={'FUNCITON_FILE_PATH': '/workspaces/config/function/function-a.py', 'NLSR_CONFIG_FILE_PATH': '/workspaces/generated/nlsr/nlsr-1.conf'}, command='bash -c " ./restart.sh && ./auto_nlsr.sh && tail -f /dev/null"'),
        NodeInfoForDockerCompose(node_name='ndn-node-2', environments={'FUNCITON_FILE_PATH': '/workspaces/config/function/function-a.py', 'NLSR_CONFIG_FILE_PATH': '/workspaces/generated/nlsr/nlsr-2.conf'}, command='bash -c " ./restart.sh && ./auto_nlsr.sh && tail -f /dev/null"'),
        NodeInfoForDockerCompose(node_name='ndn-node-3', environments={'FUNCITON_FILE_PATH': '/workspaces/config/function/function-a.py', 'NLSR_CONFIG_FILE_PATH': '/workspaces/generated/nlsr/nlsr-3.conf'}, command='bash -c " ./restart.sh && ./auto_nlsr.sh && tail -f /dev/null"')
    ]

    # Docker Compose ファイルを生成
    docker_compose = docker_compose_generator(node_infos)
    print(docker_compose)