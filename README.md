# Bocchi Guitar Hub Server：自動楽曲解析技術に基づくギター練習支援システムのサーバサイド


このリポジトリはギター練習支援システムのサーバサイドです。
4つの楽曲解析WebAPIサーバと1つのメインWebAPiサーバ、プロキシサーバなどから構成されるマイクロサービスアーキテクチャに基づいた自動楽曲解析システムとなっています。
使用されたフレームワークや各コンポーネントは以下の通りになります。
- Fast API
- Kong OSS
- Redis


## アーキテクチャ図
掲載予定

## Docker-Composeを使用した起動方法
Docker Composeを用いた迅速なデプロイが可能となっています。

### 1. リポジトリをクローンする
```bash
git clone https://github.com/koki622/bocchi-guitar-hub-server.git
cd bocchi-guitar-hub-server/
```

### 2. Kongの宣言型設定ファイルを作成
```bash
cp ./kong/kong.yaml.example ./kong/kong.yaml
```
必要に応じて中身を修正してください。

### 3. Docker-Composeで起動
#### GPU環境で起動
```bash
docker-compose up docker-compose.yml
```
#### CPU(x86-64アーキテクチャ)環境で起動
```bash
docker-compose -f docker-compose.cpu.yml up
```

#### CPU(ARM64アーキテクチャ)環境で起動
```bash
docker-compose -f docker-compose.arm64.cpu.yml up
```
