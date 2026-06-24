import asyncio
import os
import random
from typing import Callable, Optional, List, Dict, Any
from ndn.app import NDNApp
from ndn.encoding import Name, InterestParam, BinaryStr, FormalName, Component
from ndn.types import InterestNack, InterestTimeout
import logging
import datetime
import mysql.connector
from mysql.connector import Error

from lib.ndn_utils import SEGMENT_SIZE, extract_first_level_args, extract_my_function_name, get_data, get_original_name, is_function_request

logging.basicConfig(format='[{asctime}]{levelname}:{message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    style='{')

class NDNFunction:
    """
    NDN 関数ノードを表すクラス。
    """
    def __init__(self):
        self.app = NDNApp()
        self.segmented_data = {}


    def run(self, prefix: str, function_request_handler: Callable[[str, List[bytes]], bytes], data_request_handler: Callable[[str], str]):
        """
        プレフィックスに対して関数ハンドラとデータハンドラを登録して起動。

        Args:
            prefix (str): プレフィックス。
            function_request_handler (Callable[[str, List[bytes]], bytes]): 関数ハンドラ (関数名, 引数) -> 結果。
            data_request_handler (Callable[[str], str]): データハンドラ (名前) -> データ。
        """

        @self.app.route(prefix)
        def on_interest(name: FormalName, param: InterestParam, _app_param: Optional[BinaryStr]):
            async def async_on_interest():
                nonce = param.nonce
                if nonce is None:
                    # Nonce がない場合は新しく生成
                    nonce = random.randint(0, 2**32 - 1)
                nonce_str = str(nonce)
                name_str = Name.to_str(name)
                
                original_name = get_original_name(name)

                # function リクエストでない場合は、データリクエストとして処理
                if not is_function_request(original_name):
                    content = data_request_handler(name_str)
                    content = content.encode()

                    # セグメント前のリクエストであれば、データを取得してセグメントに分割して保存しておく
                    if Component.get_type(name[-1]) != Component.TYPE_SEGMENT:
                        # データを取得
                        content = data_request_handler(Name.to_str(name))
                        content = content.encode()

                        # データをセグメントに分割する
                        seg_cnt = (len(content) + SEGMENT_SIZE - 1) // SEGMENT_SIZE

                        # パケット分割の時間を計測
                        packets = [self.app.prepare_data(original_name + [Component.from_segment(i)],
                                                    content[i*SEGMENT_SIZE:(i+1)*SEGMENT_SIZE],
                                                    freshness_period=10000,
                                                    final_block_id=Component.from_segment(seg_cnt - 1))
                                for i in range(seg_cnt)]
                        
                        # セグメントデータを保存
                        self.segmented_data[Name.to_str(original_name)] = packets
                        seg_no = 0
                    else:
                        seg_no = Component.to_number(name[-1])

                    print(f'<< D: {Name.to_str(name)}')

                    # セグメントデータを送信
                    self.app.put_raw_packet(self.segmented_data[Name.to_str(original_name)][seg_no])
                    return
                
                # function リクエストの場合
                # 処理前(セグメント分割前)のリクエストであれば、データを処理してセグメントに分割して保存しておく
                if Component.get_type(name[-1]) != Component.TYPE_SEGMENT:
                    # function リクエストの場合は、まず第一階層の引数を抽出
                    args = extract_first_level_args(name)

                    # 親の Nonce（受信した Interest の Nonce）
                    parent_nonce = nonce_str

                    # それぞれを Interest で並列でリクエストし、データを集める
                    async def fetch_content(arg, parent_nonce):
                        # 子の Nonce を生成(ここら辺はログで追跡する用なので実際の処理には関係ないです)
                        child_nonce = random.randint(0, 2**32 - 1)
                        child_nonce_str = str(child_nonce)

                        # Interest を送信
                        try:
                            return await get_data(self.app, arg, child_nonce_str)
                        except InterestNack as e:
                            logging.info(f'Nacked with reason={e.reason}')
                            return None
                        except InterestTimeout:
                            logging.info(f'Timeout for interest {arg}')
                            return None

                    tasks = [fetch_content(arg, parent_nonce) for arg in args]
                    contents = await asyncio.gather(*tasks)

                    logging.info(f"Data collected: {contents}")

                    # 関数名を取得
                    my_function_name = extract_my_function_name(name)

                    logging.info(f"Function name: {my_function_name}")

                    # 関数を実行
                    result = function_request_handler(my_function_name, contents)

                    logging.info(f"Processing result: {result}")

                    # データをセグメントに分割する
                    seg_cnt = (len(result) + SEGMENT_SIZE - 1) // SEGMENT_SIZE

                    print(f'segmentation count: {seg_cnt}')

                    # パケット分割の時間を計測
                    packets = [self.app.prepare_data(original_name + [Component.from_segment(i)],
                                                result[i*SEGMENT_SIZE:(i+1)*SEGMENT_SIZE],
                                                freshness_period=10000,
                                                final_block_id=Component.from_segment(seg_cnt - 1))
                            for i in range(seg_cnt)]
                    
                    # セグメントデータを保存
                    self.segmented_data[Name.to_str(original_name)] = packets
                    seg_no = 0
                else:
                    seg_no = Component.to_number(name[-1])

                # セグメントデータを送信
                self.app.put_raw_packet(self.segmented_data[Name.to_str(original_name)][seg_no])
                return

            # イベントループで実行
            asyncio.create_task(async_on_interest())
        self.app.run_forever()

    def shutdown(self):
        """
        アプリケーションとデータベース接続を閉じる。
        """
        self.app.shutdown()

def function_request_handler(name: str, args: List[bytes]) -> bytes:
    """
    関数リクエストを処理するハンドラ。

    Args:
        name (str): 関数名。
        args (List[bytes]): 引数のリスト。

    Returns:
        bytes: 関数の実行結果。
    """
    args_decoded = [arg.decode() for arg in args if arg is not None]
    args_str = ",".join(args_decoded)
    return f"Hello, {name}! Args: {args_str}".encode()

def data_request_handler(name: str) -> str:
    """
    データリクエストを処理するハンドラ。

    Args:
        name (str): データ名。

    Returns:
        str: データの内容。
    """
    logging.info(f"Data requested for: {name}")
    return "Hello, world!"

if __name__ == '__main__':
    try:
        producer = NDNFunction()
        producer.run('/func_nodeX', function_request_handler, data_request_handler)
    except KeyboardInterrupt:
        logging.info("Application interrupted by user.")
    finally:
        producer.shutdown()
