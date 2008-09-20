#!/usr/bin/env python
import pygtk
import sys
pygtk.require('2.0')

import gtk
import gnome
import gnome.ui
import gnomeapplet
import subprocess
import gobject

from colorpicker.globals import *
from colorpicker.preferences import *

MAX_HISTORY = 16

gnome.program_init("colorpicker", "1.0")

def color_to_string(clr):
    return '#%02x%02x%02x' % (clr.red/256, clr.green/256, clr.blue/256)

def lighten(clr):
    newclr = gtk.gdk.Color(clr.red+(16*256), clr.green+(16*256), clr.blue+(16*256))
    if newclr.red > 65535:
        newclr.red = 65535
    if newclr.green > 65535:
        newclr.green = 65535
    if newclr.blue > 65535:
        newclr.blue = 65535
    return newclr

def darken(clr):
    newclr = gtk.gdk.Color(clr.red-(16*256), clr.green-(16*256), clr.blue-(16*256))
    if clr.red < 16*256:
        newclr.red = 0
    if clr.green < 16*256:
        newclr.green = 0
    if clr.blue < 16*256:
        newclr.blue = 0
    return newclr

def pixbuf_from_color(clr):
    clrs = color_to_string(clr)
    #lightclr = color_to_string(lighten(clr))
    darkclr = color_to_string(darken(clr))
    xpmimg = [
            "16 16 3 1",
            "a c " + clrs,
            "- c " + darkclr,
            "  c #555753",
            "                ",
            " aaaaaaaaaaaaaa ",
            " aaaaaaaaaaaaaa ",
            " aaaaaaaaaaaaaa ",
            " aaaaaaaaaaaaaa ",
            " aaaaaaaaaaaaaa ",
            " aaaaaaaaaaaaaa ",
            " aaaaaaaaaaaaaa ",
            " -------------- ",
            " -------------- ",
            " -------------- ",
            " -------------- ",
            " -------------- ",
            " -------------- ",
            " -------------- ",
            "                "
            ]
    return gtk.gdk.pixbuf_new_from_xpm_data(xpmimg)

def store_color_in_clipboard(color):
    color_name = color_to_string(color)
    clipboard = gtk.Clipboard(selection="PRIMARY")
    clipboard.set_text(color_name)
    clipboard.store()


def open_color_picker():
    dialog = gtk.ColorSelectionDialog(u'Select Color\u2026')
    dialog.set_icon_name(gtk.STOCK_SELECT_COLOR)
    dialog.ok_button.hide()
    dialog.add_button(gtk.STOCK_COPY, gtk.RESPONSE_OK)
    dialog.set_default_response(gtk.RESPONSE_OK)

    result = dialog.run()

    if result == gtk.RESPONSE_OK:
        color = dialog.colorsel.get_current_color()
        store_color_in_clipboard(color)

def open_gcolor2():
    subprocess.Popen(("gcolor2", ""))

