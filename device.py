#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  device module based on nvidia-installer by Antergos
#
#  Copyright © 2013-2017 Antergos
#  Copyright © 2019 Favourix <vladimir.kokes@favourix.com
#  This file is part of fx-drivers (Favourix OS Driver manager).
#
#  Favourix is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  Favourix is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#
#  You should have received a copy of the GNU General Public License
#  along with Favourix; If not, see <http://www.gnu.org/licenses/>.


import argparse
import getpass
import os
import logging
import subprocess
import sys
import devutils

LOG_FILE = "installer.log"

IDS_PATH = "pci"

YELLOW = '\033[93m'
GREEN = '\033[92m'
RED = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'

DEVICES = {
    "nvidia" : [],
    "nvidia-390xx" : [],
    "nvidia-340xx" : []
}


CLASS_ID = "0x03"
VENDOR_ID = str(devutils.get_gpu_vendor_id())

PACKAGES = {
    "nouveau": ["xf86-video-nouveau", "mesa"],
    "nvidia": ["nvidia-dkms", "libvdpau"],
    "nvidia-390xx": ["nvidia-390xx-dkms", "libvdpau"],
    "nvidia-340xx": ["nvidia-340xx-dkms", "libvdpau"],
    "bumblebee": ["bumblebee", "mesa", "xf86-video-intel",
                  "nvidia-dkms", "virtualgl", "nvidia-settings", "bbswitch-dkms"]}

PACKAGES_LTS = {
    "nouveau": [],
    "nvidia": ["nvidia-dkms"],
    "nvidia-390xx": ["nvidia-390xx-dkms"],
    "nvidia-340xx": ["nvidia-340xx-dkms"],
    "bumblebee": ["nvidia-dkms", "bbswitch-dkms"]}

PACKAGES_X86_64 = {
    "nouveau": ["lib32-mesa"],
    "nvidia": ["lib32-nvidia-utils", "lib32-libvdpau"],
    "nvidia-390xx": ["lib32-nvidia-390xx-utils", "lib32-libvdpau"],
    "nvidia-340xx": ["lib32-nvidia-340xx-utils", "lib32-libvdpau"],
    "bumblebee": ["lib32-nvidia-utils", "lib32-virtualgl", "lib32-mesa"]}

CONFLICTS = {
    "nouveau": ["nvidia-dkms", "nvidia-dkms", "nvidia-utils",
                "nvidia-390xx", "nvidia-390xx-dkms", "nvidia-390xx-utils",
                "nvidia-340xx", "nvidia-340xx-dkms", "nvidia-340xx-utils",
                "nvidia-304xx", "nvidia-304xx-lts", "nvidia-304xx-utils",
                "bumblebee", "virtualgl", "nvidia-settings", "bbswitch", "bbswitch-dkms"],
    "nvidia": ["xf86-video-nouveau"],
    "nvidia-390xx": ["xf86-video-nouveau"],
    "nvidia-340xx": ["xf86-video-nouveau"],
    "bumblebee": ["xf86-video-nouveau",
                  "nvidia-390xx-utils", "nvidia-340xx-utils", "nvidia-304xx-utils"]}

CONFLICTS_X86_64 = {
    "nouveau": ["lib32-nvidia-340xx-utils",
                "lib32-nvidia-304xx-utils", "lib32-nvidia-utils", "lib32-virtualgl"],
    "nvidia": ["lib32-nvidia-340xx-utils",
               "lib32-nvidia-304xx-utils"],
    "nvidia-390xx": ["lib32-nvidia-utils",
                     "lib32-nvidia-390xx-utils"],
    "nvidia-340xx": ["lib32-nvidia-utils",
                     "lib32-nvidia-340xx-utils"],
    "bumblebee": ["lib32-nvidia-390xx-utils",
                  "lib32-nvidia-340xx-utils", "lib32-nvidia-304xx-utils"]}

def parse_options():
    # Parse command line options
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-q", "--quiet",
        help="Supress log messages",
        action="store_true")


    return parser.parse_args()

def get_class_vendor_product(line):
    """ Parses lspci -n output line """
    line = line.split()
    class_id = "0x{}".format(line[1].rstrip(":")[0:2])
    dev = line[2].split(":")
    vendor_id = "0x{}".format(dev[0])
    product_id = "0x{}".format(dev[1])
    return (class_id, vendor_id, product_id)


def check_device():
    """ Tries to guess if a device suitable for this driver is present """
    try:
        cmd = ["/usr/bin/lspci", "-n"]
        lines = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        lines = lines.decode().split("\n")
    except subprocess.CalledProcessError as err:
        log_warning("Cannot detect hardware components : {}".format(err.output.decode()))
        return None

    drivers = []
    for line in lines:
        if line:
            class_id, vendor_id, product_id = get_class_vendor_product(line)

            if class_id == CLASS_ID and vendor_id == VENDOR_ID:
                for driver in DEVICES:
                    if product_id in DEVICES[driver]:
                        drivers.append(driver)
    return drivers


