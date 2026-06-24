# 自動生成時にコピーして使う、全ノード共通のDockerfile

# ベースイメージ
FROM hydrokhoos/ndn-all:latest

# 1. 必要なツールとDockerエンジンのインストールを1回で実行
RUN apt-get update && apt-get install -y \
    curl gnupg lsb-release iptables kmod \
    python3-pip python3-dev \
    git tmux net-tools iproute2 \
    tcpdump dnsutils iputils-ping netcat psmisc \
    && rm -rf /var/lib/apt/lists/*

# 2. Docker公式リポジトリのセットアップ
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io

# 3. Pythonライブラリのインストール
RUN pip3 install ndn-python-repo ndn-python-client psutil docker

# 4. コードとスクリプトの配置
COPY ./work/spy_agent.py /usr/local/bin/spy_agent.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 5. エントリポイント
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
