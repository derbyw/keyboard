# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
# Ubuntu Keyboard Test Suite
# Copyright (C) 2013 Canonical
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os

from testtools.matchers import Equals
from tempfile import mktemp
from textwrap import dedent

from autopilot.testcase import AutopilotTestCase
from autopilot.input import Pointer, Touch
from autopilot.matchers import Eventually

from ubuntu_keyboard.emulators.keyboard import Keyboard, KeyboardState


class UbuntuKeyboardTests(AutopilotTestCase):
    def setUp(self):
        super(UbuntuKeyboardTests, self).setUp()
        self.pointer = Pointer(Touch.create())

    def launch_test_input_area(self, label="", input_hints=None):
        self.app = self._launch_simple_input(label, input_hints)
        text_area = self.app.select_single("QQuickTextInput")

        return text_area

    def ensure_focus_on_input(self, input_area):
        self.pointer.click_object(input_area)
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)
        self.assertThat(keyboard.is_available, Eventually(Equals(True)))

    def _start_qml_script(self, script_contents):
        """Launch a qml script."""
        qml_path = mktemp(suffix='.qml')
        open(qml_path, 'w').write(script_contents)
        self.addCleanup(os.remove, qml_path)

        return self.launch_test_application(
            "qmlscene",
            qml_path,
            app_type='qt',
        )

    def _launch_simple_input(self, label="", input_hints=None):
        if input_hints is None:
            extra_script = "Qt.ImhNoPredictiveText"
        else:
            extra_script = "|".join(input_hints)

        simple_script = dedent("""
        import QtQuick 2.0
        import Ubuntu.Components 0.1

        Rectangle {
            id: window
            objectName: "windowRectangle"
            color: "lightgrey"

            Text {
                id: inputLabel
                text: "%(label)s"
                font.pixelSize: units.gu(3)
                anchors {
                    left: input.left
                    top: parent.top
                    topMargin: 25
                    bottomMargin: 25
                }
            }

            TextField {
                id: input;
                objectName: "input"
                anchors {
                    top: inputLabel.bottom
                    horizontalCenter: parent.horizontalCenter
                    topMargin: 10
                }
                inputMethodHints: %(input_method)s
            }
        }

        """ % {'label': label, 'input_method': extra_script})

        return self._start_qml_script(simple_script)


class UbuntuKeyboardTestsAccess(UbuntuKeyboardTests):

    def test_keyboard_is_available(self):
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)
        app = self._launch_simple_input()
        text_rectangle = app.select_single("QQuickTextInput")

        self.pointer.click_object(text_rectangle)

        self.assertThat(keyboard.is_available, Eventually(Equals(True)))


class UbuntuKeyboardTypingTests(UbuntuKeyboardTests):

    scenarios = [
        (
            'lower_alpha',
            dict(
                label="Lowercase",
                input='abcdefghijklmnopqrstuvwxyz'
            )
        ),
        (
            'upper_alpha',
            dict(
                label="Uppercase",
                input='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            )
        ),
        (
            'numeric',
            dict(
                label="Numeric",
                input='0123456789'
            )
        ),
        (
            'punctuation',
            dict(
                label="Puncuation",
                input='`~!@#$%^&*()_-+={}[]|\\:;"\'<>,.?/'
            )
        )
    ]

    def test_can_type_string(self):
        text_area = self.launch_test_input_area(label=self.label)
        self.ensure_focus_on_input(text_area)
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)

        keyboard.type(self.input)

        self.assertThat(text_area.text, Eventually(Equals(self.input)))


