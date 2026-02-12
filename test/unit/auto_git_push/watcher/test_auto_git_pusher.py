"""AutoGitPusher の単体テスト."""

import logging
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from auto_git_push.config import AutoGitPushConfig
from auto_git_push.exceptions import GitCommandError
from auto_git_push.watcher import AutoGitPusher


@pytest.fixture()
def config() -> AutoGitPushConfig:
    """テスト用の設定を返す."""
    return AutoGitPushConfig(
        watch_dir="/tmp/watch",
        git_repo_dir="/tmp/repo",
        push_dir="public",
        branch="main",
        delay_seconds=0,
        ignore_seconds=0,
    )


@pytest.fixture()
def logger() -> logging.Logger:
    """テスト用のロガーを返す."""
    return logging.getLogger("test_auto_git_pusher")


@pytest.fixture()
def pusher(config: AutoGitPushConfig, logger: logging.Logger) -> AutoGitPusher:
    """テスト用のAutoGitPusherインスタンスを返す."""
    return AutoGitPusher(config, logger=logger)


# --- 正常系 ---


def test_init_with_logger(config: AutoGitPushConfig, logger: logging.Logger) -> None:
    """ロガーを指定して初期化できる."""
    auto_pusher = AutoGitPusher(config, logger=logger)
    assert auto_pusher._logger is logger


def test_init_without_logger(config: AutoGitPushConfig) -> None:
    """ロガーを指定しない場合はモジュールロガーが使用される."""
    auto_pusher = AutoGitPusher(config)
    assert auto_pusher._logger.name == "auto_git_push.watcher"


@patch("auto_git_push.watcher.subprocess.run")
def test_run_git_commands_success(mock_run: MagicMock, pusher: AutoGitPusher) -> None:
    """gitコマンドが正常に実行される."""
    commit_result = MagicMock()
    commit_result.stdout = "1 file changed"
    mock_run.side_effect = [
        MagicMock(),  # git pull
        MagicMock(),  # git add
        commit_result,  # git commit
        MagicMock(),  # git push
    ]

    pusher._run_git_commands()

    assert mock_run.call_count == 4


@patch("auto_git_push.watcher.subprocess.run")
def test_run_git_commands_nothing_to_commit(mock_run: MagicMock, pusher: AutoGitPusher) -> None:
    """コミット対象がない場合にpushが実行されない."""
    commit_result = MagicMock()
    commit_result.stdout = "nothing to commit, working tree clean"
    mock_run.side_effect = [
        MagicMock(),  # git pull
        MagicMock(),  # git add
        commit_result,  # git commit
    ]

    pusher._run_git_commands()

    assert mock_run.call_count == 3


@patch("auto_git_push.watcher.subprocess.run")
def test_run_git_commands_uses_custom_commit_message(mock_run: MagicMock) -> None:
    """カスタムコミットメッセージが使用される."""
    custom_message = "custom commit message"
    custom_config = AutoGitPushConfig(
        watch_dir="/tmp/watch",
        git_repo_dir="/tmp/repo",
        commit_message_fn=lambda: custom_message,
    )
    auto_pusher = AutoGitPusher(custom_config)

    commit_result = MagicMock()
    commit_result.stdout = "1 file changed"
    mock_run.side_effect = [
        MagicMock(),  # git pull
        MagicMock(),  # git add
        commit_result,  # git commit
        MagicMock(),  # git push
    ]

    auto_pusher._run_git_commands()

    commit_call_args = mock_run.call_args_list[2]
    assert custom_message in commit_call_args[0][0]


def test_on_change_detected_sets_flag(pusher: AutoGitPusher) -> None:
    """変更検知時にフラグがセットされる."""
    with patch("auto_git_push.watcher.threading.Thread"):
        pusher._on_change_detected("/tmp/watch/test.txt")
        assert pusher._change_detected is True


def test_on_change_detected_ignores_rapid_events(pusher: AutoGitPusher) -> None:
    """短時間の連続イベントが無視される."""
    slow_config = AutoGitPushConfig(
        watch_dir="/tmp/watch",
        git_repo_dir="/tmp/repo",
        ignore_seconds=10,
    )
    slow_pusher = AutoGitPusher(slow_config)

    with patch("auto_git_push.watcher.threading.Thread") as mock_thread:
        slow_pusher._on_change_detected("/tmp/watch/test1.txt")
        first_call_count = mock_thread.call_count

        slow_pusher._on_change_detected("/tmp/watch/test2.txt")
        assert mock_thread.call_count == first_call_count


def test_stop_without_start(pusher: AutoGitPusher) -> None:
    """start前にstopを呼んでもエラーにならない."""
    pusher.stop()


# --- 準正常系 ---


@patch("auto_git_push.watcher.subprocess.run")
def test_run_git_commands_raises_git_command_error(
    mock_run: MagicMock, pusher: AutoGitPusher
) -> None:
    """gitコマンド失敗時にGitCommandErrorが発生する."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "git pull")

    with pytest.raises(GitCommandError, match="gitコマンドの実行に失敗しました"):
        pusher._run_git_commands()
