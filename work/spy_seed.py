import os
import sys
import json
import logging
import asyncio
import psutil
import docker
from ndn.app import NDNApp
from ndn.encoding import Name, Component

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = NDNApp()

# 環境変数からの静的情報の取得
MY_NODE_NAME = os.environ.get("NODE_NAME", "producer_1")
CPU_MODEL = os.environ.get("CPU_MODEL", "Intel Core i7-2026")
PASSMARK = int(os.environ.get("PASSMARK", "12000"))
MAX_MEM = int(os.environ.get("MAX_MEM", "4096"))  # MB単位

# 管理対象とするDockerイメージ名（ListやDeleteのフィルタリングに使用）
TARGET_IMAGE = "dockerprac-ndn-worker-task"

def get_dynamic_resource():
    """
    親コンテナ（自身）の動的リソース情報を取得
    """
    cpu_usage = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    mem_usage = mem.percent
    return cpu_usage, mem_usage

@app.route(f'/spy/{MY_NODE_NAME}')
def on_spy_interest(name, interest_param, app_param):
    # NDNの名前空間を文字列のリストに変換
    name_str_list = [Component.to_str(c) for c in name]
    
    # 期待するURI構造: /spy/{MY_NODE_NAME}/{operation}/...
    # 例: /spy/producer_1/resource
    operation = name_str_list[2] if len(name_str_list) > 2 else "list" # 指定がない場合はデフォルトでlist

    logging.info(f"Received Interest for operation: {operation}")

    # ==========================================
    # 1. resource: 動的リソース情報の返却とスコア計算
    # ==========================================
    if operation == 'resource':
        cpu, mem = get_dynamic_resource()
        
        # スコア計算（利用可能なリソースの割合に応じたPassMark値）
        availability = (100.0 - cpu) / 100.0
        score = int(PASSMARK * availability)
        
        payload = {
            "node_name": MY_NODE_NAME,
            "status": "success",
            "cpu_usage": f"{cpu}%",
            "memory_usage": f"{mem}%",
            "score": score
        }
        app.put_data(name, content=json.dumps(payload).encode('utf-8'), freshness_period=1)
        logging.info(f"Responded to 'resource' query. Score: {score}")

    # ==========================================
    # 2. create_child: 子コンテナ（Functionサーバー）の生成
    # ==========================================
    elif operation == 'create_child':
        # 引数のバリデーション（要素数が足りているかチェック）
        if len(name_str_list) < 6:
            error_msg = {"status": "error", "message": "Missing arguments for create_child. Expected: name, cpu, mem"}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
            return

        child_name = name_str_list[3]
        cpu_shares = int(name_str_list[4])
        mem_limit = name_str_list[5]

        try:
            client = docker.from_env()
            container = client.containers.run(
                image=TARGET_IMAGE,
                name=child_name,
                detach=True,
                cpu_shares=cpu_shares,
                mem_limit=mem_limit,
                restart_policy={"Name": "on-failure"} # 改良点: 異常終了時の自動再起動
            )
            res = {"status": "success", "message": f"Created container {child_name}", "container_id": container.short_id}
            app.put_data(name, content=json.dumps(res).encode(), freshness_period=1)
            logging.info(f"Successfully created container: {child_name}")
        except Exception as e:
            error_msg = {"status": "error", "message": str(e)}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
            logging.error(f"Failed to create container {child_name}: {e}")

    # ==========================================
    # 3. delete_child: 既存の子コンテナの削除【新規追記】
    # ==========================================
    elif operation == 'delete_child':
        if len(name_str_list) < 4:
            error_msg = {"status": "error", "message": "Missing container name for delete_child"}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
            return

        child_name = name_str_list[3]

        try:
            client = docker.from_env()
            container = client.containers.get(child_name)
            
            # 安全のため、停止させてから削除する
            logging.info(f"Stopping container: {child_name}")
            container.stop(timeout=5) 
            logging.info(f"Removing container: {child_name}")
            container.remove()

            res = {"status": "success", "message": f"Deleted container {child_name}"}
            app.put_data(name, content=json.dumps(res).encode(), freshness_period=1)
            logging.info(f"Successfully deleted container: {child_name}")
        except docker.errors.NotFound:
            error_msg = {"status": "error", "message": f"Container {child_name} not found"}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
            logging.warning(f"Delete failed: Container {child_name} not found")
        except Exception as e:
            error_msg = {"status": "error", "message": str(e)}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
            logging.error(f"Failed to delete container {child_name}: {e}")

    # ==========================================
    # 4. list: 稼働中の子コンテナ（Function群）の一覧返却【新規追記】
    # ==========================================
    elif operation == 'list':
        try:
            client = docker.from_env()
            # 特定のイメージ（TARGET_IMAGE）から起動しているコンテナのみを抽出
            containers = client.containers.list(filters={"ancestor": TARGET_IMAGE})
            
            # 各コンテナの名前と現在のステータス（runningなど）を取得
            function_list = [{"name": c.name, "status": c.status} for c in containers]
            
            payload = {
                "node_name": MY_NODE_NAME,
                "status": "success",
                "running_functions": function_list
            }
            app.put_data(name, content=json.dumps(payload).encode('utf-8'), freshness_period=1)
            logging.info(f"Responded to 'list' query. Found {len(function_list)} functions.")
        except Exception as e:
            error_msg = {"status": "error", "message": str(e)}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
            logging.error(f"Failed to fetch container list: {e}")

    # ==========================================
    # 不正な操作に対する例外処理
    # ==========================================
    else:
        error_msg = {"status": "error", "message": f"Unknown operation: {operation}"}
        app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
        logging.warning(f"Unknown operation requested: {operation}")

async def main():
    logging.info(f"Integrated Seed-Spy Agent process started on {MY_NODE_NAME}")
    await app.main_loop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Agent process stopped by user.")
        sys.exit(0)