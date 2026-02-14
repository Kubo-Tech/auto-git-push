"""auto-git-pushのカスタム設定例.

Pythonスクリプト上で設定を直接指定し、カスタムコミットメッセージを使用する例。
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from auto_git_push import AutoGitPushConfig, AutoGitPusher


def _create_commit_message() -> str:
    """カスタムコミットメッセージを生成する.

    Returns:
        str: コミットメッセージ
    """
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    return f"{now.hour}:{now.minute:02} html自動プッシュ"


def main() -> None:
    """メイン関数."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("custom_example")

    config = AutoGitPushConfig(
        watch_dir="/path/to/watch",
        git_repo_dir="/path/to/git/repo",
        push_dir="public",
        branch="main",
        delay_seconds=30,
        ignore_seconds=5,
        commit_message_fn=_create_commit_message,
    )

    pusher = AutoGitPusher(config, logger=logger)
    pusher.start()


if __name__ == "__main__":
    main()