class ColorPicker:
    def __init__(self, applet):
        self.prefs = AppletPreferences(applet)
        self.menuXML = """
        <popup name = "button3">
        <menuitem
            name = "Prefs"
            verb = "Prefs"
            _label = "Preferences"
            pixtype = "stock"
            pixname = "gtk-properties"
        />
        <menuitem
            name = "About"
            verb = "About"
            _label = "About dialog"
            pixtype = "stock"
            pixname = "gtk-properties"
        />
        </popup>
        """

        self.menuVerbs = [("Prefs", self.menu_about), ("About", self.menu_about)]

        applet.set_flags(gnomeapplet.EXPAND_MINOR)
        applet.setup_menu(self.menuXML, self.menuVerbs, None)

        self.color = gtk.gdk.Color(65000, 65000, 65535)
        self.applet = applet
        self.hbox = gtk.HBox()
        self.tooltips = gtk.Tooltips()
        self.button = gtk.Button("")
        self.button.set_relief(gtk.RELIEF_NONE)
        self.image = gtk.Image()
        #self.image.set_from_stock(gtk.STOCK_COLOR_PICKER, gtk.ICON_SIZE_BUTTON)
        self.update_image()
        self.button.connect("button-press-event", self.button_pressed)
        self.button.connect("enter-notify-event", self.enter_notify)
        self.hbox.add(self.button)
        
        applet.add(self.hbox)
        applet.show_all()

        self.load()
    
    def menu_about(self, widget, data):
        theme = gtk.icon_theme_get_default()
        pix = theme.load_icon('gnome-settings-background', 128, 0)

        gnome.ui.About('Color Picker',
                '1.0',
                'Copyright 2007 Kristoffer Gronlund',
                'Color picker applet',
                ['Kristoffer Gronlund <kegie@undiscoverable.com>'],
                [],
                None,
                pix).show()

    def enter_notify(self, widget, event):
        self.update_tooltip()

    def update_tooltip(self):
        self.tooltips.set_tip(self.hbox, color_to_string(self.color))
        self.tooltips.enable()

    def update_image(self):
        self.image.set_from_pixbuf(pixbuf_from_color(self.color))
        self.button.set_image(self.image)

    def button_pressed(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            #self.show_menu(widget, event) # show menu / history of colors
            self.applet.emit("button-press-event", event)
        elif event.type == gtk.gdk.BUTTON_PRESS and event.button == 2:
            self.show_menu(widget, event)
            store_color_in_clipboard(self.color)
            self.save()
        elif event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            # show color picker
            # todo: make small window that popups near button with picker in it
            colorsel = gtk.ColorSelectionDialog("Pick color")
            colorsel.colorsel.set_has_palette(True)
            colorsel.colorsel.set_current_color(self.color)
            colorsel.show()
            response = colorsel.run()
            if response == gtk.RESPONSE_OK:
                self.color = colorsel.colorsel.get_current_color()
                self.history.append(self.color)
                if len(self.history) > MAX_HISTORY:
                    self.history.pop(0)
                self.update_image()
                self.update_tooltip()
                self.rebuild_menu()
                #item = self.color_menuitem(self.color)
                #self.menu.add(item)
                store_color_in_clipboard(self.color)
                self.save()
            colorsel.hide()
            gtk.Widget.destroy(colorsel)

    def color_menuitem(self, color):
        item = gtk.ImageMenuItem(color_to_string(color))
        img = gtk.Image()
        img.set_from_pixbuf(pixbuf_from_color(color))
        item.set_image(img)
        return item

    def show_menu(self, widget, event):
        #self.menu.popup(None, None, lambda (menu):
        #        self.resizer(menu, widget), event.button, event.time)
        self.menu.show_all()
        self.menu.popup(None, None, None, event.button, event.time)

    def rebuild_menu(self):
        self.menu = gtk.Menu()
        agave = gtk.ImageMenuItem("agave")
        agaveimage = gtk.Image()
        agaveimage.set_from_stock(gtk.STOCK_COLOR_PICKER, gtk.ICON_SIZE_MENU)
        agave.set_image(agaveimage)

        agave.connect('button-press-event', self.start_agave)

        self.menu.add(agave)
        self.menu.add(gtk.SeparatorMenuItem())

        for i in self.history:
            clr = self.color_menuitem(i)
            clr.connect('button-press-event', self.color_selected, i)
            self.menu.add(clr)
        
        self.menu.add(gtk.SeparatorMenuItem())
        clr = self.color_menuitem(self.color)
        clr.connect('button-press-event', self.color_selected, self.color)
        self.menu.add(clr)

    def start_agave(self, menuitem, event):
        subprocess.Popen(("agave", ""))

    def color_selected(self, menuitem, event, color):
        self.color = color
        self.update_image()
        self.update_tooltip()
        self.rebuild_menu()
        self.save()
        store_color_in_clipboard(color)

    def resizer(self, menu, widget):
        (px,py) = widget.window.get_root_origin()
        r = widget.get_allocation()
        r.x += px
        r.y += py
        (mx,my) = menu.size_request()
        wAlign = 1
        hAlign = 1
        if wAlign == 1:
            if hAlign == 0:
                return (r.x - mx, r.y, True)
            else:
                return (r.x - mx, r.y - my + r.height, True)
        else:
            if hAlign == 0:
                return (r.x + r.width, r.y, True)
            else:
                return (r.x + r.width, r.y - my + r.height, True)

    def save(self):
        #self.history = []
        file = open(USER_STARTLET_DIR + "/history", "w")
        if file:
            for thing in self.history:
                file.write(color_to_string(thing) + "\n")
            

    def load(self):
        self.history = []

        if os.path.exists(USER_STARTLET_DIR + "/history"):

            file = open(USER_STARTLET_DIR + "/history", "r")

            if file:
                lines = file.readlines()
                for line in lines:
                    line2 = line[:-1]
                    if len(line2) < 7:
                        continue
                    self.history.append(gtk.gdk.color_parse(line2))
        self.color = self.history[-1]
        self.rebuild_menu()
        self.update_image()
     

#gobject.type_register(ColorPicker)

def sample_factory(applet, iid):
    picker = ColorPicker(applet)
    return True


if len(sys.argv) == 2:
    if sys.argv[1] == "run-in-window":
        main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        main_window.set_title("Color Applet")
        main_window.connect("destroy", gtk.main_quit)
        app = gnomeapplet.Applet()
        sample_factory(app, None)
        app.reparent(main_window)
        main_window.show_all()
        gtk.main()
        sys.exit()

gnomeapplet.bonobo_factory("OAFIID:GNOME_ColorApplet_Factory",
                                     gnomeapplet.Applet.__gtype__,
                                     "colorpicker", "1.0", sample_factory)

