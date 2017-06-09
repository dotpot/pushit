import collections
import random
import time
import urllib
import urllib.error
import urllib.parse
import urllib.request

import ujson as json


GCM_URL = 'https://android.googleapis.com/gcm/send'


class GCMException(Exception):
    pass


class GCMMalformedJsonException(GCMException):
    pass


class GCMConnectionException(GCMException):
    pass


class GCMAuthenticationException(GCMException):
    pass


class GCMTooManyRegIdsException(GCMException):
    pass


class GCMInvalidTtlException(GCMException):
    pass


# Exceptions from Google responses


class GCMMissingRegistrationException(GCMException):
    pass


class GCMMismatchSenderIdException(GCMException):
    pass


class GCMNotRegisteredException(GCMException):
    pass


class GCMMessageTooBigException(GCMException):
    pass


class GCMInvalidRegistrationException(GCMException):
    pass


class GCMUnavailableException(GCMException):
    pass


def group_response(response, registration_ids, key):
    # Pair up results and reg_ids
    mapping = zip(registration_ids, response['results'])
    # Filter by key
    filtered = ((reg_id, res[key]) for reg_id, res in mapping if key in res)
    # Grouping of errors and mapping of ids
    if key is 'registration_id':
        grouping = dict(filtered)
    else:
        grouping = collections.defaultdict(list)
        for k, v in filtered:
            grouping[v].append(k)

    return grouping or None


def urlencode_utf8(params):
    """
    UTF-8 safe variant of urllib.urlencode.
    http://stackoverflow.com/a/8152242
    """

    if hasattr(params, 'items'):
        params = params.items()

    params = (
        '='.join((
            urllib.quote_plus(k.encode('utf8'), safe='/'),
            urllib.quote_plus(v.encode('utf8'), safe='/')
        )) for k, v in params
    )

    return '&'.join(params)


