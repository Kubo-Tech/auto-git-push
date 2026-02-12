"""auto-git-push: ディレクトリの変更を検知して自動でGitリポジトリへpushするライブラリ.

このライブラリは、指定ディレクトリのファイル変更を監視し、
自動でgit commit & pushを行う機能を提供します。
"""

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("auto-git-push")
except (PackageNotFoundError, ImportError):
    __version__ = "unknown"

from auto_git_push.config import AutoGitPushConfig
from auto_git_push.exceptions import AutoGitPushError, GitCommandError
from auto_git_push.watcher import AutoGitPusher

__all__ = [
    "AutoGitPushConfig",
    "AutoGitPushError",
    "AutoGitPusher",
    "GitCommandError",
]
