"""auto-git-pushの基本的な使い方.

.envファイルから設定を読み込んで、ファイル監視を開始する例。
"""

import logging

from auto_git_push import AutoGitPushConfig, AutoGitPusher


def main() -> None:
    """メイン関数."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("auto_git_push_example")

    # .envから設定を読み込む
    config = AutoGitPushConfig.from_env()

    # AutoGitPusherを初期化してファイル監視を開始
    pusher = AutoGitPusher(config, logger=logger)
    pusher.start()


if __name__ == "__main__":
    main()
