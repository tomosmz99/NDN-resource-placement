from typing import Callable, Optional
from ndn.app import NDNApp
from ndn.encoding import Name, InterestParam, BinaryStr, FormalName, MetaInfo
import os
import docker
import re
import psutil
import json  # リスト表示のためにjsonをインポート

class Manager:
    def __init__(self):
        self.app = NDNApp()
        
        #辞書型でfunctionやdataを保持する
        self.resource_lists = [
            {
                "user_id": "userA",
                "resources": ["/data/profile.txt", "/func/calc_sum"]
            },
            {
                "user_id": "userB",
                "resources": ["/data/photos/", "/func/get_location"]
            },
            {
                "user_id": "userC",
                "resources": [] # このユーザーは現在リソースを持っていません
            }
        ]

        self.producer_stats = {
            "producer_1":{"cpu_free": 1024, "mem_free": 2048}
        }

    

    def search_user_from_userid(self, user_id : str) -> bool:
        """
        指定されたユーザーIDがリストに存在するかを探索します。

        引数:
            user_id (str): 探索するユーザーID

        戻り値:
            bool: ユーザーが見つかればTrue、見つからなければFalse
        """
        for user_data in self.resource_lists:
            if user_data.get("user_id") == user_id:
                return True
        return False
    
    def search_resource_for_user(self, user_id: str, resource_item: str) -> bool:
        """
        指定されたユーザーのリソースリスト内に特定のリソースが存在するかを探索します。

        引数:
            user_id (str): リソースを探索するユーザーID
            resource_item (str): 探索するリソース項目

        戻り値:
            bool: 指定されたユーザーにリソースが見つかればTrue、見つからなければFalse
        """
        for user_data in self.resource_lists:
            if user_data.get("user_id") == user_id:
                if "resources" in user_data and resource_item in user_data["resources"]:
                    return True
                return False
        return False

    def search_resource_from_list(self, resource_name : str) -> bool:
        """
        指定されたリソース項目をシステム内のいずれかのユーザーが保持しているかを探索します。

        引数:
            resource_item (str): 探索するリソース項目

        戻り値:
            bool: 指定されたリソースを保持しているユーザーが一人でも見つかればTrue、
                  そうでなければFalse。
        """
        for user_data in self.resource_lists:
            if "resources" in user_data and resource_name in user_data["resources"]:
                return True # 一つでも見つかればTrueを返して終了
        return False # 全ユーザーを調べても見つからなかった場合
    
    def add_user(self, user_id : str) -> str:
        """
        新しいユーザーをリストに追加します。リソースリストは空で初期化されます。

        引数:
            user_id (str): 追加する新しいユーザーID

        戻り値:
            bool: 追加に成功すればTrue、ユーザーIDが既に存在すればFalse
        """
        if self.search_user_from_userid(user_id):
            print(f"エラー: ユーザーID '{user_id}' は既に起動しています。")
            return "Failed"
        
        new_user = {
            "user_id": user_id,
            "resources": []
        }
        self.resource_lists.append(new_user)
        return "Success"
    
    def add_resource_to_user(self, user_id : str, new_resource : str) -> str:
        """
        既存のユーザーのリソースリストに新しいリソース項目を追加します。

        引数:
            user_id (str): リソースを追加するユーザーID
            resource_item (str): 追加するリソース項目

        戻り値:
            bool: 追加に成功すればTrue、ユーザーが存在しないかリソースが重複していればFalse
        """
        for user_data in self.resource_lists:
            if user_data.get("user_id") == user_id:# userがすでに登録されている。
                if new_resource in user_data.get("resources",[]):
                    print(f"エラー: 該当ユーザーは'{new_resource}' を既に所持しています。")
                    return "Failed"
                if "resources" not in user_data:#バグを防ぐため、念のため、リソースリストが存在しない場合は空リストを作成する。
                    user_data["resources"] = []
                user_data["resources"].append(new_resource)
                return "Success"
            # userが起動していないとき
        print(f"ユーザー'{user_id}'は起動していません。")
        return "Failed"

    def remove_user(self, user_id : str) -> str:
        """
        ユーザーとそのリソース全体をシステムから削除（シャットダウン）します。

        引数:
            user_id (str): 削除するユーザーID

        戻り値:
            str: 成功すれば "Success"、ユーザーが見つからなければ "Failed"
        """
        for i, user_data in enumerate(self.resource_lists):# enumerateで辞書をindexと一緒に抜き出している。これにより、削除途中でインデックスずれによるエラーを防げる
            if user_data.get("user_id") == user_id:
                del self.resource_lists[i]
                return "Success"
        print(f"ユーザー'{user_id}'は起動されていません")
        return "Failed"
    
    def remove_resource_from_user(self, user_id : str, remove_resouce : str):
        """
        特定のユーザーが持つ特定のリソース項目のみを削除します。

        引数:
            user_id (str): リソースを削除するユーザーID
            resource_item (str): 削除するリソース項目

        戻り値:
            str: 成功すれば "Success"、ユーザーまたはリソースが見つからなければ "Failed"
        """
        for user_data in self.resource_lists:
            if user_data.get("user_id") == user_id:
                resources = user_data.get("resources", [])
                if resources is not None and remove_resouce in resources:# user_idに対応するリソースがNoneではなく、削除対象のリソースが存在するとき
                    resources.remove(remove_resouce)
                    return "Success"
                else:
                    print(f"該当ユーザーはそのリソースを持っていません")
                    return "Failed"
        print(f"該当ユーザー'{user_id}'は起動していません。")
        return "Failed"

    def _parse_memory_to_bytes(self, mem_str):
        """
        メモリ文字列("512m", "1g"等)を整数バイトに変換。
        コンテナ作成時に指定しているメモリ量が許容量を超えないかをチェックするために使用
        """
        matches = re.match(r"(\d+)([a-zA-Z]+)", mem_str)
        if not matches:
            return 512 * 1024 * 1024  # デフォルト
        value = int(matches.group(1))
        unit = matches.group(2).lower()
        if 'g' in unit: return value * 1024**3
        if 'm' in unit: return value * 1024**2
        if 'k' in unit: return value * 1024
        return value

    def create_container(self, interest_name, cpu_shares=1024, mem_limit="512m", service_prefix="/default"):
        """
        リソースチェックを行い、合格した場合のみ物理制限付きでコンテナを作成する。
        """
        client = docker.from_env()

        # 1. コンテナ名の抽出
        try:
            container_name = interest_name.split('/')[-1]
        except Exception as e:
            return False, f"Parsing error: {e}"

        # 2. ホストリソースの安全チェック (Managerによる判断)
        requested_bytes = self._parse_memory_to_bytes(mem_limit)
        host_available_bytes = psutil.virtual_memory().available
        threshold = host_available_bytes * 0.7  # ホスト空き容量の7割

        if requested_bytes > threshold:
            msg = f"Rejected: Request {mem_limit} exceeds 70% of available host memory."
            print(f"!! {msg}")
            return False, msg

        # 3. コンテナの作成と実行 (物理制限を適用)
        host_shared_dir = "/mnt/c/Users/tmkmi/masterlab/DockerPrac/work"
        container_mount_point = "/work"

        try:
            container = client.containers.run(
                image="dockerprac-ndn-producer", 
                name=container_name,
                detach=True,
                cpu_shares=cpu_shares,   # CPU優先度を適用
                mem_limit=mem_limit,     # メモリ最大許容量を適用
                network="dockerprac_ndn-network",
                volumes={
                    host_shared_dir: {
                        "bind": container_mount_point, 
                        "mode": "rw"
                    }
                },
                tty=True#ymalの"tty:true"に対応する部分
            )
            
            success_msg = f"Success! {container_name} is running (CPU:{cpu_shares}, Mem:{mem_limit})."
            print(success_msg)
            return True, success_msg

        except docker.errors.APIError as e:
            return False, f"Docker API Error: {e}"

    def stop_container(self, container_name):#おそらく使用しないが念のため
        """
        指定された名前のコンテナを停止し、削除する。
        """
        client = docker.from_env()
        try:
            # 1. 名前からコンテナオブジェクトを取得
            container = client.containers.get(container_name)
            
            # 2. 停止 (timeoutは秒単位。即座に停止させたい場合は 0)
            print(f"Stopping container: {container_name}...")
            container.stop(timeout=5)
            
            # 3. 削除 (コンテナのインスタンス自体を消す場合)
            print(f"Removing container: {container_name}...")
            container.remove()
            
            print(f"Success! {container_name} has been destroyed.")
            return True
            
        except docker.errors.NotFound:
            print(f"Error: Container '{container_name}' not found.")
            return False
        except docker.errors.APIError as e:
            print(f"Docker API Error during removal: {e}")
            return False

    def run(self, prefix: str, data_request_handler: Callable[[str], str]):
        """
        プレフィックスに対してデータハンドラを登録して起動
        Args:
            prefix (str): プレフィックス
            data_request_handler (Callable[[str], str]): データハンドラ (名前) -> データ
        """
        @self.app.route(prefix)
        def on_interest(name: FormalName, param: InterestParam, _app_param: Optional[BinaryStr]):
            str_name = Name.to_str(name)
            print(f'>> I: {str_name}')
            
            content = data_request_handler(str_name)
            content_bytes = content.encode('utf-8')
            
            self.app.put_data(name, content=content_bytes, freshness_period=1)
            print(f'<< D: {str_name} (Size: {len(content_bytes)})')
            print(MetaInfo(freshness_period=10000))
            print('')

        print(f"Manager started on {prefix}")
        self.app.run_forever()

    def on_interest(self, name: str) -> str:
        """
        Interest名に基づき、Managerの各種操作（search/add/delete）にルーティングします。
        
        想定されるInterest名:
        /manager/<operation>/<target>/<arg1>/<arg2...>
        例: /manager/add/resource/userA/data/contentA
        """
        original_interest = name# 念のためオリジナルを保存しておく。
        print(f"Interest : {original_interest}")

        cleaned_name = name.removeprefix('/manager')# 現時点では、とりあえずmanagerの名前をこれに固定する。宛先となるprefixの/managerをいったん消す。
        #例：/manager/data/sample.txtなら先頭のみが消え、/data/sample.txtとなる.先輩のやつ使えば改良できるかも？要検討。
        split_name = cleaned_name.strip('/').split('/') # 名前をスラッシュで分割
    # 例: "/user_info/userA" は ["user_info", "userA"] になる

        if len(split_name) < 2:#残りの要素に少なくとも「命令」「命令対象の種類」「具体名」が1つずつ含まれているか,またcreateの場合は最低2つの要素があるか
            return "Error: Invalid request format. Too few components."
        
        operation = split_name[0] # search, add, delete, create
        target_type = split_name[1]    # user, resource

        # --- ワーカーからのリソース広告 ---これはスパイがやるので後々削除
        # 形式: /manager/advertise/producer_1/1024/2048 (名前/CPU空き/Mem空き)
        if operation == 'advertise':
            worker_id = split_name[1]  # producer_1 など
            cpu_free = int(split_name[2])
            mem_free = int(split_name[3])
            
            self.worker_status[worker_id] = {
                "cpu_free": cpu_free,
                "mem_free": mem_free,
            }
            return f"ACK: {worker_id} status updated."

        if operation == 'create':
            # 形式: /manager/create/<container_name>/[cpu_shares]/[mem_limit]
            # 例: /manager/create/producer_1/512/256m
            
            target_name = split_name[1]
            
            # デフォルト値を定義
            shares = 1024
            memory = "512m"
            
            # Interestからパラメータを取得（あれば上書き）
            if len(split_name) >= 3:
                shares = int(split_name[2])
            if len(split_name) >= 4:
                memory = split_name[3]
            
            # コンテナ作成実行
            success, result = self.create_container(target_name, shares, memory)#successにはTrueやFalseが入る
            return result   

        if operation == 'search':
            if target_type == 'user':
                # 形式: /search/user/<user_id> (3コンポーネント)
                if len(split_name) != 3:
                    return "Error: Invalid search/user format. Expected 3 components."
                user_id = split_name[2]
                res = self.search_user_from_userid(user_id)
                # 結果をクライアントが解析しやすい形式で返す
                result = f"UserExists:{'True' if res else 'False'}"
            elif target_type == 'resource':
                # 形式: /search/resource/<resource_path...> (3コンポーネント以上)
                if len(split_name) < 3:
                    return "Error: Invalid search/resource format."
                
                # リソースパスを/から再構成 (インデックス2以降)
                resource_path = "/" + "/".join(split_name[2:])
                
                res = self.search_resource_from_list(resource_path)
                result = f"ResourceExists:{'True' if res else 'False'}"
        
        elif operation == 'add':
            if target_type == 'user':
                # 形式: /add/user/<user_id>
                if len(split_name) != 3:
                    return "Error: Invalid add/user format. Expected 3 components."
                user_id = split_name[2]
                result = self.add_user(user_id)

            elif target_type == 'resource':
                # 形式: /add/resource/<user_id>/<resource_name...> (4コンポーネント以上)
                if len(split_name) < 4:
                    return "Error: Invalid add/resource format. Expected at least 4 components."
                
                user_id = split_name[2]
                # リソースパスを/から再構成 (インデックス3以降)
                resource_path = "/" + "/".join(split_name[3:])
                result = self.add_resource_to_user(user_id, resource_path)

        elif operation == 'delete':
            if target_type == 'user':
                # 形式: /delete/user/<user_id>
                if len(split_name) != 3:
                    return "Error: Invalid delete/user format. Expected 3 components."
                user_id = split_name[2]
                result = self.remove_user(user_id)

            elif target_type == 'resource':
                # 形式: /delete/resource/<user_id>/<resource_name...> (4コンポーネント以上)
                if len(split_name) < 4:
                    return "Error: Invalid delete/resource format. Expected at least 4 components."  
                user_id = split_name[2]
                # リソースパスを/から再構成 (インデックス3以降)
                resource_path = "/" + "/".join(split_name[3:])
                result = self.remove_resource_from_user(user_id, resource_path)
            
        # --- 成功時のリスト表示 ---
        if operation in ['add', 'delete'] and result == 'Success':
            print("\n====================================")
            print(f"{operation.upper()} 完了: 現在のユーザーリスト")
            # json.dumpsで整形して出力
            print(json.dumps(self.resource_lists, indent=4, ensure_ascii=False))
            print("====================================\n")

        return result

if __name__ == '__main__':
    manager = Manager()
    manager.run('/manager', manager.on_interest)#/preiadesから始まるリクエスト(interest)が来た際に、on_interestを実行する
