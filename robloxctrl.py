import os

import wget

import variables
import winectrl

DOWNLOAD_URL = "https://www.roblox.com/install/setup.ashx"


def get_installer():
    install_path = variables.installer_path()

    if os.path.exists(install_path):
        os.remove(install_path)

    wget.download(DOWNLOAD_URL, install_path)


def run_installer():
    winectrl.create_prefix()
    get_installer()
    winectrl.run_exe(variables.installer_path())


def locate_in_versions(exe_name):
    versions = os.path.join(variables.wine_roblox_prog(), "Versions")
    if not os.path.exists(versions):
        return None

    for dir in os.listdir(versions):
        fp = os.path.join(versions, dir)
        if os.path.isdir(fp):
            lp = os.path.join(fp, exe_name)
            if os.path.exists(lp) and os.path.isfile(lp):
                return lp


def locate_studio_launcher():
    versioned_launcher = locate_in_versions("RobloxStudioLauncherBeta.exe")
    if not versioned_launcher:
        launcher = os.path.join(variables.wine_roblox_prog(), "Versions", "RobloxStudioBetaLauncher.exe")
        if os.path.exists(launcher):
            return launcher

    return versioned_launcher


def locate_player_launcher():
    return locate_in_versions("RobloxPlayerLauncher.exe")


def run_studio(uri=""):
    launcher = locate_studio_launcher()
    if launcher is None:
        return False

    if uri:
        winectrl.run_exe(launcher, uri)
    else:
        winectrl.run_exe(launcher)

    return True


def run_player(uri):
    player = locate_player_launcher()
    if player is None:
        return False

    winectrl.run_exe(player, uri)
    return True
