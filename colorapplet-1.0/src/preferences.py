"""
Preferences per-applet or shared between applets
"""
import os, sys
from os.path import join, exists, isdir, isfile, dirname, abspath, expanduser
import gconf
import gtk
from globals import *

UNINSTALLED = False
def _check(path):
	return exists(path) and isdir(path) and isfile(path+"/TODO")
	
TMP_NAME = join(dirname(__file__), '..')
if _check(TMP_NAME):
	UNINSTALLED = True

if UNINSTALLED:
    SHARED_DATA_DIR = abspath(join(dirname(__file__), '..', 'data'))
else:
    SHARED_DATA_DIR = join(DATA_DIR, "colorpicker")
#print "Data dir: %s" % SHARED_DATA_DIR

USER_STARTLET_DIR = expanduser("~/.config/colorpicker")
if not exists(USER_STARTLET_DIR):
    try:
        os.makedirs(USER_STARTLET_DIR, 0744)
    except Exception, msg:
        print 'Error: could not create user dir (%s): %s' % (USER_STARTLET_DIR, msg)

os.chdir(expanduser("~"))

GCONF_CLIENT = gconf.client_get_default()
GCONF_DIR = "/apps/colorpicker"

GCONF_CLIENT.add_dir(GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)

def more_information_dialog(parent, title, content):
	message_dialog = gtk.MessageDialog(parent=parent, buttons=gtk.BUTTONS_CLOSE)
	message_dialog.set_markup("<span size='larger' weight='bold'>%s</span>\n\n%s" % (cgi.escape(title), cgi.escape(content)))
	resp = message_dialog.run()
	if resp == gtk.RESPONSE_CLOSE:
		message_dialog.destroy()

def get_xdg_data_dirs():
    dirs = os.getenv("XDG_DATA_HOME")
    if dirs == None:
	dirs = expanduser("~/.local/share")
    
    sysdirs = os.getenv("XDG_DATA_DIRS")
    if sysdirs == None:
        sysdirs = "/usr/local/share:/usr/share"
    
    dirs = "%s:%s" % (dirs, sysdirs)
    return [dir for dir in dirs.split(":") if dir.strip() != "" and exists(dir)]

def copy_to_desktop(desktop_file):
    dst = os.path.expanduser("~/Desktop/")
    shutil.copy(desktop_file, dst)

def get_desktop_file(desktop_id):
    dirs = get_xdg_data_dirs()
    for dir in dirs:
        fl = dir + "/" + desktop_id
        print fl

class AppletPreferences:
    def __init__(self, applet):
        self.GCONF_APPLET_DIR = GCONF_DIR
        
        path = applet.get_preferences_key()
        if path != None:
            self.GCONF_APPLET_DIR = path

            applet.add_preferences("/schemas" + GCONF_DIR)
            GCONF_CLIENT.add_dir(self.GCONF_APPLET_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)

            print 'Using per-applet gconf key:', self.GCONF_APPLET_DIR

