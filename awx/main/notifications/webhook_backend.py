# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging
import requests

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.utils import get_awx_version

logger = logging.getLogger('awx.main.notifications.webhook_backend')


class WebhookBackend(AWXBaseEmailBackend):

    init_parameters = {"url": {"label": "Target URL", "type": "string"},
                       "http_method": {"label": "HTTP Method", "type": "string", "default": "POST"},
                       "disable_ssl_verification": {"label": "Verify SSL", "type": "bool", "default": False},
                       "username": {"label": "Username", "type": "string", "default": ""},
                       "password": {"label": "Password", "type": "password", "default": ""},
                       "headers": {"label": "HTTP Headers", "type": "object"}}
    recipient_parameter = "url"
    sender_parameter = None

    def __init__(self, http_method, headers, disable_ssl_verification=False, fail_silently=False, username=None, password=None, **kwargs):
        self.http_method = http_method
        self.disable_ssl_verification = disable_ssl_verification
        self.headers = headers
        self.username = username
        self.password = password
        super(WebhookBackend, self).__init__(fail_silently=fail_silently)

    def format_body(self, body):
        return body

    def send_messages(self, messages):
        sent_messages = 0
        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = "Tower {}".format(get_awx_version())
        if self.http_method.lower() not in ['put','post']:
            raise ValueError("HTTP method must be either 'POST' or 'PUT'.")
        chosen_method = getattr(requests, self.http_method.lower(), None)
        for m in messages:
            auth = None
            if self.username:
                auth = (self.username, self.password)
            r = chosen_method("{}".format(m.recipients()[0]),
                              auth=auth,
                              json=m.body,
                              headers=self.headers,
                              verify=(not self.disable_ssl_verification))
            if r.status_code >= 400:
                logger.error(smart_text(_("Error sending notification webhook: {}").format(r.text)))
                if not self.fail_silently:
                    raise Exception(smart_text(_("Error sending notification webhook: {}").format(r.text)))
            sent_messages += 1
        return sent_messages
