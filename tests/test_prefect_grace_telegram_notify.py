from prefect_grace.tasks import telegram_notify


def test_notify_submission_event_skips_without_chat(monkeypatch) -> None:
    monkeypatch.delenv("GRACE_NOTIFY_CHAT_ID", raising=False)
    monkeypatch.delenv("SUPERVISOR_NOTIFY_CHAT_ID", raising=False)
    monkeypatch.delenv("DUCTOR_CHAT_ID", raising=False)
    monkeypatch.delenv("BOT_ADMIN_IDS", raising=False)
    monkeypatch.setattr(telegram_notify, "PROJECT_ROOT", telegram_notify.PROJECT_ROOT.parent / "__missing__")
    assert telegram_notify.notify_submission_event(feature_id="FEAT-1", title="Title", execute=False) is False


def test_notify_packet_event_renders_prefect_links(monkeypatch) -> None:
    sent: list[str] = []
    monkeypatch.setenv("GRACE_NOTIFY_PACKET_STATUSES", "rework_required")
    monkeypatch.setattr(telegram_notify, "_send_html_message", lambda text: sent.append(text) or True)
    monkeypatch.setattr(
        telegram_notify,
        "load_runtime_config",
        lambda: type("Cfg", (), {"public_ui_url": "https://prefect.vasiliy-ivanov.ru"})(),
    )

    ok = telegram_notify.notify_packet_event(
        feature_id="FEAT-1",
        packet_id="FEAT-1-W01-CODER",
        role="coder",
        status="rework_required",
        wave_id="W01",
        title="Week Runtime Indicator Disclosure",
        reasons=["Observability evidence missing"],
        task_run_id="task-123",
        flow_run_id="flow-456",
    )

    assert ok is True
    assert sent
    assert "FEAT-1-W01-CODER" in sent[0]
    assert "Открыть запуск задачи" in sent[0]
    assert "Открыть запуск фичи" in sent[0]


def test_notify_packet_event_filters_non_major_statuses_by_default(monkeypatch) -> None:
    sent: list[str] = []
    monkeypatch.delenv("GRACE_NOTIFY_PACKET_STATUSES", raising=False)
    monkeypatch.setattr(telegram_notify, "_send_html_message", lambda text: sent.append(text) or True)

    assert telegram_notify.notify_packet_event(
        feature_id="FEAT-1",
        packet_id="FEAT-1-W01-CODER",
        role="coder",
        status="accepted",
        wave_id="W01",
    ) is False
    assert sent == []


def test_notify_packet_event_allows_status_override(monkeypatch) -> None:
    sent: list[str] = []
    monkeypatch.setenv("GRACE_NOTIFY_PACKET_STATUSES", "all")
    monkeypatch.setattr(telegram_notify, "_send_html_message", lambda text: sent.append(text) or True)

    assert telegram_notify.notify_packet_event(
        feature_id="FEAT-1",
        packet_id="FEAT-1-W01-CODER",
        role="coder",
        status="accepted",
        wave_id="W01",
    ) is True
    assert "Пакет: принят" in sent[0]


def test_notify_feature_event_renders_ru_short_blocked_summary(monkeypatch) -> None:
    sent: list[str] = []
    monkeypatch.setattr(telegram_notify, "_send_html_message", lambda text: sent.append(text) or True)

    ok = telegram_notify.notify_feature_event(
        feature_id="FEAT-1",
        title="Feature 1",
        status="pipeline_invalid",
        summary="Long English summary that should not be the primary user-facing message.",
        blockers=["Planner wave plan JSON markers were not found in reviewer output and this text is intentionally long enough to be trimmed by the notifier."],
        next_action="fix-planner-contract",
    )

    assert ok is True
    assert sent
    assert "Фича: пайплайн некорректен" in sent[0]
    assert "Итог: пайплайн некорректен." in sent[0]
    assert "Planner wave plan JSON markers were not found" in sent[0]
    assert "Исправьте контракт планировщика." in sent[0]


def test_notify_chat_id_falls_back_to_last_bot_admin_id_from_env(monkeypatch) -> None:
    monkeypatch.delenv("GRACE_NOTIFY_CHAT_ID", raising=False)
    monkeypatch.delenv("SUPERVISOR_NOTIFY_CHAT_ID", raising=False)
    monkeypatch.delenv("DUCTOR_CHAT_ID", raising=False)
    monkeypatch.setenv("BOT_ADMIN_IDS", "1,2,833478509")

    assert telegram_notify._notify_chat_id() == 833478509


def test_notify_chat_id_falls_back_to_env_file(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("GRACE_NOTIFY_CHAT_ID", raising=False)
    monkeypatch.delenv("SUPERVISOR_NOTIFY_CHAT_ID", raising=False)
    monkeypatch.delenv("DUCTOR_CHAT_ID", raising=False)
    monkeypatch.delenv("BOT_ADMIN_IDS", raising=False)
    monkeypatch.setattr(telegram_notify, "PROJECT_ROOT", tmp_path)
    (tmp_path / ".env").write_text("BOT_ADMIN_IDS=11,22,833478509\n", encoding="utf-8")

    assert telegram_notify._notify_chat_id() == 833478509


def test_send_html_message_falls_back_to_telegram_api(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    monkeypatch.setenv("GRACE_NOTIFY_CHAT_ID", "833478509")
    monkeypatch.delenv("SUPERVISOR_NOTIFY_CHAT_ID", raising=False)
    monkeypatch.delenv("DUCTOR_CHAT_ID", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(
        telegram_notify,
        "_post_json",
        lambda url, payload: calls.append((url, payload)) or ("api.telegram.org" in url),
    )

    ok = telegram_notify._send_html_message("<b>Hello</b>")

    assert ok is True
    assert len(calls) >= 2
    assert calls[0][0] == "http://127.0.0.1:8001/notify"
    assert "api.telegram.org" in calls[-1][0]
