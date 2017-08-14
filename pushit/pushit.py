import enum
import logging
import random
from typing import Callable

from .android import GCM2
from .ios import APNs, Payload

log = logging.getLogger(__name__)


IOSResponseListenerType = Callable[[dict], dict]


class ConfigurationMissingError(BaseException):
    pass


class UnrecognisedPushIdError(BaseException):
    pass


class IOSConfig:
    cert_file_path = None
    key_file_path = None
    sandbox = False
    enhanced = False
    response_listener_callback = None

    def ios_response_listener(self, error_response) -> dict:
        log.error('client get error-response: %s', error_response)
        try:
            if 'identifier' in error_response:
                log.error('identifier %s found in response', error_response['identifier'])
        except Exception as exception:
            log.error('error while reading and setting response, %s', exception)

        return error_response

    def __init__(self,
                 cert_file_path: str,
                 key_file_path: str,
                 use_sandbox: bool,
                 enhanced: bool,
                 response_listener_callback: IOSResponseListenerType):
        self.cert_file_path = cert_file_path
        self.key_file_path = key_file_path
        self.sandbox = use_sandbox
        self.enhanced = enhanced

        # register callback handler if provided.
        self.response_listener_callback = response_listener_callback if \
            response_listener_callback else self.ios_response_listener


class AndroidConfig:
    gcm_api_key = None

    def __init__(self, gcm_api_key: str):
        self.gcm_api_key = gcm_api_key


class PushIdKind(enum.Enum):
    IOs = 'ios'
    Android = 'android'


class PushId:
    """wrapper for ios and android push id"""
    push_id = None  # type: str
    kind = None  # type: PushIdKind

    def __init__(self, push_id: str, kind: PushIdKind):
        self.push_id = push_id
        self.kind = kind


class Services:
    ios = None  # type: APNs
    android = None  # type: GCM2

    def __init__(self, ios: APNs, android: GCM2):
        self.ios = ios
        self.android = android


_services = None  # type: Services


def configure(ios: IOSConfig, android: AndroidConfig):
    global _services

    _services = Services(
        ios=APNs(
            use_sandbox=ios.sandbox,
            cert_file=ios.cert_file_path,
            key_file=ios.key_file_path,
            enhanced=ios.enhanced,
        ),
        android=GCM2(
            api_key=android.gcm_api_key
        )
    )

    # attach response callback handler.
    _services.ios.gateway_server.register_response_listener(ios.response_listener_callback)

    return _services


class Notification:
    notification_data = None
    sound = "default"
    badge = 0
    custom_message = None
    content_available = False
    mutable_content = False

    def __init__(self,
                 notification_data: dict,
                 sound: str="default",
                 badge: int=0,
                 custom_message: dict=None,
                 content_available: bool=True,
                 mutable_content: bool=True):
        self.notification_data = notification_data
        self.sound = sound
        self.badge = badge
        self.custom_message = custom_message
        self.content_available = content_available
        self.mutable_content = mutable_content

    def _send_ios(self, push_id: PushId):
        global _services

        payload = Payload(
            alert=self.notification_data,
            sound=self.sound,
            badge=self.badge,
            custom=self.custom_message,
            content_available=self.content_available,
            mutable_content=self.mutable_content)

        return _services.ios.gateway_server.send_notification(
            token_hex=push_id.push_id,
            payload=payload,
            identifier=random.SystemRandom().getrandbits(32)
        )

    def _send_android(self, push_id: PushId):
        global _services

        response = _services.android.json_request(
            registration_ids=[push_id.push_id],
            notification_data=self.notification_data)

        return response

    def send(self, push_id: PushId):
        global _services

        if not _services:
            raise ConfigurationMissingError("missing configuration, use `configure` method first.")

        if push_id.kind == PushIdKind.IOs:
            return self._send_ios(push_id=push_id)
        elif push_id.kind == PushIdKind.Android:
            return self._send_android(push_id=push_id)

        raise UnrecognisedPushIdError("unrecognized push_id")


__all__ = [
    'configure',

    'Notification',

    'AndroidConfig',
    'IOSConfig',

    'PushId',
]
