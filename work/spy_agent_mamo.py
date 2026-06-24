import os
import sys
import json
import logging
import asyncio
import random
import docker  # 親コンテナの内部から、自身の中(子コンテナ)を操作するために使用
import psutil
from ndn.app import NDNApp
from ndn.encoding import Name, Component

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = NDNApp()

# =================================================================
# (1) スパイが親コンテナから静的性能（環境変数）を取得するロジック
# =================================================================
MY_NODE_NAME = os.environ.get("NODE_NAME", "unknown_node")
CPU_MODEL = os.environ.get("CPU_MODEL", "Generic CPU")
PASSMARK = int(os.environ.get("PASSMARK", "10000"))
GPU_SCORE = int(os.environ.get("GPU_SCORE", "0"))
MAX_MEM = int(os.environ.get("MAX_MEM", "8192"))  # MB単位
TDP = int(os.environ.get("TDP", "45"))

def generate_background_resource(tdp):
    """親コンテナ内部の現在の疑似的な背景負荷を計算"""
    real_cpu = psutil.cpu_percent(interval=None)
    
    if tdp <= 15:
        usage_cpu = max(real_cpu, random.uniform(30.0, 70.0))
        usage_mem = random.uniform(40.0, 60.0)
    elif tdp <= 60:
        usage_cpu = max(real_cpu, random.uniform(15.0, 45.0))
        usage_mem = random.uniform(20.0, 50.0)
    else:
        usage_cpu = max(real_cpu, random.uniform(5.0, 25.0))
        usage_mem = random.uniform(10.0, 30.0)
    return usage_cpu, usage_mem


# /spy/producer_1 のような個別Prefixで待ち受ける
@app.route(f'/spy/{MY_NODE_NAME}')
def on_spy_interest(name, interest_param, app_param):
    name_str_list = [Component.to_str(c) for c in name]
    
    # 処理のルーティング分岐
    # 構造: ['spy', 'producer_1', 'resource' または 'create_child']
    operation = name_str_list[2] if len(name_str_list) > 2 else ""

    # -------------------------------------------------------------
    # 機能①: Manager（またはクライアント）へのリソース状態の返答
    # -------------------------------------------------------------
    if operation == 'resource':
        logging.info(f"📥 リソース照会 Interest受信")
        try:
            usage_cpu, usage_mem = generate_background_resource(TDP)
            availability = (100.0 - usage_cpu) / 100.0
            
            score_no_tdp = int(PASSMARK * availability)
            score_with_tdp = int((PASSMARK / TDP) * availability)
            
            response_payload = {
                "node_name": MY_NODE_NAME,
                "cpu_model": CPU_MODEL,
                "cpu_performance": PASSMARK,
                "gpu_performance": GPU_SCORE,
                "max_memory": MAX_MEM,
                "cpu_usage": f"{usage_cpu:.1f}%",
                "memory_usage": f"{usage_mem:.1f}%",
                "score_no_tdp": score_no_tdp,
                "score_with_tdp": score_with_tdp
            }
            
            data_bytes = json.dumps(response_payload).encode('utf-8')
            app.put_data(name, content=data_bytes, freshness_period=1)
            logging.info(f"📤 Data送信完了 (スコア: {score_no_tdp})")
        except Exception as e:
            logging.error(f"Resource response error: {e}")

    # -------------------------------------------------------------
    # 機能②: Managerの指示の元、親コンテナ内部で「子コンテナ」を起動する
    # -------------------------------------------------------------
    elif operation == 'create_child':
        # 形式: /spy/producer_1/create_child/<child_container_name>/<cpu_shares>/<mem_limit>
        # インデックス対応: [2]='create_child', [3]=child_name, [4]=cpu_shares, [5]=mem_limit
        if len(name_str_list) < 6:
            app.put_data(name, content=b"Error: Too few components for child creation", freshness_period=1)
            return

        child_name = name_str_list[3]
        cpu_shares = int(name_str_list[4])
        mem_limit = name_str_list[5] # 例: "256m"

        logging.info(f"📥 子コンテナ作成指示を受信: {child_name} (CPU:{cpu_shares}, Mem:{mem_limit})")

        try:
            client = docker.from_env()
            
            # 親コンテナの中にタスク処理用子コンテナを生成・起動
            container = client.containers.run(
                image="dockerprac-ndn-worker-task", # 子コンテナ用の軽量イメージ
                name=child_name,
                detach=True,
                cpu_shares=cpu_shares,   # Managerから指定された物理制限を適用
                mem_limit=mem_limit,     # Managerから指定された物理制限を適用
                tty=True
            )
            
            success_msg = f"Success: {child_name} is running inside {MY_NODE_NAME}."
            logging.info(f"   {success_msg}")
            app.put_data(name, content=success_msg.encode('utf-8'), freshness_period=1)

        except Exception as e:
            err_msg = f"Child Container Creation Failed: {e}"
            logging.error(err_msg)
            app.put_data(name, content=err_msg.encode('utf-8'), freshness_period=1)


async def main():
    if MY_NODE_NAME == "unknown_node":
        logging.error("エラー: 環境変数 'NODE_NAME' が設定されていません。")
        sys.exit(1)

    logging.info("========================================================")
    logging.info(f"🤖 Spy Agent [コンテナinコンテナ対応版] 起動完了")
    logging.info(f"  - 担当仮想マシン: {MY_NODE_NAME}")
    logging.info(f"  - 設定スペック: {CPU_MODEL} (Passmark: {PASSMARK})")
    logging.info(f"  - 監視Prefix: /spy/{MY_NODE_NAME}")
    logging.info("========================================================")
    
    await app.main_loop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Spy Agent を停止しました。")
    finally:
        app.shutdown()