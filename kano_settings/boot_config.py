#!/usr/bin/env python

# boot_config.py
#
# Copyright (C) 2014,2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Functions controlling reading and writing to /boot/config.txt
#

import re
import os
import sys
import shutil
from kano.utils import read_file_contents_as_lines
from kano.utils import is_number, open_locked
from kano.logging import logger

boot_config_standard_path = "/boot/config.txt"
boot_config_pi1_backup_path = "/boot/config_pi1_backup.txt"
boot_config_pi2_backup_path = "/boot/config_pi2_backup.txt"
tvservice_path = '/usr/bin/tvservice'
boot_config_safemode_backup_path = '/boot/config.txt.orig'


class BootConfig:
    def __init__(self, path=boot_config_standard_path):
        self.path = path
        self.dry_run = False

    def exists(self):
        return os.path.exists(self.path)

    def set_dry_run(self):
        """
        Set dry run mode. If set, no actual changes will be written to
        disk; instead more logging will happen.
        """
        self.dry_run = True

    def ensure_exists(self):
        if not self.exists():
            f = open_locked(self.path, "w")
            print >>f, "#"  # otherwise set_value thinks the file should not be written to

            # make sure changes go to disk
            f.flush()
            os.fsync(f.fileno())

            f.close()  # make file, even if empty

    def remove_noobs_defaults(self):
        """
        Remove the config entries added by Noobs,
        by removing all the lines after and including
        noobs' sentinel
        
        """
        if self.dry_run:
            logger.debug("Removing Noobs default values")
            return

        lines = read_file_contents_as_lines(self.path)
        noobs_line = "# NOOBS Auto-generated Settings:"
        if noobs_line in lines:
            with open_locked(self.path, "w") as boot_config_file:
                
                for line in lines:
                    if line == noobs_line:
                        break
                    
                    boot_config_file.write(line+ "\n")

                # flush changes to disk
                boot_config_file.flush()
                os.fsync(boot_config_file.fileno())

            return True
        return False
        

    def set_value(self, name, value=None):
        # if the value argument is None, the option will be commented out
        lines = read_file_contents_as_lines(self.path)
        if not lines:  # this is true if the file is empty, not sure that was intended.
            return

        logger.info('writing value to {} {} {}'.format(self.path, name, value))

        option_re = r'^\s*#?\s*' + str(name) + r'=(.*)'

        if self.dry_run:
            logger.debug("Setting config value {} in {} to {}".format(name, self.path, value))
            return

        with open_locked(self.path, "w") as boot_config_file:
            was_found = False

            for line in lines:
                if re.match(option_re, line):
                    was_found = True
                    if value is not None:
                        replace_str = str(name) + "=" + str(value)
                    else:
                        replace_str = r'#' + str(name) + r'=0'
                    new_line = replace_str
                else:
                    new_line = line

                boot_config_file.write(new_line + "\n")

            if not was_found and value is not None:
                boot_config_file.write(str(name) + "=" + str(value) + "\n")

            # flush changes to disk
            boot_config_file.flush()
            os.fsync(boot_config_file.fileno())

    def get_value(self, name):
        lines = read_file_contents_as_lines(self.path)
        if not lines:
            return 0

        for l in lines:
            if l.startswith(name + '='):
                value = l.split('=')[1]
                if is_number(value):
                    value = int(value)
                return value

        return 0

    def set_comment(self, name, value):
        lines = read_file_contents_as_lines(self.path)
        if not lines:
            return

        logger.info('writing comment to {} {} {}'.format(self.path, name, value))

        comment_str_full = '### {}: {}'.format(name, value)
        comment_str_name = '### {}'.format(name)

        if self.dry_run:
            logger.debug("setting comment {} in {} to {}".format(name, self.path, value))
            return

        with open_locked(self.path, "w") as boot_config_file:
            boot_config_file.write(comment_str_full + '\n')

            for line in lines:
                if comment_str_name in line:
                    continue

                boot_config_file.write(line + '\n')

            # make sure changes go to disk
            boot_config_file.flush()
            os.fsync(boot_config_file.fileno())

    def get_comment(self, name, value):
        lines = read_file_contents_as_lines(self.path)
        if not lines:
            return False

        comment_str_full = '### {}: {}'.format(name, value)
        return comment_str_full in lines

    def has_comment(self, name):
        lines = read_file_contents_as_lines(self.path)
        if not lines:
            return False

        comment_start = '### {}:'.format(name)
        for l in lines:
            if l.startswith(comment_start):
                return True

        return False


real_config = BootConfig()
pi1_backup_config = BootConfig(boot_config_pi1_backup_path)
pi2_backup_config = BootConfig(boot_config_pi2_backup_path)

def set_dry_run():
    """
    Set dry run on all config files.
    """
    real_config.set_dry_run()
    pi1_backup_config.set_dry_run()
    pi2_backup_config.set_dry_run()
    


def set_config_value(name, value=None):
    real_config.set_value(name, value)


def get_config_value(name):
    return real_config.get_value(name)


def set_config_comment(name, value):
    real_config.set_comment(name, value)


def get_config_comment(name, value):
    return real_config.get_comment(name, value)


def has_config_comment(name):
    return real_config.has_comment(name)

def remove_noobs_defaults():
    return real_config.remove_noobs_defaults()


def enforce_pi():
    pi_detected = os.path.exists(tvservice_path) and \
        os.path.exists(boot_config_standard_path)
    if not pi_detected:
        logger.error('need to run on a Raspberry Pi')
        sys.exit()


def is_safe_boot():
    """ Test whether the unit is booting in the safe mode already. """

    return os.path.isfile(boot_config_safemode_backup_path)


def safe_mode_backup_config():
    shutil.copy2(boot_config_standard_path, boot_config_safemode_backup_path)


def safe_mode_restore_config():
    shutil.move(boot_config_safemode_backup_path, boot_config_standard_path)
