import base64
import requests
from config import *

API_URL = 'https://api.imgur.com/'
MASHAPE_URL = 'https://imgur-apiv3.p.mashape.com/'


class AuthWrapper(object):
    def __init__(self, access_token, refresh_token, client_id, client_secret):
        self.current_access_token = access_token

        if refresh_token is None:
            raise TypeError('A refresh token must be provided')

        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret

    def get_refresh_token(self):
        return self.refresh_token

    def get_current_access_token(self):
        return self.current_access_token

    def refresh(self):
        data = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token'
        }

        url = API_URL + 'oauth2/token'

        response = requests.post(url, data=data)

        if response.status_code != 200:
            raise print('Error refreshing access token!', response.status_code)

        response_data = response.json()
        self.current_access_token = response_data['access_token']


class ImgurClient(object):
    allowed_album_fields = {
        'ids', 'title', 'description', 'privacy', 'layout', 'cover'
    }

    allowed_advanced_search_fields = {
        'q_all', 'q_any', 'q_exactly', 'q_not', 'q_type', 'q_size_px'
    }

    allowed_account_fields = {
        'bio', 'public_images', 'messaging_enabled', 'album_privacy', 'accepted_gallery_terms', 'username'
    }

    allowed_image_fields = {
        'album', 'name', 'title', 'description'
    }

    def __init__(self, client_id, client_secret, access_token=None, refresh_token=None, mashape_key=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth = None
        self.mashape_key = mashape_key

        if refresh_token is not None:
            self.auth = AuthWrapper(access_token, refresh_token, client_id, client_secret)

        self.credits = self.get_credits()

    def set_user_auth(self, access_token, refresh_token):
        self.auth = AuthWrapper(access_token, refresh_token, self.client_id, self.client_secret)

    def get_client_id(self):
        return self.client_id

    def get_credits(self):
        return self.make_request('GET', 'credits', None, True)

    def get_auth_url(self, response_type='pin'):
        return '%soauth2/authorize?client_id=%s&response_type=%s' % (API_URL, self.client_id, response_type)

    def authorize(self, response, grant_type='pin'):
        return self.make_request('POST', 'oauth2/token', {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': grant_type,
            'code' if grant_type == 'authorization_code' else grant_type: response
        }, True)

    def prepare_headers(self, force_anon=False):
        headers = {}
        if force_anon or self.auth is None:
            if self.client_id is None:
                raise ImgurClientError('Client credentials not found!')
            else:
                headers['Authorization'] = 'Client-ID %s' % self.get_client_id()
        else:
            headers['Authorization'] = 'Bearer %s' % self.auth.get_current_access_token()

        if self.mashape_key is not None:
            headers['X-Mashape-Key'] = self.mashape_key

        return headers


    def make_request(self, method, route, data=None, force_anon=False):
        method = method.lower()
        method_to_call = getattr(requests, method)

        header = self.prepare_headers(force_anon)
        url = (MASHAPE_URL if self.mashape_key is not None else API_URL) + ('3/%s' % route if 'oauth2' not in route else route)

        if method in ('delete', 'get'):
            response = method_to_call(url, headers=header, params=data, data=data)
        else:
            response = method_to_call(url, headers=header, data=data)

        if response.status_code == 403 and self.auth is not None:
            self.auth.refresh()
            header = self.prepare_headers()
            if method in ('delete', 'get'):
                response = method_to_call(url, headers=header, params=data, data=data)
            else:
                response = method_to_call(url, headers=header, data=data)

        self.credits = {
            'UserLimit': response.headers.get('X-RateLimit-UserLimit'),
            'UserRemaining': response.headers.get('X-RateLimit-UserRemaining'),
            'UserReset': response.headers.get('X-RateLimit-UserReset'),
            'ClientLimit': response.headers.get('X-RateLimit-ClientLimit'),
            'ClientRemaining': response.headers.get('X-RateLimit-ClientRemaining')
        }

        # Rate-limit check
        if response.status_code == 429:
            raise print('429 error')

        try:
            response_data = response.json()
        except:
            raise print('JSON decoding of response failed.')

        if 'data' in response_data and isinstance(response_data['data'], dict) and 'error' in response_data['data']:
            raise print(response_data['data']['error'], response.status_code)

        return response_data['data'] if 'data' in response_data else response_data

    def validate_user_context(self, username):
        if username == 'me' and self.auth is None:
            raise print('\'me\' can only be used in the authenticated context.')

    def logged_in(self):
        if self.auth is None:
            raise print('Must be logged in to complete request.')

    # Account-related endpoints
    def get_account(self, username):
        self.validate_user_context(username)
        account_data = self.make_request('GET', 'account/%s' % username)

        return Account(
            account_data['id'],
            account_data['url'],
            account_data['bio'],
            account_data['reputation'],
            account_data['created'],
            account_data['pro_expiration'],
        )