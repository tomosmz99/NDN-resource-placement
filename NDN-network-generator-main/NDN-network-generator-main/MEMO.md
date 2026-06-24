config/functions 配下の、functionノード自体の名前と対応するファイルの exec を呼び出す
(k8sでconfigごとマウントして、そのファイルのエイリアスを作り、functionが呼び出しているファイルを消してそいつに変更する)

## NDN を適当に作る
docker pull hydrokhoos/ndn-all:arm
docker run -it hydrokhoos/ndn-all:arm
nfd-start

## ルートを確認
nlsrc routing

## NDN + NLSRの起動
```
# pip を変えてれば
pip install -r requirements.txt 

# 1
docker compose exec ndn-node-1 bash
./restart.sh
./auto_nlsr.sh 1

# 2
docker compose exec ndn-node-2 bash
./restart.sh
./auto_nlsr.sh 2
```

### 実行テスト(NDN tools)
```
# 1
echo 'Hello, world!' > /sample.txt
nlsrc advertise /sample.txt
ndnputchunks /sample.txt < /sample.txt

# 2
ndncatchunks /sample.txt
```

### 実行テスト(python package)
```
# 1
nlsrc advertise /example
python3 ./example/client_producer.py 

# 2
python3 ./example/client_consumer.py 
```


## ndndumpログ

```
1720069682.979047 IP 172.22.0.3 > 172.22.0.2, TCP, length 98, INTEREST: /ndn/waseda/%C1.Router/router1/nlsr/INFO/%07%20%08%03ndn%08%06waseda%08%08%C1.Router%08%07router2?CanBePrefix&MustBeFresh&Nonce=da7683e9&Lifetime=1000
1720069682.980428 IP 172.22.0.2 > 172.22.0.3, TCP, length 240, DATA: /ndn/waseda/%C1.Router/router1/nlsr/INFO/%07%20%08%03ndn%08%06waseda%08%08%C1.Router%08%07router2/v=1720069682979
1720069684.641264 IP 172.22.0.3 > 172.22.0.2, TCP, length 36, INTEREST: /sample.txt/32=metadata?CanBePrefix&MustBeFresh&Nonce=cc25c92f
1720069684.642755 IP 172.22.0.2 > 172.22.0.3, TCP, length 205, DATA: /sample.txt/32=metadata/v=1720069684642/seg=0
1720069684.643105 IP 172.22.0.3 > 172.22.0.2, TCP, length 35, INTEREST: /sample.txt/v=1720069638790/seg=1?Nonce=25a51ef5
1720069684.643569 IP 172.22.0.2 > 172.22.0.3, TCP, length 48, NDNLPv2, NACK (None): /sample.txt/v=1720069638790/seg=1?Nonce=25a51ef5
```

```1
ndndump: listening on eth0, link-type EN10MB (Ethernet)
1720069776.013066 IP 172.22.0.3 > 172.22.0.2, TCP, length 36, INTEREST: /sample.txt/32=metadata?CanBePrefix&MustBeFresh&Nonce=70dc1807
1720069776.015100 IP 172.22.0.2 > 172.22.0.3, TCP, length 203, DATA: /sample.txt/32=metadata/v=1720069776014/seg=0
1720069776.015906 IP 172.22.0.3 > 172.22.0.2, TCP, length 35, INTEREST: /sample.txt/v=1720069638790/seg=1?Nonce=89eada64
1720069776.016868 IP 172.22.0.2 > 172.22.0.3, TCP, length 48, NDNLPv2, NACK (None): /sample.txt/v=1720069638790/seg=1?Nonce=89eada64
```

```2
ndndump: listening on eth0, link-type EN10MB (Ethernet)
1720069776.013003 IP 172.22.0.3 > 172.22.0.2, TCP, length 36, INTEREST: /sample.txt/32=metadata?CanBePrefix&MustBeFresh&Nonce=70dc1807
1720069776.015144 IP 172.22.0.2 > 172.22.0.3, TCP, length 203, DATA: /sample.txt/32=metadata/v=1720069776014/seg=0
1720069776.015893 IP 172.22.0.3 > 172.22.0.2, TCP, length 35, INTEREST: /sample.txt/v=1720069638790/seg=1?Nonce=89eada64
1720069776.016881 IP 172.22.0.2 > 172.22.0.3, TCP, length 48, NDNLPv2, NACK (None): /sample.txt/v=1720069638790/seg=1?Nonce=89eada64
```