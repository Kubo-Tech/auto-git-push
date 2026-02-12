# auto-git-push

## 概要

`auto-git-push`は、ディレクトリの変更を検知して自動でGitリポジトリへcommit & pushを行うライブラリです。

ファイル監視には[watchdog](https://github.com/gorakhargosh/watchdog)を使用し、変更検知後に一定時間待機してからgitコマンドを実行します。重複イベントの抑制や、カスタマイズ可能なコミットメッセージ生成にも対応しています。


## 動作要件

- Python 3.12以上
- Git（CLIが利用可能であること）


## 依存パッケージ

- [watchdog](https://github.com/gorakhargosh/watchdog) >= 3.0.0
- [python-dotenv](https://github.com/theskumar/python-dotenv) >= 1.0.0


## インストール

```bash
pip install -e /path/to/auto-git-push
```


## セットアップ

### .envファイルによる設定（デフォルト）

`.env.example`をコピーして`.env`を作成し、値を設定してください。

```bash
cp .env.example .env
```

```env
AUTO_GIT_PUSH_WATCH_DIR=/path/to/watch
AUTO_GIT_PUSH_GIT_REPO_DIR=/path/to/git/repo
AUTO_GIT_PUSH_PUSH_DIR=.
AUTO_GIT_PUSH_BRANCH=main
AUTO_GIT_PUSH_DELAY_SECONDS=30
AUTO_GIT_PUSH_IGNORE_SECONDS=5
```

| 環境変数 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `AUTO_GIT_PUSH_WATCH_DIR` | ○ | - | 監視対象のディレクトリパス |
| `AUTO_GIT_PUSH_GIT_REPO_DIR` | ○ | - | 自動push対象のGitリポジトリのルートディレクトリパス |
| `AUTO_GIT_PUSH_PUSH_DIR` | - | `.` | git addするディレクトリ（リポジトリからの相対パス） |
| `AUTO_GIT_PUSH_BRANCH` | - | `main` | プッシュ先のブランチ名 |
| `AUTO_GIT_PUSH_DELAY_SECONDS` | - | `30` | 変更検知後のコミットまでの待機時間（秒） |
| `AUTO_GIT_PUSH_IGNORE_SECONDS` | - | `5` | 重複イベント無視の閾値（秒） |


## 使い方

### .envから設定を読み込む場合

```python
import logging

from auto_git_push import AutoGitPushConfig, AutoGitPusher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("my_app")

config = AutoGitPushConfig.from_env()
pusher = AutoGitPusher(config, logger=logger)
pusher.start()  # Ctrl+Cで停止
```

### Pythonスクリプト上で設定を直接指定する場合

```python
import logging

from auto_git_push import AutoGitPushConfig, AutoGitPusher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("my_app")

config = AutoGitPushConfig(
    watch_dir="/path/to/watch",
    git_repo_dir="/path/to/git/repo",
    push_dir="public",
    branch="main",
    delay_seconds=30,
    ignore_seconds=5,
)
pusher = AutoGitPusher(config, logger=logger)
pusher.start()
```

### コミットメッセージをカスタマイズする場合

```python
from datetime import datetime

from auto_git_push import AutoGitPushConfig

config = AutoGitPushConfig(
    watch_dir="/path/to/watch",
    git_repo_dir="/path/to/git/repo",
    commit_message_fn=lambda: f"[auto] {datetime.now().strftime('%H:%M')} 自動プッシュ",
)
```


## エラーハンドリング

本ライブラリが送出する例外は全て`AutoGitPushError`を基底クラスとしています：

| 例外クラス | 説明 |
|---|---|
| `AutoGitPushError` | 基底例外クラス |
| `GitCommandError` | gitコマンドの実行に失敗した場合 |
| `ConfigError` | 設定値が不正な場合 |

