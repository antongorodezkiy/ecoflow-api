#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ecoflow REST API Library
"""

import hashlib
import hmac
import random
import time
import logging
import urllib
from flatten_dict import flatten
from urllib.parse import urlencode
from urllib.parse import unquote
from http.client import HTTPConnection

import requests

class EcoflowApi:
    base_url = None
    access_key = None
    secret_key = None
    log = None
    _app_debug_level = None
    _requests_debug_level = None

    def __init__(self, *, base_url = 'https://api.ecoflow.com', access_key, secret_key):
        self.base_url = base_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.log = logging

    def set_logger(self, logger):
        self.log = logger

    def debug_requests_on(self):
        # (c) https://stackoverflow.com/a/24588289/741782
        '''Switches on logging of the requests module.'''
        HTTPConnection.debuglevel = 1

        self.log.basicConfig()
        root_logger = self.log.getLogger()
        self._app_debug_level = root_logger.getEffectiveLevel()
        root_logger.setLevel(self.log.DEBUG)

        requests_log = self.log.getLogger('requests.packages.urllib3')
        self._requests_debug_level = requests_log.getEffectiveLevel()
        requests_log.setLevel(self.log.DEBUG)
        requests_log.propagate = True

    def debug_requests_off(self):
        # (c) https://stackoverflow.com/a/24588289/741782
        '''Switches off logging of the requests module, might be some side-effects'''
        HTTPConnection.debuglevel = 0

        self.log.getLogger().setLevel(self._app_debug_level)

        requests_log = self.log.getLogger('requests.packages.urllib3')
        requests_log.setLevel(self._requests_debug_level)
        requests_log.propagate = False

    def get_timestamp(self):
        timestamp = int(time.time()) * 1000
        return str(timestamp)

    def generate_nonce(self):
        return str(random.randrange(100000, 999999))

    def ecoflow_reducer(self, k1, k2):
        if k1 is None:
            return k2
        else:
            if type(k2) is int:
                return f"{k1}[{k2}]"
            else:
                return f"{k1}.{k2}"

    def generate_sign(self, params, timestamp, nonce):
        params = flatten(params, reducer = self.ecoflow_reducer, enumerate_types=(list,))
        all_params = {
            **params,
            **{
                'accessKey': self.access_key,
                'nonce': nonce,
                'timestamp': timestamp
            }
        }

        return hmac \
            .new(self.secret_key.encode(), unquote(urlencode(all_params)).encode(), hashlib.sha256) \
            .hexdigest()

    def debug(self, message):
        self.log.debug(f"Ecoflow API debug: {message}")
        pass

    def error(self, message):
        self.log.error(f"Ecoflow API error occured: {message}")
        pass

    def url(self, path_and_params):
        return f"{self.base_url}{path_and_params}"

    def request(self, method, url, *, data = None):
        timestamp = self.get_timestamp()
        nonce = self.generate_nonce()

        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'accessKey': self.access_key,
            'nonce': nonce,
            'timestamp': timestamp,
            'sign': self.generate_sign(data if data is not None else {}, timestamp, nonce)
        }

        response = requests.request(method, url, headers = headers, json = data)

        self.debug(f"{method} {url} with headers = {headers}, data = {data}, response = {response}")

        if response and response.status_code == 200:
             return response
        else:
            self.error("Non-success status code: {response.status_code} while requesting {url}")
            raise Exception(f"Non-success status code: {response.status_code}")

    def get_device_list(self):
        """
        Query the user's bound device list
        Only returns the device bound to itself, not by share.
        """

        return self.request('get', self.url('/iot-open/sign/device/list'))

    def set_device_quota(self, sn, params):
        """
        Setting device's function
        """

        data = {
            'params': params,
            'sn': sn
        }

        return self.request('put', self.url('/iot-open/sign/device/quota'), data = data)

    def get_device_quota(self, sn, params):
        """
        Query the device's quota infomation
        """

        data = {
            'params': params,
            'sn': sn
        }

        return self.request('post', self.url('/iot-open/sign/device/quota'), data = data)

    def get_device_quota_all(self, sn):
        """
        Query device's all quota infomation
        """

        return self.request('get', self.url(f"/iot-open/sign/device/quota/all?sn={sn}"))

    def get_mqtt_certification(self):
        """
        MQTT certificate acquisition
        Get the MQTT certification, using it for MQTT communication.
        """

        return self.request('get', self.url('/iot-open/sign/certification'))