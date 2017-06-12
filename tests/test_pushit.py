import pytest

from pushit import pushit


def test_pushit_notification_raises_if_no_configuration():
    notification = pushit.Notification({'some': 'data'})
    assert notification is not None

    with pytest.raises(pushit.ConfigurationMissingError):
        notification.send(pushit.PushId('123123', pushit.PushIdKind.IOs))

