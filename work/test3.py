class ResourceManager:
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
                "resources": []  # このユーザーは現在リソースを持っていません
            }
        ]

    def find_user(self, user_id: str) -> bool:
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

    def find_resource_for_user(self, user_id: str, resource_item: str) -> bool:
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

    def find_resource_globally(self, resource_item: str) -> bool:
        """
        指定されたリソース項目をシステム内のいずれかのユーザーが保持しているかを探索します。

        引数:
            resource_item (str): 探索するリソース項目

        戻り値:
            bool: 指定されたリソースを保持しているユーザーが一人でも見つかればTrue、
                  そうでなければFalse。
        """
        for user_data in self.lists:
            if "resources" in user_data and resource_item in user_data["resources"]:
                return True # 一つでも見つかればTrueを返して終了
        return False # 全ユーザーを調べても見つからなかった場合

# --- 関数の使用例 ---
if __name__ == "__main__":
    manager = ResourceManager()

    print("--- ユーザーの探索 ---")
    print(f"'userA'は見つかりますか？ {manager.find_user('userA')}")
    print(f"'userD'は見つかりますか？ {manager.find_user('userD')}")
    print("-" * 30)

    print("\n--- ユーザー内の特定リソース探索 ---")
    print(f"'userA'は'/data/profile.txt'を持っていますか？ {manager.find_resource_for_user('userA', '/data/profile.txt')}")
    print(f"'userB'は'/func/get_location'を持っていますか？ {manager.find_resource_for_user('userB', '/func/get_location')}")
    print("-" * 30)

    print("\n--- システム全体でのリソースの存在確認 ---")
    # '/data/profile.txt'が存在するかどうか
    has_profile_txt = manager.find_resource_globally('/data/profile.txt')
    print(f"'/data/profile.txt'はシステム内に存在しますか？ {has_profile_txt}")

    # '/func/get_location'が存在するかどうか
    has_location_func = manager.find_resource_globally('/func/get_location')
    print(f"'/func/get_location'はシステム内に存在しますか？ {has_location_func}")

    # 存在しないリソースが存在するかどうか
    has_non_existent_resource = manager.find_resource_globally('/data/non_existent.jpg')
    print(f"'/data/non_existent.jpg'はシステム内に存在しますか？ {has_non_existent_resource}")
    print("-" * 30)