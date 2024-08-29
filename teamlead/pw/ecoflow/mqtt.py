import logging
import ssl
import time
from threading import Timer
from multiprocessing import Process

import paho.mqtt.client as mqtt

class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

class EcoflowMQTTApi():
    client = None
    host = None
    port = 1883
    log = None
    timeout = 60
    last_message_time = None
    timoeout_sleep_before_reconnect = 5
    timoeout_idle_reconnect_process = 60

    REASON_CODE_SUCCESS = 'Success'
    REASON_CODE_KEEP_ALIVE_TIMEOUT = 'Keep alive timeout'
    REASON_CODE_UNSUPPORTED_PROTOCOL_VERSION = 'Unsupported protocol version'
    REASON_CODE_CLIENT_IDENTIFIER_NOT_VALID = 'Client identifier not valid'
    REASON_CODE_SERVER_UNAVAILABLE = 'Server unavailable'
    REASON_CODE_BAD_USER_NAME_OR_PASSWORD = 'Bad user name or password'
    REASON_CODE_NOT_AUTHORIZED = 'Not authorized'

    def __init__(self, *, username, password, host, port):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.log = logging

    def set_logger(self, logger):
        self.log = logger

    def set_timeout(self, timeout):
        self.timeout = timeout

    def set_client_id(self, client_id):
        self.client_id = client_id

    def set_on_connected(self, on_connected):
        self.on_connected = on_connected

    def set_on_message(self, on_message):
        self.on_message = on_message

    def touch(self):
        self.last_message_time = time.time()

    def _init_idle_timer(self):
        # In the file https://github.com/peuter/ecoflow/blob/master/model/ecoflow/mqtt_client.py for example
        # there is no such logic at all, need to figure it out
        self.idle_timer = RepeatTimer(10, self.idle_reconnect)
        self.idle_timer.daemon = True
        self.idle_timer.start()

    def connect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        else:
            self._init_idle_timer()

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.client_id)
        self.client.username_pw_set(self.username, self.password)
        self.client.tls_set(certfile = None, keyfile = None, cert_reqs = ssl.CERT_REQUIRED)
        self.client.tls_insecure_set(False)

        # callbacks
        self.client.on_connect = self._on_connect
        self.client.on_subscribe = self._on_subscribe
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.log.info(f"Connecting to MQTT Broker {self.host}:{self.port}, client id = {self.client_id}")
        self.client.connect(self.host, self.port)
        self.client.loop_start()

    def idle_reconnect(self):
        if self.last_message_time and (time.time() - self.last_message_time) > self.timeout:
            self.log.error(f"Inactive for {self.timeout} seconds. Reconnecting...")
            # We pull the following into a separate process because there are actually quite a few things that can go
            # wrong inside the connection code, including it just timing out and never returning. So this gives us a
            # measure of safety around reconnection
            while True:
                connect_process = Process(target = self.connect)
                connect_process.start()
                connect_process.join(timeout = self.timoeout_idle_reconnect_process)
                connect_process.terminate()
                if connect_process.exitcode == 0:
                    self.log.info('Reconnected successfully')
                    # Reset last_message_time here to avoid a race condition between idle_reconnect getting called again
                    # before on_connect() or on_message() are called
                    self.last_message_time = None
                    break
                else:
                    self.log.error('Failed to reconnect or timed out, reconnecting...')

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        # reset message time on connection
        self.touch()
        match reason_code:
            case self.REASON_CODE_SUCCESS:
                self.on_connected(self, client)
            case _:
                self.log.error(f"Failed to connect to MQTT: {reason_code}")

        return client

    def on_connected(self, client):
        self.log.info(f"on_connected: {client}")

    def _on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        self.log.info(f"on_subscribe: {client}, {userdata}, {mid}, {reason_code_list}, {properties}")

    def _on_message(self, client, userdata, message):
        self.touch()
        self.on_message(self, client, userdata, message)

    def on_message(self, client, userdata, message):
        self.log.info(f"on_message: {message.payload.decode('utf-8')}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code > 0:
            self.log.error(f"Unexpected MQTT disconnection: {reason_code}. Will auto-reconnect")
            time.sleep(self.timoeout_sleep_before_reconnect)
        else:
            self.log.error(f"Other MQTT disconnection: {reason_code}")

    def get_client(self):
        return self.client