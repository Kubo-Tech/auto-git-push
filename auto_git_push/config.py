"""設定モジュール.

AutoGitPusherの設定をdataclassで定義する。
デフォルトでは.envファイルから設定を読み込む。
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from dotenv import load_dotenv

from auto_git_push.exceptions import ConfigError

# デフォルトのコミットメッセージ生成関数
_DEFAULT_COMMIT_MESSAGE_FN: Callable[[], str] = lambda: (
    f"{datetime.now().strftime('%Y-%m-%d %H:%M')} auto push"
)


@dataclass(frozen=True)
class AutoGitPushConfig:
    """AutoGitPusherの設定.

    Attributes:
        watch_dir: 監視対象のディレクトリパス
        git_repo_dir: Gitリポジトリのルートディレクトリパス
        push_dir: git addするディレクトリ（git_repo_dirからの相対パス）
        branch: プッシュ先のブランチ名
        delay_seconds: 変更検知後のコミットまでの待機時間（秒）
        ignore_seconds: 直近の変更から何秒以内のイベントを無視するか
        commit_message_fn: コミットメッセージを生成するコールバック関数
    """

    watch_dir: str
    git_repo_dir: str
    push_dir: str = "."
    branch: str = "main"
    delay_seconds: int = 30
    ignore_seconds: int = 5
    commit_message_fn: Callable[[], str] = field(default=_DEFAULT_COMMIT_MESSAGE_FN)

    def __post_init__(self) -> None:
        """設定値のバリデーションを行う.

        Raises:
            ConfigError: 設定値が不正な場合
        """
        if not self.watch_dir:
            raise ConfigError("watch_dir は必須です")
        if not self.git_repo_dir:
            raise ConfigError("git_repo_dir は必須です")
        if self.delay_seconds < 0:
            raise ConfigError("delay_seconds は0以上の整数を指定してください")
        if self.ignore_seconds < 0:
            raise ConfigError("ignore_seconds は0以上の整数を指定してください")

    @classmethod
    def from_env(cls, env_path: str | None = None) -> "AutoGitPushConfig":
        """環境変数から設定を読み込む.

        .envファイルから以下の環境変数を読み込む:
        - AUTO_GIT_PUSH_WATCH_DIR: 監視対象ディレクトリ（必須）
        - AUTO_GIT_PUSH_GIT_REPO_DIR: Gitリポジトリディレクトリ（必須）
        - AUTO_GIT_PUSH_PUSH_DIR: git addするディレクトリ（デフォルト: "."）
        - AUTO_GIT_PUSH_BRANCH: ブランチ名（デフォルト: "main"）
        - AUTO_GIT_PUSH_DELAY_SECONDS: 待機時間（デフォルト: 30）
        - AUTO_GIT_PUSH_IGNORE_SECONDS: 無視時間（デフォルト: 5）

        Args:
            env_path: .envファイルのパス。Noneの場合はカレントディレクトリの.envを使用

        Returns:
            AutoGitPushConfig: 設定インスタンス

        Raises:
            ConfigError: 必須の環境変数が未設定の場合
        """
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        watch_dir = _load_env_str("AUTO_GIT_PUSH_WATCH_DIR")
        git_repo_dir = _load_env_str("AUTO_GIT_PUSH_GIT_REPO_DIR")

        if not watch_dir:
            raise ConfigError("環境変数 AUTO_GIT_PUSH_WATCH_DIR が設定されていません")
        if not git_repo_dir:
            raise ConfigError("環境変数 AUTO_GIT_PUSH_GIT_REPO_DIR が設定されていません")

        return cls(
            watch_dir=watch_dir,
            git_repo_dir=git_repo_dir,
            push_dir=_load_env_str("AUTO_GIT_PUSH_PUSH_DIR", "."),
            branch=_load_env_str("AUTO_GIT_PUSH_BRANCH", "main"),
            delay_seconds=_load_env_int("AUTO_GIT_PUSH_DELAY_SECONDS", 30),
            ignore_seconds=_load_env_int("AUTO_GIT_PUSH_IGNORE_SECONDS", 5),
        )


def _load_env_str(key: str, default: str = "") -> str:
    """環境変数から文字列を取得する.

    Args:
        key: 環境変数のキー
        default: デフォルト値

    Returns:
        str: 環境変数の値
    """
    return os.environ.get(key, default)


def _load_env_int(key: str, default: int = 0) -> int:
    """環境変数から整数を取得する.

    Args:
        key: 環境変数のキー
        default: デフォルト値

    Returns:
        int: 環境変数の値

    Raises:
        ConfigError: 値が整数に変換できない場合
    """
    value = os.environ.get(key, "")
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"環境変数 {key} の値 '{value}' を整数に変換できません")
