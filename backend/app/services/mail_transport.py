"""Authenticated SMTP with conservative handling of an uncertain DATA outcome."""
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from cryptography.fernet import Fernet, InvalidToken

from app.schemas.notifications import MailAccount, SMTPConnection


class MailFailure(Exception):
    def __init__(self, code: str, *, retryable=False, uncertain=False, account_failure=False, address_failure=False):
        self.code = code
        self.retryable = retryable
        self.uncertain = uncertain
        self.account_failure = account_failure
        self.address_failure = address_failure
        super().__init__(code)


class SMTPTransport:
    def __init__(self, encryption_key: str | None):
        self.cipher = Fernet(encryption_key.encode()) if encryption_key else None

    @property
    def configured(self):
        return self.cipher is not None

    def _login(self, account, password):
        client = None
        try:
            if account.security == "ssl":
                client = smtplib.SMTP_SSL(account.host, account.port, timeout=10, context=ssl.create_default_context())
            else:
                client = smtplib.SMTP(account.host, account.port, timeout=10)
                client.ehlo()
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            client.login(account.username, password)
            return client
        except smtplib.SMTPAuthenticationError as exc:
            if client:
                client.close()
            raise MailFailure("smtp_auth_failed", account_failure=True) from exc
        except (OSError, smtplib.SMTPException) as exc:
            if client:
                client.close()
            raise MailFailure("smtp_connection_failed", retryable=True) from exc

    def connect(self, connection: SMTPConnection) -> MailAccount:
        if self.cipher is None:
            raise MailFailure("mail_encryption_key_missing", account_failure=True)
        client = self._login(connection, connection.password.get_secret_value())
        client.close()  # Auth check only: no message is sent.
        fields = connection.model_dump(exclude={"password"})
        return MailAccount(**fields, encrypted_password=self.cipher.encrypt(connection.password.get_secret_value().encode()).decode())

    def send(self, account: MailAccount, recipient: str, subject: str, body: str, message_id: str):
        if self.cipher is None:
            raise MailFailure("mail_encryption_key_missing", account_failure=True)
        try:
            password = self.cipher.decrypt(account.encrypted_password.encode()).decode()
        except InvalidToken as exc:
            raise MailFailure("mail_credentials_unreadable", account_failure=True) from exc
        message = EmailMessage()
        message["From"] = formataddr((account.sender_name, account.sender_email))
        message["To"] = recipient
        message["Subject"] = subject
        message["Message-ID"] = message_id
        message.set_content(body)
        client = self._login(account, password)
        try:
            refused = client.send_message(message)
            if refused:
                raise MailFailure("recipient_rejected", address_failure=True)
        except smtplib.SMTPRecipientsRefused as exc:
            codes = [value[0] for value in exc.recipients.values()]
            temporary = bool(codes) and all(400 <= code < 500 for code in codes)
            raise MailFailure("recipient_temporarily_rejected" if temporary else "recipient_rejected",
                              retryable=temporary, address_failure=not temporary) from exc
        except (smtplib.SMTPDataError, smtplib.SMTPSenderRefused) as exc:
            raise MailFailure("smtp_message_rejected", retryable=400 <= exc.smtp_code < 500) from exc
        except (OSError, smtplib.SMTPException) as exc:
            # We may have lost the response AFTER SMTP accepted DATA. No blind retry.
            raise MailFailure("smtp_acceptance_unknown", uncertain=True) from exc
        finally:
            client.close()  # A later QUIT failure must not turn an accepted send into a retry.
