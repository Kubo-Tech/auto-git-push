"""ファイル監視と自動Git push.

ディレクトリの変更を検知して自動でgit commit & pushを行うコアモジュール。
"""

import logging
import subprocess
import threading
import time
from typing import Any

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from auto_git_push.config import AutoGitPushConfig
from auto_git_push.exceptions import GitCommandError


class AutoGitPusher:
    """ディレクトリの変更を検知して自動でGitリポジトリへpushするクラス.

    Attributes:
        _config: 設定
        _logger: ロガーインスタンス
        _change_detected: 変更フラグ
        _last_event_time: 直近のイベント時刻
        _lock: スレッドロック
        _observer: watchdog Observer
    """

    def __init__(
        self,
        config: AutoGitPushConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        """AutoGitPusherを初期化する.

        Args:
            config: 設定インスタンス
            logger: ロガーインスタンス。Noneの場合はモジュールロガーを使用
        """
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._change_detected = False
        self._last_event_time: float = 0.0
        self._lock = threading.Lock()
        self._observer: Any = None

    def _run_git_commands(self) -> None:
        """Gitの自動コミットとプッシュを実行する.

        Raises:
            GitCommandError: gitコマンドの実行に失敗した場合
        """
        commit_message = self._config.commit_message_fn()
        git_repo_dir = self._config.git_repo_dir
        branch = self._config.branch
        push_dir = self._config.push_dir

        try:
            self._logger.info("git commit & push を実行します...")

            subprocess.run(
                ["git", "pull", "origin", branch],
                cwd=git_repo_dir,
                check=True,
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", push_dir],
                cwd=git_repo_dir,
                check=True,
                encoding="utf-8",
            )
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=git_repo_dir,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            commit_stdout = result.stdout or ""
            commit_stderr = result.stderr or ""
            commit_output = f"{commit_stdout}\n{commit_stderr}".lower()

            if "nothing to commit" in commit_output:
                self._logger.info("コミット対象の変更がありません。pushをスキップします")
                return

            if result.returncode != 0:
                error_message = (
                    "git commit が失敗しました: "
                    f"returncode={result.returncode}, stderr={commit_stderr.strip()}"
                )
                self._logger.error(error_message)
                raise GitCommandError(error_message)

            subprocess.run(
                ["git", "push", "origin", branch],
                cwd=git_repo_dir,
                check=True,
                encoding="utf-8",
            )
            self._logger.info("git commit & push が完了しました: %s", commit_message)

        except subprocess.CalledProcessError as error:
            error_message = f"gitコマンドの実行に失敗しました: {error}"
            self._logger.error(error_message)
            raise GitCommandError(error_message) from error

    def _delayed_commit(self) -> None:
        """変更があってから一定時間後にGitコマンドを実行する."""
        time.sleep(self._config.delay_seconds)
        should_run = False
        with self._lock:
            if self._change_detected:
                self._change_detected = False
                should_run = True

        if not should_run:
            return

        try:
            self._run_git_commands()
        except GitCommandError:
            pass  # ログ出力は_run_git_commands内で実施済み

    def _on_change_detected(self, src_path: str) -> None:
        """ファイル変更を検知した際の処理.

        Args:
            src_path: 変更されたファイルのパス
        """
        current_time = time.time()
        with self._lock:
            if current_time - self._last_event_time < self._config.ignore_seconds:
                return
            self._last_event_time = current_time
            self._change_detected = True

        self._logger.info("変更を検知しました: %s", src_path)
        threading.Thread(target=self._delayed_commit, daemon=True).start()

    def start(self) -> None:
        """ファイル監視を開始する.

        監視をブロッキングで開始する。Ctrl+Cで停止可能。
        """
        event_handler = _ChangeHandler(self)
        self._observer = Observer()
        self._observer.schedule(event_handler, self._config.watch_dir, recursive=True)
        self._observer.start()
        self._logger.info("ディレクトリを監視中: %s", self._config.watch_dir)

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """ファイル監視を停止する."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._logger.info("監視を停止しました")


class _ChangeHandler(FileSystemEventHandler):
    """ファイルシステムの変更を監視するハンドラー.

    Attributes:
        _pusher: AutoGitPusherインスタンスへの参照
    """

    def __init__(self, pusher: "AutoGitPusher") -> None:
        """ハンドラーを初期化する.

        Args:
            pusher: AutoGitPusherインスタンス
        """
        super().__init__()
        self._pusher = pusher

    def on_any_event(self, event: Any) -> None:
        """ファイルシステムの変更イベントを処理する.

        Args:
            event: ファイルシステムイベント
        """
        if event.is_directory:
            return
        self._pusher._on_change_detected(event.src_path)
