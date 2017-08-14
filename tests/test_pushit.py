import pytest

from pushit import pushit


@pytest.fixture
def ios_apns_fixture():
    class ApnsMock:
        class DummyGatewayServer:
            def register_response_listener(self, listener): pass

            def send_notification(self, token_hex, payload, identifier): pass

        gateway_server = DummyGatewayServer()
    return ApnsMock()


@pytest.fixture
def gcm_fixture():
    class GCMMock:
        def json_request(self, registration_ids, notification_data):
            return {}
    return GCMMock()


def test_pushit_notification_raises_if_no_configuration():
    notification = pushit.Notification({'some': 'data'})
    assert notification is not None

    with pytest.raises(pushit.ConfigurationMissingError):
        notification.send(pushit.PushId('123123', pushit.PushIdKind.IOs))


def test_pushit_notification_send_raises_once_wrong_push_id(ios_apns_fixture, gcm_fixture):
    notification = pushit.Notification({'some': 'data'}, custom_message={'custom': 'message'})
    pushit._services = pushit.Services(ios=ios_apns_fixture, android=gcm_fixture)
    with pytest.raises(pushit.UnrecognisedPushIdError):
        notification.send(push_id=pushit.PushId(push_id='123123', kind='asd'))


def test_pushit_notification_send_ios_calls(ios_apns_fixture, gcm_fixture, mocker):
    notification = pushit.Notification({'some': 'data'}, custom_message={'custom': 'message'})
    pushit._services = pushit.Services(ios=ios_apns_fixture, android=gcm_fixture)

    mocker.patch.object(pushit._services.ios.gateway_server, 'send_notification', autospec=True)
    notification.send(push_id=pushit.PushId(push_id='123', kind=pushit.PushIdKind.IOs))
    pushit._services.ios.gateway_server.send_notification.assert_called_once()


def test_pushit_notification_send_android_calls(ios_apns_fixture, gcm_fixture, mocker):
    notification = pushit.Notification({'some': 'data'}, custom_message={'custom': 'message'})
    pushit._services = pushit.Services(ios=ios_apns_fixture, android=gcm_fixture)

    mocker.patch.object(pushit._services.android, 'json_request', autospec=True)
    notification.send(push_id=pushit.PushId(push_id='123', kind=pushit.PushIdKind.Android))
    pushit._services.android.json_request.assert_called_once()
