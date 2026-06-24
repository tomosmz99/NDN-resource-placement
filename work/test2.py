import sys

name = sys.argv[1]

url_content = input("URL形式のコンテンツ名を入力してください（例: /manager/data/sample.txt）: ")
cleaned_name = url_content.removeprefix(name)
print(f"処理後のコンテンツ名: {cleaned_name}")