# NDN-FC WorkflowPlus python実装版

NDN-FC workflow+ を python で実装したものとなります。

## 仕組みなど

[解説スライド](https://docs.google.com/presentation/d/1QKP5_N0ExrEn8PfivQ4KW6YzeGq4XjVVZ4nBeVsLEmQ/edit?usp=sharing)の28ページがわかりやすいです。

要するに function クライアントのみが頑張ればいいだけなので、NDNネットワークを作って `function_sample.py` のような実装をしたノードをネットワーク内に配置してあげれば動きます。

(もちろん経路広告などは必要です。経路広告やネットワークの構成など、そこらへんまとめてやってほしい場合は[こちら](https://github.com/kobayashiharuto/NDN-network-generator/tree/k2sw)のネットワークジェネレータでどうぞ。)

## 使い方

### 1. NDNネットワークの準備

まずは function ノードに NDN 関連ツールを導入して、NFDをスタートしておきます。

```
nfd-start > $LOG_FILE
```

### 2. 依存関係のインストール

```
pip install -r requirements.txt
```

### 3. 経路を NDN ネットワークに広告しておきます

nlsrc でもなんでもいいのでとりあえず経路を広告しておきましょう

### 4. function を起動する

3 で登録した prefix を function に提供して起動しましょう。

/funcA だとしたら以下の感じ。

```
python function_sample.py /funcA
```

### 5. リクエストする

あとはこの prefix に対してリクエストすれば動きます。

```
ndncatchunks /funcA/(/dataB, /dataC)
```
