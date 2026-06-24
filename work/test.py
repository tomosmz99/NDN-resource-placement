class UserManager:
    def __init__(self):
        self.lists = [
            {
                "user_id": "userA",
                "resources": ["/data/profile.txt", "/func/calc_sum/"]
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

    def search_user_from_userid(self, user_id : str) -> bool:
        """
        指定されたユーザーIDがリストに存在するかを探索します。

        引数:
            user_id (str): 探索するユーザーID

        戻り値:
            bool: ユーザーが見つかればTrue、見つからなければFalse
        """
        for user_data in self.lists:
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
        for user_data in self.lists:
            if user_data.get("user_id") == user_id:
                if "resources" in user_data and resource_item in user_data["resources"]:
                    return True
                return False
        return False

    def search_data_from_list(self, resource_name : str) -> bool:
        """
        指定されたリソース項目をシステム内のいずれかのユーザーが保持しているかを探索します。

        引数:
            resource_item (str): 探索するリソース項目

        戻り値:
            bool: 指定されたリソースを保持しているユーザーが一人でも見つかればTrue、
                  そうでなければFalse。
        """
        for user_data in self.lists:
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
        self.lists.append(new_user)
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
        for user_data in self.lists:
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
        for i, user_data in enumerate(self.lists):# enumerateで辞書をindexと一緒に抜き出している。これにより、削除途中でインデックスずれによるエラーを防げる
            if user_data.get("user_id") == user_id:
                del self.lists[i]
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
        for user_data in self.lists:
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

if __name__ == '__main__':
    manager = UserManager()
    import json
    
    # 準備: userDを追加し、userAに新しいリソースを追加
    manager.add_user('userD')
    manager.add_resource_to_user('userA', '/data/new_doc.txt')
    manager.add_resource_to_user('userD', '/func/delete_item')
    
    print("\n--- 初期リスト（削除前） ---")
    print(json.dumps(manager.lists, indent=4))
    print("-" * 30)

    # --- ユーザーの削除テスト ---
    print("\n--- ユーザーの削除（シャットダウン） ---")
    
    # userDの削除テスト
    result_remove_d = manager.remove_user('userD')
    print(f"'userD'の削除: {result_remove_d}")
    
    # 存在しないユーザーの削除テスト
    result_remove_z = manager.remove_user('userZ')
    print(f"'userZ'の削除: {result_remove_z}")
    print("-" * 30)
    
    print("\n--- リスト中間確認（userDが消えているはず） ---")
    print(json.dumps(manager.lists, indent=4))
    print("-" * 30)

    # --- 特定リソースの削除テスト ---
    print("\n--- 特定リソースの削除 ---")
    
    # userAからリソースを削除（成功）
    result_remove_res_a1 = manager.remove_resource_from_user('userA', '/data/profile.txt')
    print(f"'userA'から'/data/profile.txt'の削除: {result_remove_res_a1}")
    
    # userBから存在しないリソースを削除（失敗）
    result_remove_res_b1 = manager.remove_resource_from_user('userB', '/data/non_existent')
    print(f"'userB'から'/data/non_existent'の削除: {result_remove_res_b1}")
    
    # 存在しないユーザーからリソースを削除（失敗）
    result_remove_res_z2 = manager.remove_resource_from_user('userZ', '/func/test')
    print(f"'userZ'からリソースを削除: {result_remove_res_z2}")
    print("-" * 30)

    print("\n--- 最終的なリスト ---")
    print(json.dumps(manager.lists, indent=4))
    print("-" * 30)


    ###以下メモ
    """
    if (split_name[0] == 'user_info'): # 最初の要素が'user_info'の場合
            if len(split_name) > 1: # user_idがあることを確認
                user_id = split_name[1] # 2番目の要素をuser_idとして取得
                return f"{self.search_user_from_userid(user_id)}"
        elif(split_name[0] == 'data' or split_name[0] == 'func'):
            if (len(split_name) > 1):
                return f"{self.search_resource_from_list(cleaned_name)}"# cleaned_nameが先のようになったので、list内のリソースと一致するかを見ればよい。
        return "Error: Unrecognized interest name format." # 条件に合わない場合やユーザーが見つからない場合はNoneを返す
    """