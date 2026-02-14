"""AutoGitPushConfig の単体テスト."""

import os

import pytest

from auto_git_push.config import AutoGitPushConfig
from auto_git_push.exceptions import ConfigError

# --- 正常系 ---


def test_create_config_with_required_params() -> None:
    """必須パラメータのみで設定を生成できる."""
    config = AutoGitPushConfig(
        watch_dir="/tmp/watch",
        git_repo_dir="/tmp/repo",
    )
    assert config.watch_dir == "/tmp/watch"
    assert config.git_repo_dir == "/tmp/repo"
    assert config.push_dir == "."
    assert config.branch == "main"
    assert config.delay_seconds == 30
    assert config.ignore_seconds == 5


def _custom_message() -> str:
    return "custom message"


def test_create_config_with_all_params() -> None:
    """全パラメータを指定して設定を生成できる."""
    config = AutoGitPushConfig(
        watch_dir="/tmp/watch",
        git_repo_dir="/tmp/repo",
        push_dir="public",
        branch="develop",
        delay_seconds=60,
        ignore_seconds=10,
        commit_message_fn=_custom_message,
    )
    assert config.watch_dir == "/tmp/watch"
    assert config.git_repo_dir == "/tmp/repo"
    assert config.push_dir == "public"
    assert config.branch == "develop"
    assert config.delay_seconds == 60
    assert config.ignore_seconds == 10
    assert config.commit_message_fn() == "custom message"


def test_default_commit_message_fn_returns_string() -> None:
    """デフォルトのコミットメッセージ生成関数が文字列を返す."""
    config = AutoGitPushConfig(
        watch_dir="/tmp/watch",
        git_repo_dir="/tmp/repo",
    )
    message = config.commit_message_fn()
    assert isinstance(message, str)
    assert "auto push" in message


def test_from_env_loads_config(monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
    """環境変数から設定を正しく読み込める."""
    monkeypatch.setenv("AUTO_GIT_PUSH_WATCH_DIR", "/tmp/watch")
    monkeypatch.setenv("AUTO_GIT_PUSH_GIT_REPO_DIR", "/tmp/repo")
    monkeypatch.setenv("AUTO_GIT_PUSH_PUSH_DIR", "dist")
    monkeypatch.setenv("AUTO_GIT_PUSH_BRANCH", "develop")
    monkeypatch.setenv("AUTO_GIT_PUSH_DELAY_SECONDS", "45")
    monkeypatch.setenv("AUTO_GIT_PUSH_IGNORE_SECONDS", "8")

    config = AutoGitPushConfig.from_env(env_path=os.devnull)
    assert config.watch_dir == "/tmp/watch"
    assert config.git_repo_dir == "/tmp/repo"
    assert config.push_dir == "dist"
    assert config.branch == "develop"
    assert config.delay_seconds == 45
    assert config.ignore_seconds == 8


def test_from_env_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """必須項目のみ設定した場合にデフォルト値が使用される."""
    monkeypatch.setenv("AUTO_GIT_PUSH_WATCH_DIR", "/tmp/watch")
    monkeypatch.setenv("AUTO_GIT_PUSH_GIT_REPO_DIR", "/tmp/repo")
    monkeypatch.delenv("AUTO_GIT_PUSH_PUSH_DIR", raising=False)
    monkeypatch.delenv("AUTO_GIT_PUSH_BRANCH", raising=False)
    monkeypatch.delenv("AUTO_GIT_PUSH_DELAY_SECONDS", raising=False)
    monkeypatch.delenv("AUTO_GIT_PUSH_IGNORE_SECONDS", raising=False)

    config = AutoGitPushConfig.from_env(env_path=os.devnull)
    assert config.push_dir == "."
    assert config.branch == "main"
    assert config.delay_seconds == 30
    assert config.ignore_seconds == 5


@pytest.mark.parametrize(
    "delay,ignore",
    [
        (0, 0),
        (0, 5),
        (30, 0),
    ],
)
def test_boundary_values_for_seconds(delay: int, ignore: int) -> None:
    """境界値（0）の設定が受け入れられる."""
    config = AutoGitPushConfig(
        watch_dir="/tmp/watch",
        git_repo_dir="/tmp/repo",
        delay_seconds=delay,
        ignore_seconds=ignore,
    )
    assert config.delay_seconds == delay
    assert config.ignore_seconds == ignore


# --- 準正常系 ---


def test_empty_watch_dir_raises_config_error() -> None:
    """watch_dirが空文字の場合にConfigErrorが発生する."""
    with pytest.raises(ConfigError, match="watch_dir"):
        AutoGitPushConfig(watch_dir="", git_repo_dir="/tmp/repo")


def test_empty_git_repo_dir_raises_config_error() -> None:
    """git_repo_dirが空文字の場合にConfigErrorが発生する."""
    with pytest.raises(ConfigError, match="git_repo_dir"):
        AutoGitPushConfig(watch_dir="/tmp/watch", git_repo_dir="")


def test_negative_delay_seconds_raises_config_error() -> None:
    """delay_secondsが負の値の場合にConfigErrorが発生する."""
    with pytest.raises(ConfigError, match="delay_seconds"):
        AutoGitPushConfig(
            watch_dir="/tmp/watch",
            git_repo_dir="/tmp/repo",
            delay_seconds=-1,
        )


def test_negative_ignore_seconds_raises_config_error() -> None:
    """ignore_secondsが負の値の場合にConfigErrorが発生する."""
    with pytest.raises(ConfigError, match="ignore_seconds"):
        AutoGitPushConfig(
            watch_dir="/tmp/watch",
            git_repo_dir="/tmp/repo",
            ignore_seconds=-1,
        )


def test_from_env_missing_watch_dir_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数にwatch_dirがない場合にConfigErrorが発生する."""
    monkeypatch.delenv("AUTO_GIT_PUSH_WATCH_DIR", raising=False)
    monkeypatch.setenv("AUTO_GIT_PUSH_GIT_REPO_DIR", "/tmp/repo")

    with pytest.raises(ConfigError, match="AUTO_GIT_PUSH_WATCH_DIR"):
        AutoGitPushConfig.from_env(env_path=os.devnull)


def test_from_env_missing_git_repo_dir_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """環境変数にgit_repo_dirがない場合にConfigErrorが発生する."""
    monkeypatch.setenv("AUTO_GIT_PUSH_WATCH_DIR", "/tmp/watch")
    monkeypatch.delenv("AUTO_GIT_PUSH_GIT_REPO_DIR", raising=False)

    with pytest.raises(ConfigError, match="AUTO_GIT_PUSH_GIT_REPO_DIR"):
        AutoGitPushConfig.from_env(env_path=os.devnull)


def test_from_env_invalid_delay_seconds_raises_config_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """環境変数のdelay_secondsが整数変換できない場合にConfigErrorが発生する."""
    monkeypatch.setenv("AUTO_GIT_PUSH_WATCH_DIR", "/tmp/watch")
    monkeypatch.setenv("AUTO_GIT_PUSH_GIT_REPO_DIR", "/tmp/repo")
    monkeypatch.setenv("AUTO_GIT_PUSH_DELAY_SECONDS", "abc")

    with pytest.raises(ConfigError, match="整数に変換できません"):
        AutoGitPushConfig.from_env(env_path=os.devnull)
