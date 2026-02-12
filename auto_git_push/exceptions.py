"""例外クラス定義.

このモジュールは、auto-git-pushライブラリで使用される例外クラスを定義する。
"""


class AutoGitPushError(Exception):
    """auto-git-push基底例外.

    auto-git-pushライブラリの全ての例外の基底クラス。
    """

    pass


class GitCommandError(AutoGitPushError):
    """Gitコマンド実行エラー.

    gitコマンドの実行に失敗した場合に送出される例外。
    """

    pass


class ConfigError(AutoGitPushError):
    """設定エラー.

    設定値が不正な場合に送出される例外。
    """

    pass
