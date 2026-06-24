#!/bin/bash
# NFDの起動
nfd-start
sleep 2

# seed と spy_agent をバックグラウンドで実行
python3 /usr/local/bin/seed.py &
python3 /usr/local/bin/spy_agent.py &

# いずれかのプロセスが終了したらコンテナを終了させる
wait -n
exit $?