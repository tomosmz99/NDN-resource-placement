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

# 環境変数からの静的情報の取得（C++側とも共通化する環境変数）
MY_NODE_NAME = os.environ.get("NODE_NAME", "node_1")
CPU_MODEL = os.environ.get("CPU_MODEL", "Intel Core i7-2026")
PASSMARK = int(os.environ.get("PASSMARK", "12000"))
MAX_MEM = int(os.environ.get("MAX_MEM", "4096"))  # MB単位

# 管理対象（子コンテナ）とするDockerイメージ名
TARGET_IMAGE = "dockerprac-ndn-worker-task"

def get_dynamic_resource():
    """親コンテナ自身の動的リソース情報を取得"""
    cpu_usage = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    mem_usage = mem.percent
    return cpu_usage, mem_usage

# URI: /node/{MY_NODE_NAME}/agent で待ち受け
@app.route(f'/node/{MY_NODE_NAME}/agent')
def on_agent_interest(name, interest_param, app_param):
    # NDNの名前を文字列のリストに変換
    name_str_list = [Component.to_str(c) for c in name]
    
    # [0]=node, [1]={MY_NODE_NAME}, [2]=agent, [3]=operation (resource, create, delete, list)
    operation = name_str_list[3] if len(name_str_list) > 3 else "list"

    logging.info(f"💡 [Python Agent] Received operation: {operation}")

    # -------------------------------------------------------------------------
    # 1. resource (旧spy機能): リソース監視とスコア計算
    # -------------------------------------------------------------------------
    if operation == 'resource':
        cpu, mem = get_dynamic_resource()
        availability = (100.0 - cpu) / 100.0
        score = int(PASSMARK * availability)
        
        payload = {
            "status": "success",
            "node_name": MY_NODE_NAME,
            "cpu_usage": f"{cpu}%",
            "memory_usage": f"{mem}%",
            "score": score
        }
        app.put_data(name, content=json.dumps(payload).encode('utf-8'), freshness_period=1)

    # -------------------------------------------------------------------------
    # 2. create (旧seed機能): 子コンテナの生成
    # -------------------------------------------------------------------------
    elif operation == 'create':
        if len(name_str_list) < 7: # /node/{NM}/agent/create/{name}/{cpu}/{mem} で7要素
            error_msg = {"status": "error", "message": "Missing arguments for create. Expected: name, cpu, mem"}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
            return

        child_name = name_str_list[4]
        cpu_shares = int(name_str_list[5])
        mem_limit = name_str_list[6]

        try:
            client = docker.from_env()
            container = client.containers.run(
                image=TARGET_IMAGE,
                name=child_name,
                detach=True,
                cpu_shares=cpu_shares,
                mem_limit=mem_limit,
                restart_policy={"Name": "on-failure"}
            )
            res = {"status": "success", "message": f"Created container {child_name}", "container_id": container.short_id}
            app.put_data(name, content=json.dumps(res).encode(), freshness_period=1)
        except Exception as e:
            error_msg = {"status": "error", "message": str(e)}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)

    # -------------------------------------------------------------------------
    # 3. delete (旧seed機能): 子コンテナの削除
    # -------------------------------------------------------------------------
    elif operation == 'delete':
        if len(name_str_list) < 5: # /node/{NM}/agent/delete/{name} で5要素
            error_msg = {"status": "error", "message": "Missing container name for delete"}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
            return

        child_name = name_str_list[4]

        try:
            client = docker.from_env()
            container = client.containers.get(child_name)
            container.stop(timeout=5) 
            container.remove()

            res = {"status": "success", "message": f"Deleted container {child_name}"}
            app.put_data(name, content=json.dumps(res).encode(), freshness_period=1)
        except docker.errors.NotFound:
            error_msg = {"status": "error", "message": f"Container {child_name} not found"}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)
        except Exception as e:
            error_msg = {"status": "error", "message": str(e)}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)

    # -------------------------------------------------------------------------
    # 4. list (旧seed機能): 稼働中の子コンテナ一覧
    # -------------------------------------------------------------------------
    elif operation == 'list':
        try:
            client = docker.from_env()
            containers = client.containers.list(filters={"ancestor": TARGET_IMAGE})
            function_list = [{"name": c.name, "status": c.status} for c in containers]
            
            payload = {
                "status": "success",
                "node_name": MY_NODE_NAME,
                "running_functions": function_list
            }
            app.put_data(name, content=json.dumps(payload).encode('utf-8'), freshness_period=1)
        except Exception as e:
            error_msg = {"status": "error", "message": str(e)}
            app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)

    # -------------------------------------------------------------------------
    # 例外: 未知のオペレーション
    # -------------------------------------------------------------------------
    else:
        error_msg = {"status": "error", "message": f"Unknown operation: {operation}"}
        app.put_data(name, content=json.dumps(error_msg).encode(), freshness_period=1)

async def main():
    logging.info(f"🚀 Python Integrated Agent started on prefix: /node/{MY_NODE_NAME}/agent")
    await app.main_loop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Agent stopped.")
        sys.exit(0)