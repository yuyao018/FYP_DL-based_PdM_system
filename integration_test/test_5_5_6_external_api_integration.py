import sys
from types import SimpleNamespace

import degradation_analysis
import email_notifications


def test_smtp_adapter_sends_message_to_configured_recipients(monkeypatch):
    calls = {}

    class FakeSMTP:
        def __init__(self, host, port): calls.update(host=host, port=port)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def ehlo(self): pass
        def starttls(self): pass
        def login(self, sender, password): calls.update(sender=sender, password=password)
        def sendmail(self, sender, recipients, message):
            calls.update(recipients=recipients, message=message)

    monkeypatch.setenv("EMAIL_SENDER", "alerts@example.test")
    monkeypatch.setenv("EMAIL_PASSWORD", "test-secret")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setattr(email_notifications.smtplib, "SMTP", FakeSMTP)

    sent = email_notifications._send_email("Test alert", "<p>Test</p>", ["tech@example.test"])

    assert sent is True
    assert calls["host"] == "smtp.example.test" and calls["port"] == 2525
    assert calls["recipients"] == ["tech@example.test"]
    assert "Test alert" in calls["message"]


def test_smtp_failure_is_reported_without_raising(monkeypatch):
    class BrokenSMTP:
        def __init__(self, *args): raise OSError("SMTP unavailable")

    monkeypatch.setenv("EMAIL_SENDER", "alerts@example.test")
    monkeypatch.setenv("EMAIL_PASSWORD", "test-secret")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setattr(email_notifications.smtplib, "SMTP", BrokenSMTP)
    assert email_notifications._send_email("Test alert", "body", ["tech@example.test"]) is False


def test_groq_client_response_is_validated_and_returned(monkeypatch):
    requests = []

    class FakeGroq:
        def __init__(self, **kwargs): requests.append(("init", kwargs))
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    requests.append(("request", kwargs))
                    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                        content=("### Why It Was Detected\n- **T30** has a SHAP contribution.\n\n"
                                 "### Engineering Interpretation\nThe pattern is HPC Degradation with 75.0% similarity.\n\n"
                                 "### Recommended Action\n- [Priority 1](https://example.test): Inspect the HPC.")))])

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=FakeGroq))
    result, source = degradation_analysis.generate_llm_explanation(
        "HPC Degradation", 0.75, [{"sensor": "T30", "score": 0.8}], return_source=True
    )
    assert "HPC Degradation" in result and "75.0%" in result
    assert "Priority 1:" in result and "[Priority" not in result and "https://example.test" not in result
    assert source == "Groq · GPT-OSS 120B"
    assert requests[0] == ("init", {"api_key": "test-key"})
    assert requests[1][1]["model"] == "openai/gpt-oss-120b"


def test_groq_outage_uses_local_fallback(monkeypatch):
    class UnavailableGroq:
        def __init__(self, **kwargs): pass
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs): raise OSError("API unavailable")

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=UnavailableGroq))
    result, source = degradation_analysis.generate_llm_explanation(
        "HPC Degradation", 0.75, [{"sensor": "T30", "score": 0.8}], return_source=True
    )
    assert "Why It Was Detected" in result
    assert "HPC Degradation" in result
    assert source == "Template fallback"


def test_groq_output_with_unlisted_sensor_is_replaced_by_fallback(monkeypatch):
    class InconsistentGroq:
        def __init__(self, **kwargs): pass
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                        content=("### Why It Was Detected\n- **T30** contributes.\n\n"
                                 "### Engineering Interpretation\nHPC Degradation has 75.0% similarity; P30 is declining.\n\n"
                                 "### Recommended Action\n- Monitor T30.")))])

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=InconsistentGroq))
    result, source = degradation_analysis.generate_llm_explanation(
        "HPC Degradation", 0.75, [{"sensor": "T30", "score": -0.8}], return_source=True
    )
    assert source == "Template fallback"
    assert "P30" not in result
    assert "T30" in result
