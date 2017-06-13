[![Travis](https://img.shields.io/travis/dotpot/pushit.svg)]()

## pushit 
Push notifications sender library for `ios` and `android`, made easy.


## Examples

```python
import pushit

def ios_callback_listener(error: dict) -> dict:
    # Handle error
    
    return error

# Create ios configuration.
ios_config = pushit.IOSConfig(
    cert_file_path='cert.pem',
    key_file_path='key.pem',
    use_sandbox=True,
    enhanced=True,
    
    # register your callback listener - in case of errors.
    response_listener_callback=ios_callback_listener
)

# Create android configuration
android_config = pushit.AndroidConfig(gcm_api_key='gcm-api-key')

# Configure pushit
pushit.configure(
    ios=ios_config,
    android=android_config
)

# Create notification object.
notification = pushit.Notification(
    notification_data={
        'title-loc-key': 'notification_title_new_message',
        'loc-key': 'notification_key_new_message'},
    sound='default',
    badge=1,
    custom_message={
        'notification_body': {
            'title': 'you have a new message from John',
            'message': 'hi!',
        }
    },
    content_available=True,
    mutable_content=True,
)

# Send notification for ios
notification.send(
    push_id=pushit.PushId(push_id='ios-push-id', kind=pushit.PushIdKind.IOs)
)

# Send notification for android
notification.send(
    push_id=pushit.PushId(push_id='android-push-id', kind=pushit.PushIdKind.Android)
)
```
