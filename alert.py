import os
from twilio.rest import Client
import constants

class SMSSender:
    def __init__(self):
        self.number = '+447700168457'
        self.account_sid = constants.API_ACCOUNT_SID
        self.auth_token = constants.API_AUTH_TOKEN

    def send(self, recipient, message):
        client = Client(self.account_sid, self.auth_token)
        message = client.messages.create(
        body=f"{message}",
        from_="+447700168457",
        to=f"{recipient}"
)

