from datetime import date

# Monkeypatch dependencies in gmail_services
import googleapiclient.discovery
import pytest
from googleapiclient.errors import HttpError

# Import the module to test
from services.google_integration import gmail_services


# Dummy implementations to bypass real API calls
class DummyCredentials:
    def authorize(self, http):
        return http


def dummy_load_credentials(token_path):
    return DummyCredentials()


def dummy_refresh_access_token(creds, token_path):
    return creds


def dummy_print_token_ttl(creds):
    pass


# Dummy Gmail API objects
class DummyMessages:
    def list(self, **kwargs):
        # Distinguish between inbox/unread and reserved unread labels
        if kwargs.get("labelIds") == ["INBOX", "UNREAD"]:

            class DummyResponse:
                def execute(self):
                    return {"messages": [{"id": "1"}, {"id": "2"}]}

            return DummyResponse()
        elif kwargs.get("labelIds") == ["reserved", "UNREAD"]:

            class DummyResponse:
                def execute(self):
                    return {"messages": [{"id": "3"}]}

            return DummyResponse()
        else:

            class DummyResponse:
                def execute(self):
                    return {}

            return DummyResponse()

    def modify(self, **kwargs):
        class DummyResponse:
            def execute(self):
                return None

        return DummyResponse()

    def get(self, **kwargs):
        class DummyResponse:
            def execute(self):
                return {
                    "payload": {
                        "headers": [
                            {
                                "name": "Subject",
                                "value": "Reservation confirmed: Jane Doe",
                            },
                            {"name": "From", "value": "jane@example.com"},
                            {"name": "Date", "value": "2022-01-02"},
                        ],
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {"data": "dGVzdA=="},  # base64 for "test"
                            }
                        ],
                    },
                    "snippet": "Test snippet",
                }

        return DummyResponse()


class DummyLabels:
    def list(self, **kwargs):
        class DummyResponse:
            def execute(self):
                return {
                    "labels": [
                        {"id": "reserved", "name": "reserved"},
                        {"id": "poubelle", "name": "poubelle"},
                    ]
                }

        return DummyResponse()


class DummyUsers:
    def messages(self):
        return DummyMessages()

    def labels(self):
        return DummyLabels()


class DummyGmail:
    def users(self):
        return DummyUsers()


# Monkeypatch build to use our DummyGmail
def dummy_build(serviceName, version, credentials):
    return DummyGmail()


# Pytest fixtures
@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    monkeypatch.setenv("TOKEN_PATH", "dummy_token_path")
    # Patch functions in the gmail_services module instead of oauth_credentials.authentification
    monkeypatch.setattr(gmail_services, "load_credentials", dummy_load_credentials)
    monkeypatch.setattr(
        gmail_services, "refresh_access_token", dummy_refresh_access_token
    )
    monkeypatch.setattr(gmail_services, "print_token_ttl", dummy_print_token_ttl)
    # Patch both discovery.build and the already imported build in gmail_services
    monkeypatch.setattr(googleapiclient.discovery, "build", dummy_build)
    monkeypatch.setattr(gmail_services, "build", dummy_build)


@pytest.fixture
def gmail_service_instance():
    return gmail_services.GmailService()


def test_list_unread_mails(gmail_service_instance):
    # Test that list_unread_mails returns expected IDs.
    ids = gmail_service_instance.list_unread_mails()
    assert ids == ["1", "2"]


def test_get_mail_content(gmail_service_instance):
    # Test get_mail_content returns expected details.
    content = gmail_service_instance.get_mail_content("3")
    assert content.get("Subject") == "Reservation confirmed: Jane Doe"
    assert content.get("Sender") == "jane@example.com"
    # Check date conversion (2022-01-02)
    assert content.get("Date") == str(date(2022, 1, 2))
    assert content.get("Snippet") == "Test snippet"
    # Decode: base64 "dGVzdA==" -> "test" appears in the message body (if parsed correctly)
    assert "test" in content.get("Message_body", "")


