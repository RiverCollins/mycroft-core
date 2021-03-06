# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import subprocess
import time
import sys
from alsaaudio import Mixer
from threading import Thread, Timer
import requests

import mycroft.dialog
from mycroft.client.enclosure.base import Enclosure
from mycroft.api import has_been_paired
from mycroft.audio import wait_while_speaking
from mycroft.enclosure.display_manager import \
    init_display_manager_bus_connection
from mycroft.messagebus.message import Message
from mycroft.util import connected
from mycroft.util.log import LOG

class EnclosureZPod(Enclosure):
    """
    Serves as a communication interface between a simple text frontend and
    Mycroft Core.  This is used for Picroft or other headless systems,
    and/or for users of the CLI.
    """

    _last_internet_notification = 0

    def __init__(self):
        super().__init__()
        # Notifications from mycroft-core
        self.bus.on("enclosure.notify.no_internet", self.on_no_internet)
        self.bus.on("enclosure.started", self.talk)
        
        # initiates the web sockets on display manager
        # NOTE: this is a temporary place to connect the display manager
        init_display_manager_bus_connection()

        # verify internet connection and prompt user on bootup if needed
        if not connected():
            # We delay this for several seconds to ensure that the other
            # clients are up and connected to the messagebus in order to
            # receive the "speak".  This was sometimes happening too
            # quickly and the user wasn't notified what to do.
            Timer(5, self._do_net_check).start()
        self.bus.on('enclosure.mouth.reset', self.reset)
        self.bus.on('enclosure.mouth.talk', self.talk)
        self.bus.on('enclosure.mouth.think', self.think)
        self.bus.on('enclosure.mouth.listen', self.listen)
        self.bus.on('enclosure.mouth.smile', self.smile)
        self.bus.on('enclosure.mouth.viseme', self.viseme)
        self.bus.on('enclosure.mouth.text', self.text)
        self.bus.on('enclosure.mouth.display', self.display)
        self.bus.on('enclosure.mouth.display_image', self.display_image)
        self.bus.on('enclosure.weather.display', self.display_weather)
        self.bus.on('speak', self.speakTest)
        self.bus.on('mycroft.audio.speech.stop', self.speakStop)

        self.bus.on('recognizer_loop:record_begin', self.mouthListen)
        self.bus.on('recognizer_loop:record_end', self.mouthReset)
        self.bus.on('recognizer_loop:audio_output_start', self.mouthTalk)
        self.bus.on('recognizer_loop:audio_output_end', self.mouthReset)

        self.bus.on('enclosure.mouth.events.activate', self.mouthActive)
        self.bus.on('enclosure.mouth.events.deactivate', self.mouthDeactive)

    def speakStop(self, event):
        r = requests.post("http://127.0.0.1/speakStop")
        LOG.debug("Wow ===> speakStop" + r.text)
        utterance = event.data['utterance']
        LOG.debug("TEST => " + utterance)

    def speakTest(self, event):
        utterance = event.data['utterance']
        payload = {"words": utterance}
        r = requests.get("http://127.0.0.1/speakTest", params=payload)
        LOG.debug("TEST " + r.url)
        LOG.debug("Wow ===> speakTest" + r.text)
        LOG.debug("TEST => " + utterance)

    def mouthDeactive(self, event=None):
        r = requests.post("http://127.0.0.1/mouthDeactive")
        LOG.debug("Wow ===> mouth deactive" + r.text)

    def mouthActive(self, event=None):
        r = requests.post("http://127.0.0.1/mouthActive")
        LOG.debug("Wow ===> mouth activee" + r.text)

    def mouthListen(self, event=None):
        r = requests.post("http://127.0.0.1/mouthListen")
        LOG.debug("Wow ===> mouth Listen" + r.text)

    def mouthReset(self, event=None):
        r = requests.post("http://127.0.0.1/mouthReset")
        LOG.debug("Wow ===> mouth Reset" + r.text)

    def mouthTalk(self, event=None):
        r = requests.post("http://127.0.0.1/mouthTalk")
        LOG.debug("Wow ===> mouth Talkt" + r.text)

    def reset(self, event=None):
        r = requests.post("http://127.0.0.1/reset")
        LOG.debug("Wow ===================> reset" + r.text)

    def talk(self, event=None):
        r = requests.post("http://127.0.0.1/talk")
        LOG.debug("Wow ===================> talk" + r.text)

    def think(self, event=None):
        r = requests.post("http://127.0.0.1/think")
        LOG.debug("Wow ===================> think" + r.text)

    def listen(self, event=None):
        r = requests.post("http://127.0.0.1/listen")
        LOG.debug("Wow ===================> listen" + r.text)

    def smile(self, event=None):
        r = requests.post("http://127.0.0.1/smile")
        LOG.debug("Wow ===================> smile" + r.text)
    
    def viseme(self, event=None):
        LOG.debug("Wow viseme")
        r = requests.post("http://127.0.0.1/viseme")
        LOG.debug("Wow ===================> viseme" + r.text)

    def text(self, event=None):
        r = requests.post("http://127.0.0.1/text")
        LOG.debug("Wow ===================> text" + r.text)

    def display(self, event=None):
        r = requests.post("http://127.0.0.1/display")
        LOG.debug("Wow ===================> display" + r.text)

    def display_image(self, event=None):
        r = requests.post("http://127.0.0.1/display_image")
        LOG.debug("Wow ===================> display_image" + r.text)


    def display_weather(self, event=None):
        r = requests.post("http://127.0.0.1/display_weather")
        LOG.debug("Wow ===================> display_weather" + r.text)

    def on_no_internet(self, event=None):
        if connected():
            # One last check to see if connection was established
            return

        if time.time() - Enclosure._last_internet_notification < 30:
            # don't bother the user with multiple notifications with 30 secs
            return

        Enclosure._last_internet_notification = time.time()

        # TODO: This should go into EnclosureMark1 subclass of Enclosure.
        if has_been_paired():
            # Handle the translation within that code.
            self.bus.emit(Message("speak", {
                'utterance': "This device is not connected to the Internet. "
                             "Either plug in a network cable or set up your "
                             "wifi connection."}))
        else:
            # enter wifi-setup mode automatically
            self.bus.emit(Message('system.wifi.setup', {'lang': self.lang}))

    def speak(self, text):
        self.bus.emit(Message("speak", {'utterance': text}))

    def _handle_pairing_complete(self, Message):
        """
        Handler for 'mycroft.paired', unmutes the mic after the pairing is
        complete.
        """
        self.bus.emit(Message("mycroft.mic.unmute"))

    def _do_net_check(self):
        # TODO: This should live in the derived Enclosure, e.g. EnclosureMark1
        LOG.info("Checking internet connection")
        if not connected():  # and self.conn_monitor is None:
            if has_been_paired():
                # TODO: Enclosure/localization
                self.speak("This unit is not connected to the Internet. "
                           "Either plug in a network cable or setup your "
                           "wifi connection.")
            else:
                # Begin the unit startup process, this is the first time it
                # is being run with factory defaults.

                # TODO: This logic should be in EnclosureMark1
                # TODO: Enclosure/localization

                # Don't listen to mic during this out-of-box experience
                self.bus.emit(Message("mycroft.mic.mute"))
                # Setup handler to unmute mic at the end of on boarding
                # i.e. after pairing is complete
                self.bus.once('mycroft.paired', self._handle_pairing_complete)

                self.speak(mycroft.dialog.get('mycroft.intro'))
                wait_while_speaking()
                time.sleep(2)  # a pause sounds better than just jumping in

                # Kick off wifi-setup automatically
                data = {'allow_timeout': False, 'lang': self.lang}
                self.bus.emit(Message('system.wifi.setup', data))
