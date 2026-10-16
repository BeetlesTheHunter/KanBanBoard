#KanBan Board

軽量かつリアルタイムなカンバン／ブレインストーミング用ボードです。ローカル開発に特化した設計を採用しており、複雑なビルド手順やNode.jsの依存関係、データベースのセットアップは一切不要。純粋なPythonとJavaScriptのみで構成されています。


## 機能

* **無限の自由形式キャンバス:** ボード上の好きな場所に、インタラクティブな付箋をドラッグ＆ドロップで配置できます。
* **糸（コネクティング・ライン）:** 関連するメモ同士を、動的かつ自動更新されるSVGラインで視覚的につなぐことができます。
* **軽量スタンプライブラリ:** メモリ消費を抑えた効率的なライブラリを活用し、カードにステータスを示すスタンプ（✅、❌、⚠️、🔍）を素早く追加できます。
* **リアルタイム・コラボレーション:** 「スプリットステート・ハートビート・ロック」技術により、複数ユーザー間での同期を実現。誰かがカードを編集・移動している間は、そのカードが即座にロックされるため、データ競合を防ぐことができます。

## 技術スタック

* **バックエンド:** Python 3.11+、Fas​​tAPI、Uvicorn
* **フロントエンド:** HTML5 Canvas/SVG、Vanilla JavaScript、Tailwind CSS（CDN経由）
* **並行処理:** Python標準の `asyncio.Queue` を用いたバックグラウンドワーカーによるFIFOパイプライン処理。
* **永続状態:** バックグラウンドワーカーのみが操作する単一の `state.json` ファイル（ファイルI/Oロックを回避）。

##  ローカルクイックスタート

**1. リポジトリをクローンします：**
```bash
git clone https://github.com/BeetlesTheHunter/KanBanBoard
```

**2. 仮想環境を作成し、有効化する：**

*Linux / Mac:*
```bash
python3 -m venv venv
source venv/bin/activate
```

*Windows:*
```cmd
python -m venv venv
venv\Scripts\activate
```

**3. 依存関係をインストールする:**
このプロジェクトでは、FastAPIとUvicornが必要です。仮想環境が有効になっていることを確認した上で、ターミナルからこれらをインストールしてください。
```bash
pip install -r requirements.txt
```

**4. サーバーを起動する：**
```bash
uvicorn main:app --reload --port 8000
```

**5. Webアプリへのアクセス**
Webブラウザで `http://localhost:8000` にアクセスしてください。


# KanBan Board

A lightweight, real-time Kanban and brainstorming board built entirely in a single file. Designed with a strict local-development paradigm, this project eliminates complex build steps, node dependencies, and database setups in favor of raw Python and Vanilla JavaScript.

##  Features

* **Infinite Free-Form Canvas:** Drag and drop interactive sticky notes anywhere on the board.
* **Detective Strings:** Visually connect related cards with dynamic, auto-updating SVG lines.
* **Flyweight Stamp Library:** Quickly mark cards with status indicators (✅, ❌, ⚠️, 🔍) using a centralized, low-memory asset library.
* **Real-Time Collaboration:** Multi-user synchronization using a split-state heartbeat lock. If a user is actively editing or dragging a card, it is instantly locked for everyone else to prevent data collisions.
* **Pass-Through Authentication:** Frictionless entry. No passwords or registration—just enter a detective name and join the board.

##  Architecture & Tech Stack

* **Backend:** Python 3.11+, FastAPI, Uvicorn
* **Frontend:** HTML5 Canvas/SVG, Vanilla JavaScript, Tailwind CSS (via CDN)
* **Concurrency:** Native Python `asyncio.Queue` background worker processing a FIFO pipeline.
* **Persistent State:** A single `state.json` file handled exclusively by the background worker to eliminate file I/O locks.


##  Local Quick Start

**1. Clone the repository:**
```bash
git clone https://github.com/BeetlesTheHunter/KanBanBoard
```

**2. Create and activate a Virtual Environment:**

*Linux / Mac:*
```bash
python3 -m venv venv
source venv/bin/activate
```

*Windows:*
```cmd
python -m venv venv
venv\Scripts\activate
```

**3. Install Dependencies:**
This project requires FastAPI and Uvicorn. Ensure your virtual environment is activated, then install them via the terminal:
```bash
pip install -r requirements.txt
```

**4. Launch the Server:**
```bash
uvicorn main:app --reload --port 8000
```

**5. Open the Board:**
Navigate to `http://localhost:8000` in your web browser. 
*(Pro-tip: Open a second Incognito/Private window to the same address to easily simulate multi-user collaboration and test the locking mechanisms!)*
