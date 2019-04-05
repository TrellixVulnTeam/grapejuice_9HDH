import os

from gi.repository import Gtk

import install
import robloxctrl
import variables
import winectrl


class MainWindowHandlers:
    def on_destroy(self, *args):
        Gtk.main_quit()

    def run_winecfg(self, *args):
        winectrl.winecfg()

    def run_regedit(self, *args):
        winectrl.regedit()

    def run_winetricks(self, *args):
        winectrl.wine_tricks()

    def disable_mime_assoc(self, *args):
        winectrl.disable_mime_assoc()

    def sandbox(self, *args):
        winectrl.sandbox()

    def run_roblox_installer(self, *args):
        robloxctrl.run_installer()

    def run_roblox_studio(self, *args):
        if not robloxctrl.run_studio():
            dialog_text = "Roblox Studio could not be launched. You might have to install it first by going to "
            "the Maintanance tab."

            dialog = Gtk.MessageDialog(
                parent=self.window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=dialog_text
            )
            dialog.run()
            dialog.destroy()

    def wine_explorer(self, *args):
        winectrl.explorer()

    def apply_dll_overrides(self, *args):
        winectrl.load_dll_overrides()

    def open_drive_c(self, *args):
        os.spawnlp(os.P_NOWAIT, "xdg-open", "xdg-open", variables.wine_drive_c())

    def update_desktop_files(self, *args):
        install.install_desktop_files()

    def update_protocol_handlers(self, *args):
        install.update_protocol_handlers()


def move_children(source, target):
    for child in source.get_children():
        source.remove(child)
        target.add(child)


def load_window(glade_file, handlers, window_name):
    builder = Gtk.Builder()
    builder.add_from_file(glade_file)

    h = handlers()
    builder.connect_signals(h)
    window = builder.get_object(window_name)

    try:
        h.window = window
    except:
        pass

    return window, builder


def main_window():
    global uri_label
    window, builder = load_window("assets/grapejuice_main.glade", MainWindowHandlers, "main_window")

    return window
