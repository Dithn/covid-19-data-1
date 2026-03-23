from slack import WebClient
from cowidev.utils.params import SECRETS

ERROR_COLOR = "#a30200"
WARNING_COLOR = "#f2c744"
SUCCESS_COLOR = "#01a715"


class SlackAPI:
    def __init__(self) -> None:
        self.client = self._load_client()

    def _load_client(self):
        if SECRETS.slack.token != "":
            return WebClient(token=SECRETS.slack.token)
        return None

    def _send_msg(self, channel, title, message_color, title_header=None, message="", trace=None):
        if not self.client:
            return None
        if title_header is not None:
            title = f"{title_header}: {title}"
        if trace is not None and trace != "":
            message += f"\n```{trace}```"
        return self.client.chat_postMessage(
            channel=channel,
            attachments=[{"color": message_color, "title": title, "fallback": title, "text": message}],
        )

    def send_error(self, channel, title, message="", trace=None):
        self._send_msg(
            channel=channel,
            title=title,
            title_header="Error",
            message_color=ERROR_COLOR,
            message=message,
            trace=trace,
        )

    def send_warning(self, channel, title, message="", trace=None):
        self._send_msg(
            channel=channel,
            title=title,
            title_header="Warning",
            message_color=WARNING_COLOR,
            message=message,
            trace=trace,
        )

    def send_success(self, channel, title, message="", trace=None):
        self._send_msg(
            channel=channel,
            title=title,
            message_color=SUCCESS_COLOR,
            message=message,
            trace=trace,
        )


if __name__ == "__main__":
    slack = SlackAPI()
    slack.send_warning("#corona-data-updates", "Test", "Test error message")