class UbuntuKeyboardStateChanges(UbuntuKeyboardTests):

    # Note: this is a failing test due to bug lp:1214695
    # Note: based on UX design doc
    def test_keyboard_layout_starts_shifted(self):
        """When first launched the keyboard state must be
        shifted/capitalised.

        """
        text_area = self.launch_test_input_area()
        self.ensure_focus_on_input(text_area)
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)

        self.assertThat(
            keyboard.keyboard.layoutState,
            Eventually(Equals(KeyboardState.SHIFTED))
        )

    def test_shift_latch(self):
        """Double tap of the shift key must lock it 'On' until the shift key
        tapped again.

        Normally hitting shift then a letter reverts from the shifted state
        back to the default. If double clicked it should stay in the shifted
        until the shift key is clicked again.

        """
        text_area = self.launch_test_input_area()
        self.ensure_focus_on_input(text_area)
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)

        keyboard.type('abc')
        keyboard.press_key('SHIFT')
        keyboard.press_key('SHIFT')
        keyboard.type('S')

        self.assertThat(
            keyboard.keyboard.layoutState,
            Eventually(Equals(KeyboardState.SHIFTED))
        )
        self.assertThat(text_area.text, Eventually(Equals('abcS')))

    # Note: based on UX design doc
    def test_shift_state_returns_to_default_after_letter_typed(self):
        """Pushing shift and then typing an uppercase letter must automatically
        shift the keyboard back into the default state.

        """
        text_area = self.launch_test_input_area()
        self.ensure_focus_on_input(text_area)
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)

        # Normally, type and (press_key) take care of shifting into the correct
        # state, we do it manually here as that's what we're testing.
        keyboard.type('abc')
        keyboard.press_key('SHIFT')
        keyboard.type('A')

        # Once the capital letter has been typed, we must be able to access the
        # lowercase letters, otherwise it's not in the correct state.
        self.assertThat(
            keyboard.keyboard.layoutState,
            Eventually(Equals(KeyboardState.DEFAULT))
        )

        self.assertThat(text_area.text, Eventually(Equals('abcA')))

    # Note: this is a failing test due to bug lp:1214695
    # Note: Based on UX design doc.
    def test_shift_state_entered_after_fullstop(self):
        """After typing a fullstop the keyboard state must automatically
        enter the shifted state.

        """
        text_area = self.launch_test_input_area()
        self.ensure_focus_on_input(text_area)
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)

        keyboard.type("abc.")

        self.assertThat(
            text_area.text,
            Eventually(Equals("abc."))
        )

        self.assertThat(
            keyboard.keyboard.layoutState,
            Eventually(Equals(KeyboardState.SHIFTED))
        )

    def test_switching_between_states(self):
        """The user must be able to type many different characters including
        spaces and backspaces.

        """
        text_area = self.launch_test_input_area()
        self.ensure_focus_on_input(text_area)
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)

        keyboard.type(
            'abc gone\b\b &  \bABC (123)'
        )

        expected = "abc go & ABC (123)"
        self.assertThat(
            text_area.text,
            Eventually(Equals(expected))
        )


class UbuntuKeyboardInputTypeStateChange(UbuntuKeyboardTests):
    """Note: these tests are currently failing due to bug lp:1214694 (the
    activeView detail isn't exposed correctly nor is it updated as expected
    (i.e. when the view changes.))

    """

    scenarios = [
        (
            "Url",
            dict(
                label="Url",
                hints=['Qt.ImhUrlCharactersOnly'],
                expected_activeview="url"
            )
        ),
        (
            "Password",
            dict(
                label="Password",
                hints=['Qt.ImhHiddenText', 'Qt.ImhSensitiveData'],
                expected_activeview="password"
            )
        ),
        (
            "Email",
            dict(
                label="Email",
                hints=['Qt.ImhEmailCharactersOnly'],
                expected_activeview="email"
            )
        ),
        (
            "Number",
            dict(
                label="Number",
                hints=['Qt.ImhFormattedNumbersOnly'],
                expected_activeview="number"
            )
        ),
        (
            "Telephone",
            dict(
                label="Telephone",
                hints=['Qt.ImhDigitsOnly'],
                expected_activeview="phonenumber"
            )
        ),
    ]

    # Note: based on UX design doc
    def test_keyboard_layout(self):
        """The Keyboard must respond to the input type and change to be the
        correct state.

        """
        text_area = self.launch_test_input_area(self.label, self.hints)
        self.ensure_focus_on_input(text_area)
        keyboard = Keyboard()
        self.addCleanup(keyboard.dismiss)

        self.assertThat(
            keyboard.keyboard.activeView,
            Eventually(Equals(self.expected_activeview))
        )