class GCM2(object):
    # Timeunit is milliseconds.
    BACKOFF_INITIAL_DELAY = 1000
    MAX_BACKOFF_DELAY = 1024000

    def __init__(self, api_key, url=GCM_URL, proxy=None):
        """ api_key : google api key
            url: url of gcm service.
            proxy: can be string "http://host:port" or dict {'https':'host:port'}
        """
        super(GCM2, self).__init__()

        self.api_key = api_key
        self.url = url
        if proxy:
            if isinstance(proxy, str):
                protocol = url.split(':')[0]
                proxy = {protocol: proxy}

            auth = urllib.request.HTTPBasicAuthHandler()
            opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxy), auth, urllib.request.HTTPHandler)
            urllib.request.install_opener(opener)

    def construct_payload(self, registration_ids, data=None, collapse_key=None,
                          delay_while_idle=False, time_to_live=None, is_json=True, dry_run=False):
        """
        Construct the dictionary mapping of parameters.
        Encodes the dictionary into JSON if for json requests.
        Helps appending 'data.' prefix to the plaintext data: 'hello' => 'data.hello'

        :return constructed dict or JSON payload
        :raises GCMInvalidTtlException: if time_to_live is invalid
        """

        if time_to_live:
            four_weeks_in_secs = 2419200
            if not (0 <= time_to_live <= four_weeks_in_secs):
                raise GCMInvalidTtlException("Invalid time to live value")

        if is_json:
            payload = {'registration_ids': registration_ids}
            if data:
                payload['data'] = data
        else:
            payload = {'registration_id': registration_ids}

            if data:
                for k in sorted(data.keys()):
                    data['data.%s' % k] = data.pop(k)
                payload.update(data)

        if delay_while_idle:
            payload['delay_while_idle'] = delay_while_idle

        if time_to_live:
            payload['time_to_live'] = time_to_live

        if collapse_key:
            payload['collapse_key'] = collapse_key

        if dry_run:
            payload['dry_run'] = True

        if is_json:
            payload = json.dumps(payload).encode('utf8')

        return payload

    def make_request(self, data, is_json=True):
        """
        Makes a HTTP request to GCM servers with the constructed payload

        :param data: return value from construct_payload method
        :raises GCMMalformedJsonException: if malformed JSON request found
        :raises GCMAuthenticationException: if there was a problem with authentication, invalid api key
        :raises GCMConnectionException: if GCM is screwed
        """

        headers = {
            'Authorization': 'key=%s' % self.api_key,
        }
        # Default Content-Type is defaulted to
        # application/x-www-form-urlencoded;charset=UTF-8
        if is_json:
            headers['Content-Type'] = 'application/json'

        if not is_json:
            data = urllib.parse.urlencode(data)
        req = urllib.request.Request(self.url, data, headers)

        try:
            response = urllib.request.urlopen(req).read()
        except urllib.error.HTTPError as e:
            if e.code == 400:
                raise GCMMalformedJsonException(
                    "The request could not be parsed as JSON")
            elif e.code == 401:
                raise GCMAuthenticationException(
                    "There was an error authenticating the sender account")
            elif e.code == 503:
                raise GCMUnavailableException("GCM service is unavailable")
        except urllib.error.URLError as e:
            raise GCMConnectionException(
                "There was an internal error in the GCM server while trying to process the request")

        if is_json:
            response = json.loads(response.decode('utf8'))
        return response

    def raise_error(self, error):
        if error == 'InvalidRegistration':
            raise GCMInvalidRegistrationException("Registration ID is invalid")
        elif error == 'Unavailable':
            # Plain-text requests will never return Unavailable as the error code.
            # http://developer.android.com/guide/google/gcm/gcm.html#error_codes
            raise GCMUnavailableException(
                "Server unavailable. Resent the message")
        elif error == 'NotRegistered':
            raise GCMNotRegisteredException(
                "Registration id is not valid anymore")
        elif error == 'MismatchSenderId':
            raise GCMMismatchSenderIdException(
                "A Registration ID is tied to a certain group of senders")
        elif error == 'MessageTooBig':
            raise GCMMessageTooBigException("Message can't exceed 4096 bytes")

    def handle_plaintext_response(self, response):

        # Split response by line
        response_lines = response.strip().split('\n')
        # Split the first line by =
        key, value = response_lines[0].split('=')
        if key == 'Error':
            self.raise_error(value)
        else:
            if len(response_lines) == 2:
                return response_lines[1].split('=')[1]
            return

    def handle_json_response(self, response, registration_ids):
        errors = group_response(response, registration_ids, 'error')
        canonical = group_response(
            response, registration_ids, 'registration_id')

        info = {
            'info': {},
            'original_response': response
        }

        if errors:
            info['info'].update({'errors': errors})
        if canonical:
            info['info'].update({'canonical': canonical})

        return info

    def extract_unsent_reg_ids(self, info):
        if 'errors' in info and 'Unavailable' in info['errors']:
            return info['errors']['Unavailable']
        return []

    def plaintext_request(self, registration_id, data=None, collapse_key=None,
                          delay_while_idle=False, time_to_live=None, retries=5, dry_run=False):
        """
        Makes a plaintext request to GCM servers

        :param registration_id: string of the registration id
        :param data: dict mapping of key-value pairs of messages
        :return dict of response body from Google including multicast_id, success, failure, canonical_ids, etc
        :raises GCMMissingRegistrationException: if registration_id is not provided
        """

        if not registration_id:
            raise GCMMissingRegistrationException("Missing registration_id")

        payload = self.construct_payload(
            registration_id, data, collapse_key,
            delay_while_idle, time_to_live, False, dry_run
        )

        attempt = 0
        backoff = self.BACKOFF_INITIAL_DELAY
        for attempt in range(retries):
            try:
                response = self.make_request(payload, is_json=False)
                return self.handle_plaintext_response(response)
            except GCMUnavailableException:
                sleep_time = backoff / 2 + random.randrange(backoff)
                time.sleep(float(sleep_time) / 1000)
                if 2 * backoff < self.MAX_BACKOFF_DELAY:
                    backoff *= 2

        raise IOError("Could not make request after %d attempts" % attempt)

    def json_request(self, registration_ids, data=None, collapse_key=None,
                     delay_while_idle=False, time_to_live=None, retries=5, dry_run=False):
        """
        Makes a JSON request to GCM servers

        :param registration_ids: list of the registration ids
        :param data: dict mapping of key-value pairs of messages
        :return dict of response body from Google including multicast_id, success, failure, canonical_ids, etc
        :raises GCMMissingRegistrationException: if the list of registration_ids is empty
        :raises GCMTooManyRegIdsException: if the list of registration_ids exceeds 1000 items
        """

        if not registration_ids:
            raise GCMMissingRegistrationException("Missing registration_ids")
        if len(registration_ids) > 1000:
            raise GCMTooManyRegIdsException(
                "Exceded number of registration_ids")

        attempt = 0
        backoff = self.BACKOFF_INITIAL_DELAY
        response = ''

        for attempt in range(retries):
            payload = self.construct_payload(
                registration_ids, data, collapse_key,
                delay_while_idle, time_to_live, True, dry_run
            )
            response = self.make_request(payload, is_json=True)
            info = self.handle_json_response(response, registration_ids)

            unsent_reg_ids = self.extract_unsent_reg_ids(info)
            if unsent_reg_ids:
                registration_ids = unsent_reg_ids
                sleep_time = backoff / 2 + random.randrange(backoff)
                time.sleep(float(sleep_time) / 1000)
                if 2 * backoff < self.MAX_BACKOFF_DELAY:
                    backoff *= 2
            else:
                break

        return info
