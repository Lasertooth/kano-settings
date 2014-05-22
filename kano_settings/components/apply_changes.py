#!/usr/bin/env python

# apply_changes.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# This controls the style of the main button in the projects that applies the changes

from gi.repository import Gtk
import kano_settings.components.cursor as cursor


class Apply():

    def __init__(self, name=""):

        # Create button
        self.button = Gtk.Button(name)

        # Get rid of annoying dotted borders around click buttons
        # TODO: change styling so the focus border is less intrusive
        self.button.set_can_focus(False)

        # Allows button to be styled in css
        self.button_style = self.button.get_style_context()
        self.button_style.add_class("apply_changes_button")
        self.button_style.add_class("green")
        cursor.attach_cursor_events(self.button)

        # This stops the button resizing to fit the size of it's container
        self.box = Gtk.Box()
        self.box.pack_start(self.button, False, False, 0)
        self.box.props.halign = Gtk.Align.CENTER

    def enable(self):
        self.button.set_sensitive(True)

    # styling of disabled button is in style.css
    def disable(self):
        self.button.set_sensitive(False)

    def grey_background(self):
        self.button_style.add_class("grey")
        self.button_style.remove_class("green")

    def green_background(self):
        self.button_style.add_class("green")
        self.button_style.remove_class("grey")

    def set_text(self, text):
        self.button.set_label(text)
