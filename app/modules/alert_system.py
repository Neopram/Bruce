import logging
import asyncio
import aiohttp
import smtplib
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import Config

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Maximum retries for failed requests
MAX_RETRIES = 3

class AlertSystem:
    """
    Advanced multi-channel alert system:
    - Email (SMTP)
    - Telegram
    - Discord
    - Webhooks
    - SMS (Twilio)
    """

    def __init__(self, recipients=None, smtp_config=None, telegram_config=None, discord_webhook=None, sms_config=None):
        """
        Initializes the Alert System.

        Args:
            recipients (list): Email recipients.
            smtp_config (dict): SMTP email settings.
            telegram_config (dict): Telegram bot token & chat ID.
            discord_webhook (str): Discord webhook URL.
            sms_config (dict): Twilio SMS configuration.
        """
        self.recipients = recipients or []
        self.smtp_config = smtp_config
        self.telegram_config = telegram_config
        self.discord_webhook = discord_webhook
        self.sms_config = sms_config

    def validate_email_addresses(self):
        """
        Validates email recipients.

        Returns:
            bool: True if valid, False otherwise.
        """
        email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        invalid_emails = [email for email in self.recipients if not email_regex.match(email)]
        if invalid_emails:
            logging.warning(f"⚠️ Invalid email addresses: {invalid_emails}")
        return not invalid_emails

    async def send_email_alert(self, subject, message, format="plain"):
        """
        Sends an email alert.

        Args:
            subject (str): Email subject.
            message (str): Message content.
            format (str): Email format ('plain' or 'html').

        Returns:
            str: Success or error message.
        """
        if not self.validate_email_addresses():
            logging.error("❌ Invalid email recipients.")
            return "Invalid email recipients"

        msg = MIMEMultipart()
        msg["From"] = self.smtp_config.get("smtp_user")
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(message, format))

        try:
            with smtplib.SMTP(self.smtp_config.get("smtp_server"), self.smtp_config.get("smtp_port")) as server:
                server.starttls()
                server.login(self.smtp_config.get("smtp_user"), self.smtp_config.get("smtp_password"))
                server.sendmail(self.smtp_config.get("smtp_user"), self.recipients, msg.as_string())

            logging.info(f"📧 Email alert sent successfully.")
            return "Email alert sent successfully"
        except smtplib.SMTPException as e:
            logging.error(f"❌ Email Error: {e}")
            return f"Email Error: {e}"

    async def _send_async_request(self, url, payload, headers=None):
        """
        Sends an asynchronous HTTP request.

        Args:
            url (str): Request URL.
            payload (dict): Request payload.
            headers (dict, optional): Headers.

        Returns:
            dict: Response data.
        """
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                        return await response.text()
            except aiohttp.ClientError as e:
                logging.error(f"HTTP Request Failed: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(2)

        return {"error": "Max retries reached"}

    async def send_telegram_alert(self, message):
        """
        Sends a Telegram alert.

        Args:
            message (str): Alert message.

        Returns:
            str: Success or error message.
        """
        if not self.telegram_config:
            logging.warning("⚠️ Telegram configuration missing.")
            return "Telegram configuration missing"

        url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
        payload = {"chat_id": self.telegram_config["chat_id"], "text": message}
        
        return await self._send_async_request(url, payload)

    async def send_discord_alert(self, message):
        """
        Sends a Discord alert.

        Args:
            message (str): Alert message.

        Returns:
            str: Success or error message.
        """
        if not self.discord_webhook:
            logging.warning("⚠️ Discord webhook missing.")
            return "Discord webhook missing"

        payload = {"content": message}
        return await self._send_async_request(self.discord_webhook, payload)

    async def send_sms_alert(self, message):
        """
        Sends an SMS alert via Twilio.

        Args:
            message (str): SMS message.

        Returns:
            str: Success or error message.
        """
        if not self.sms_config:
            logging.warning("⚠️ SMS configuration missing.")
            return "SMS configuration missing"

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.sms_config['account_sid']}/Messages.json"
        payload = {
            "From": self.sms_config["from_number"],
            "To": self.sms_config["to_number"],
            "Body": message
        }
        headers = {
            "Authorization": f"Basic {self.sms_config['auth_token']}"
        }

        return await self._send_async_request(url, payload, headers)

    async def send_alert(self, message, alert_type="all", format="plain"):
        """
        Sends an alert through multiple channels asynchronously.

        Args:
            message (str): Alert message.
            alert_type (str): 'email', 'telegram', 'discord', 'sms', or 'all'.
            format (str): Email format ('plain' or 'html').

        Returns:
            dict: Responses from each alerting method.
        """
        tasks = {}

        if alert_type in ["email", "all"]:
            tasks["email"] = asyncio.create_task(self.send_email_alert("🚨 Trading Alert", message, format))

        if alert_type in ["telegram", "all"]:
            tasks["telegram"] = asyncio.create_task(self.send_telegram_alert(message))

        if alert_type in ["discord", "all"]:
            tasks["discord"] = asyncio.create_task(self.send_discord_alert(message))

        if alert_type in ["sms", "all"]:
            tasks["sms"] = asyncio.create_task(self.send_sms_alert(message))

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        return dict(zip(tasks.keys(), results))


# Example Usage
if __name__ == "__main__":
    alert_system = AlertSystem(
        recipients=["user@example.com"],
        smtp_config={"smtp_server": "smtp.example.com", "smtp_port": 587, "smtp_user": "your_email@example.com", "smtp_password": "your_password"},
        telegram_config={"bot_token": "your_telegram_bot_token", "chat_id": "your_chat_id"},
        discord_webhook="your_discord_webhook_url",
        sms_config={"account_sid": "your_twilio_sid", "auth_token": "your_twilio_auth_token", "from_number": "+1234567890", "to_number": "+0987654321"}
    )

    asyncio.run(alert_system.send_alert("⚡ Market volatility detected!", "all"))