def install(driver, TEST):
    """ Performs packages installation """

    packages = PACKAGES[driver]
    conflicts = CONFLICTS[driver]

    if os.uname()[-1] == "x86_64":
        packages.extend(PACKAGES_X86_64[driver])
        conflicts.extend(CONFLICTS_X86_64[driver])

    if os.path.exists('/boot/vmlinuz-linux-lts'):
        packages.extend(PACKAGES_LTS[driver])

    log_info("Removing conflicting packages...")
    installed_packages = get_installed_packages()

    cmd = ["pacman", "-Rs", "--noconfirm", "--noprogressbar", "--nodeps"]
    for conflict in conflicts:
        if conflict in installed_packages:
            if TEST:
                log_info(" ".join(cmd + [conflict]))
            else:
                try:
                    subprocess.check_output(cmd + [conflict], stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as err:
                    msg = "Cannot remove conflicting package {0}: {1}"
                    log_error(msg.format(conflict, err.output.decode()))
                    return False

    log_info("Downloading and installing driver packages, please wait...")
    cmd = ["pacman", "-Sqy", "--noconfirm", "--noprogressbar"]
    cmd.extend(packages)
    if TEST:
        log_info(" ".join(cmd))
    else:
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            msg = "Cannot install required packages: {}"
            log_error(msg.format(err.output.decode()))
            return False

    return True


def get_installed_packages():
    """ Gets a list of all installed packages """
    installed_packages = []
    try:
        cmd = ["pacman", "-Q"]
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().split('\n')
        for line in res:
            line = line.split()
            if line:
                installed_packages.append(line[0])
    except subprocess.CalledProcessError as err:
        msg = "Cannot check installed packages (pacman -Q): {}"
        log_warning(msg.format(err.output.decode()))
    except OSError as err:
        msg = "Cannot check installed packages (pacman -Q): {}"
        log_warning(msg.format(err))
    return installed_packages


def add_user_to_group(user, group, TEST):
    """ Adds user to group in system """
    log_info("Adding user {0} to {1} group...".format(user, group))
    cmd = ["gpasswd", "-a", user, group]
    log_info(" ".join(cmd))
    if not TEST:
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            msg = "Cannot add user {0} to the {1} group: {2}"
            log_warning(msg.format(user, group, err.output.decode()))


def get_user():
    """ Gets current username """
    user = None
    try:
        user = os.environ['SUDO_USER']
    except KeyError:
        user = getpass.getuser()
    return user


def enable_service(service, enable, TEST):
    """ Enables service using systemctl """
    if not service.endswith(".service"):
        service += ".service"

    if os.path.exists("/usr/lib/systemd/system/{}".format(service)):
        cmd = ["systemctl"]
        if enable:
            log_info("Enabling {} service...".format(service))
            cmd += ["enable", service]
        else:
            log_info("Disabling {} service...".format(service))
            cmd += ["disable", service]
        log_info(" ".join(cmd))
        if not TEST:
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as err:
                msg = "Cannot enable/disable {0} service: {1}"
                log_warning(msg.format(service, err.output.decode()))


def patch_nvidia_settings(patch, TEST):
    """ Fixes nvidia-settings.desktop """
    desktop_path = "/usr/share/applications/nvidia-settings.desktop"
    if os.path.exists(desktop_path):
        exec1 = "Exec=/usr/bin/nvidia-settings"
        exec2 = "Exec=optirun -b none /usr/bin/nvidia-settings -c :8"
        if patch:
            log_info("Patching {}...".format(desktop_path))
            sed = "s|{0}|{1}|"
        else:
            log_info("Unpatching {}...".format(desktop_path))
            sed = "s|{1}|{0}|"
        sed = sed.format(exec1, exec2)
        cmd = ["/usr/bin/sed", "-i", sed, desktop_path]
        if TEST:
            log_info(" ".join(cmd))
        else:
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as err:
                msg = "Cannot modify {0} file : {1}"
                log_warning(msg.format(desktop_path, err.output.decode()))


def remove_file(path, TEST):
    """ Removes file if exists """
    if os.path.exists(path):
        log_info("Removing {} file...".format(path))
        if not TEST:
            os.remove(path)
    else:
        log_info("{} not found. That's ok.".format(path))


def create_nvidia_conf(path, TEST):
    """ Creates specific Xorg nvidia setup """
    log_info("Creating {} file...".format(path))
    if not TEST:
        with open(path, 'w') as nvidia:
            nvidia.write('Section "Device"\n')
            nvidia.write('    Identifier "Nvidia Card"\n')
            nvidia.write('    Driver "nvidia"\n')
            nvidia.write('    VendorName "NVIDIA Corporation"\n')
            nvidia.write('    Option "NoLogo" "true"\n')
            nvidia.write('EndSection\n')


def post_install(driver, TEST):
    """ Run post installation actions here """

    nvidia_conf_path = "/etc/X11/xorg.conf.d/20-nvidia.conf"

    if driver == "bumblebee":
        user = get_user()
        if user != "root":
            add_user_to_group(user, "bumblebee", TEST)
            add_user_to_group(user, "video", TEST)
        else:
            msg = "NOT adding user 'root' to bumblebee or video groups! " \
                "Remember to add your users to those groups"
            log_warning(msg)

        enable_service("bumblebeed.service", True, TEST)
        patch_nvidia_settings(True, TEST)
    else:
        # not bumblebee
        enable_service("bumblebeed.service", False, TEST)
        patch_nvidia_settings(False, TEST)

    if driver.startswith("nvidia"):
        create_nvidia_conf(nvidia_conf_path, TEST)
    else:
        # bumblebee and nouveau
        remove_file(nvidia_conf_path, TEST)

    fix_mkinitcpio(TEST)


def fix_mkinitcpio(TEST):
    """ Removes nouveau and nvidia from MODULES line in mkinitcpio.conf """

    mkinitcpio_path = "/etc/mkinitcpio.conf"

    # Read mkinitcpio.conf
    with open(mkinitcpio_path) as mkinitcpio_file:
        mklines = mkinitcpio_file.readlines()

    modified = False
    new_mklines = []
    for line in mklines:
        # Remove nouveau and nvidia from MODULES line (just in case)
        if line.startswith("MODULES"):
            if "nouveau" in line or "nvidia" in line:
                old_line = line
                line = line.replace("nouveau", "")
                line = line.replace("nvidia", "")
                line = line.replace(",,", ",")
                line = line.replace('",', '"')
                line = line.replace(',"', '"')
                msg = "{0} will be changed to {1} in {2}"
                log_info(msg.format(old_line.strip("\n"), line.strip("\n"), mkinitcpio_path))
                modified = True
        new_mklines.append(line)

    if modified and not TEST:
        try:
            with open(mkinitcpio_path, "w") as mkinitcpio_file:
                for line in new_mklines:
                    mkinitcpio_file.write(line)

            cmd = ["mkinitcpio", "-p", "linux"]
            res = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            res = res.decode().split('\n')

            if os.path.exists('/boot/vmlinuz-linux-lts'):
                cmd = ["mkinitcpio", "-p", "linux-lts"]
                res = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                res = res.decode().split('\n')
        except subprocess.CalledProcessError as err:
            msg = "Cannot run {0}: {1}, please run it manually before rebooting!"
            log_warning(msg.format(' '.join(cmd), err))
        except PermissionError:
            log_error("This script must be run with administrative privileges!")


def setup_logging(cmd_line):
    """ Configure our logger """
    logger = logging.getLogger()

    logger.handlers = []

    log_level = logging.INFO

    logger.setLevel(log_level)

    #context_filter = ContextFilter()
    #logger.addFilter(context_filter.filter)

    # Log format
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")

    # File logger
    try:
        file_handler = logging.FileHandler(LOG_FILE, mode='w')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError as permission_error:
        log_error("Can't open {0} : {1}".format(LOG_FILE, permission_error))

    # Stdout logger
    if not cmd_line.quiet:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        log_info("All logs will be stored in {}".format(LOG_FILE))


def log_error(msg):
    """ Log error message """
    msg = RED + msg + ENDC
    logging.error(msg)


def log_warning(msg):
    """ Log warning message """
    msg = YELLOW + msg + ENDC
    logging.warning(msg)


def log_info(msg):
    """ Log information message """
    msg = GREEN + msg + ENDC
    logging.info(msg)


def load_ids_file(path):
    """ Loads pci device numbers from a ids file """
    with open(path, 'r') as ids_file:
        lines = ids_file.readlines()

    for index, line in enumerate(lines):
        lines[index] = line.lower()

    ids = []
    for line in lines:
        ids.extend(line.split())

    for index, pci_id in enumerate(ids):
        ids[index] = "0x" + pci_id

    return ids


def load_ids():
    """ Load all nvidia devices pci ids """
    for item in os.listdir(IDS_PATH):
        if item.endswith('.ids') and "nvidia" in item:
            key = item[:-4]
            path = os.path.join(IDS_PATH, item)
            DEVICES[key] = load_ids_file(path)