def test_parse_reservation_header(gmail_service_instance):
    # Test parse_reservation_header with a dummy subject.
    content = {"Subject": "Reservation confirmed: John Doe"}
    result = gmail_service_instance.parse_reservation_header(content)
    # Check the 'type' key instead of 'is_reservation'
    assert result["type"] == "reservation"
    assert result["full_name"] == "John Doe"


def test_mark_as_read(gmail_service_instance):
    # Test mark_as_read does not raise errors.
    try:
        gmail_service_instance.mark_as_read("1")
    except HttpError:
        pytest.fail("mark_as_read raised HttpError unexpectedly.")


def test_tag_email(gmail_service_instance, monkeypatch):
    # Ensure tag_email does not raise errors.
    called = False

    def dummy_modify(self, **kwargs):
        nonlocal called
        called = True

        class DummyResponse:
            def execute(self):
                return {}

        return DummyResponse()

    # Force get_label_id to return a dummy label ID
    monkeypatch.setattr(
        gmail_service_instance, "get_label_id", lambda label: "dummy_label_id"
    )
    # Override the modify method on the DummyMessages class used in the service instance
    messages_instance = gmail_service_instance.gmail.users().messages()
    monkeypatch.setattr(messages_instance.__class__, "modify", dummy_modify)
    gmail_service_instance.tag_email("dummy_msg_id", "reserved")
    assert called is True


def test_process_unread_emails(gmail_service_instance, monkeypatch):
    # Simply ensure process_unread_emails runs without error.
    monkeypatch.setattr(gmail_service_instance, "list_unread_mails", lambda: ["1"])
    # Force a reservation email for id "1"
    monkeypatch.setattr(
        gmail_service_instance,
        "get_mail_content",
        lambda msg_id: {"Subject": "Reservation confirmed: Jane Doe"},
    )
    monkeypatch.setattr(
        gmail_service_instance, "get_label_id", lambda label: "dummy_label_id"
    )
    # Patch modify to do nothing.
    monkeypatch.setattr(
        gmail_service_instance.gmail.users().messages(),
        "modify",
        lambda **kwargs: type("Dummy", (), {"execute": lambda: {}})(),
    )
    gmail_service_instance.process_unread_emails()


def test_get_unread_emails_content_by_label(gmail_service_instance, monkeypatch):
    # Simulate get_unread_emails_content_by_label method.
    dummy_response = {"messages": [{"id": "1"}, {"id": "2"}]}
    monkeypatch.setattr(
        gmail_service_instance.gmail.users().messages(),
        "list",
        lambda **kwargs: type("Dummy", (), {"execute": lambda: dummy_response})(),
    )
    monkeypatch.setattr(
        gmail_service_instance,
        "get_mail_content",
        lambda msg_id: {"id": msg_id, "Subject": "Dummy"},
    )
    # Override get_label_id to trigger the INBOX branch
    monkeypatch.setattr(gmail_service_instance, "get_label_id", lambda label: "INBOX")
    result = gmail_service_instance.get_unread_emails_content_by_label("reserved")
    assert isinstance(result, list)
    assert len(result) == 2


def test_mark_mails_as_read_for_label(gmail_service_instance, monkeypatch):
    # Simulate marking emails as read.
    dummy_response = {"messages": [{"id": "1"}]}
    # Override get_label_id to trigger the "reserved" branch in DummyMessages.list
    monkeypatch.setattr(
        gmail_service_instance, "get_label_id", lambda label: "reserved"
    )
    monkeypatch.setattr(
        gmail_service_instance.gmail.users().messages(),
        "list",
        lambda **kwargs: type("Dummy", (), {"execute": lambda: dummy_response})(),
    )
    called = False

    def dummy_mark_as_read(msg_id: str):
        nonlocal called
        called = True

    monkeypatch.setattr(gmail_service_instance, "mark_as_read", dummy_mark_as_read)
    gmail_service_instance.mark_mails_as_read_for_label("reserved")
    assert called is True
