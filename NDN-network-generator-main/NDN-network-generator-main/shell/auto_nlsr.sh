#!/bin/bash

# これは NLSR の設定ファイルのパスを元に、NLSR を起動し、設定ファイルに記載されている neighbor の情報を元に face を作成するスクリプトです。
# 環境変数 NLSR_CONFIG_FILE_PATH に NLSR の設定ファイルのパスを指定してください。

# もしNLSRの設定ファイルが存在しない場合はエラーを出力して終了
if [ ! -f "$NLSR_CONFIG_FILE_PATH" ]; then
  echo "NLSR configuration file not found. NLSR_CONFIG_FILE_PATH=$NLSR_CONFIG_FILE_PATH"
  exit 1
fi

# どこのファイルを参照するかを出力
echo "Using NLSR configuration file: $NLSR_CONFIG_FILE_PATH"

# nlsr.conf へのシンボリックリンクを作成
rm -f ./nlsr.conf
cp "$NLSR_CONFIG_FILE_PATH" /tmp/nlsr.conf

logfile="/tmp/nlsr_error.log"

# ログファイルを空にする
true > "$logfile"

# nlsr をバックグラウンドで実行し、エラーログを保存
nlsr -f /tmp/nlsr.conf > /dev/null 2> "$logfile" &
pid=$!

# 少し待機してプロセスが即時クラッシュしないか確認
sleep 3

# プロセスが生きているかチェック
if ! kill -0 $pid 2>/dev/null; then
  echo "Error: nlsr failed to start." >&2
  echo "==== Error Output ====" >&2
  cat "$logfile" >&2  # エラーログの内容を標準エラーに出力
  exit 1
fi

# Wait a moment to ensure nlsr has started
sleep 2

# Extract neighbor information and create faces
grep -A 3 "neighbor" "$NLSR_CONFIG_FILE_PATH" | while read -r line; do
  if echo "$line" | grep -q "face-uri "; then
    URI=$(echo "$line" | sed -n 's/.*face-uri \(.*\)/\1/p')
    echo "Creating face for $URI"
    nfdc face create "$URI" > /dev/null 2>&1 &
  fi
done

echo "All faces created."
