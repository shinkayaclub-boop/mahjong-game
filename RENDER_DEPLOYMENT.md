# Renderへの移行手順

## 1. GitHubリポジトリの準備

### 1-1. Gitの初期化（まだの場合）

```bash
cd C:\Users\maxsp\Desktop\MahjongApp
git init
git add .
git commit -m "Initial commit for Render deployment"
```

### 1-2. GitHubにプッシュ

1. GitHub.comでアカウント作成（持っていない場合）
2. 新しいリポジトリを作成（例: mahjong-game）
3. ローカルからプッシュ：

```bash
git remote add origin https://github.com/YOUR_USERNAME/mahjong-game.git
git branch -M main
git push -u origin main
```

## 2. Renderでのデプロイ

### 2-1. Renderアカウント作成

1. https://render.com にアクセス
2. 「Get Started for Free」をクリック
3. GitHubアカウントで登録

### 2-2. Web Serviceの作成

1. Renderダッシュボードで「New +」→「Web Service」
2. GitHubリポジトリを接続
3. 設定：
   - **Name**: mahjong-game（任意）
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --worker-class eventlet -w 1 app:app`
   - **Plan**: Free

### 2-3. 環境変数の設定

Renderダッシュボードで以下を追加：

- `SECRET_KEY`: ランダムな文字列（例: your-secret-key-here）

### 2-4. デプロイ

「Create Web Service」をクリック

## 3. デプロイ後の確認

デプロイが完了すると、URLが発行されます：
`https://mahjong-game-XXXX.onrender.com`

このURLにアクセスして動作確認してください。

## 4. 次のステップ: Unity開発

Renderへの移行が完了したら、Unity + WebGLでの3D麻雀ゲーム開発に進みます。

### Unity開発の流れ：

1. Unityのインストール
2. 新規3Dプロジェクト作成
3. 麻雀卓と牌の3Dモデリング
4. テクスチャとマテリアルの設定
5. ゲームロジックの実装（C#）
6. WebSocketクライアントの実装
7. WebGLビルド
8. Renderサーバーとの統合

## トラブルシューティング

### デプロイが失敗する場合

- Renderのログを確認
- requirements.txtの内容を確認
- Pythonバージョンを確認

### WebSocketが動作しない場合

- Renderは自動的にWebSocketをサポート
- クライアント側のURLを確認（https://）
