"""
Fuzzy File Navigation

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
Edited by Liam Cain
"""

import sublime
import sublime_plugin
import os
import os.path as path
import re

PLATFORM = sublime.platform()

KILO = 1024
MEGA = 1048576
GIGA = 1073741824
TERA = 1099511627776


class FuzzyStartFromFileCommand(sublime_plugin.TextCommand):
    def run(self, edit, regex_exclude=[]):
        name = self.view.file_name()
        if name:
            self.view.window().run_command("pikachoose", {"start": path.dirname(name), "regex_exclude": regex_exclude})

class PikachooseListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        sel = view.sel()[0]
        line_text = view.substr(view.line(sel))
        if key == "pikachoose_window_showing":
           return PikachooseCommand.active == operand
        if key == "at_pikachoose_start":
          return (PikachooseCommand.active and len(line_text) < 1) == operand

    # def on_modified(self,view):

class PikachooseShowHiddenCommand(sublime_plugin.WindowCommand):
    def run(self, regex_exclude=[]):
        start = PikachooseCommand.cwd
        self.window.run_command("pikachoose", {"start": start, "regex_exclude": regex_exclude})

class PikachooseCommand(sublime_plugin.WindowCommand):
    active = False
    def run(self, start=None, regex_exclude=[]):
        if PikachooseCommand.active:
            self.window.run_command("hide_overlay")
        PikachooseCommand.active = True
        self.regex_exclude = regex_exclude
        print regex_exclude
        PikachooseCommand.cwd = self.get_root_path() if start == None or not path.exists(start) or not path.isdir(start) else unicode(start)
        self.get_files(PikachooseCommand.cwd)

    def exclude(self, files, cwd):
        folders = []
        documents = []
        for f in files:
            valid = True
            full_path = path.join(cwd, f)
            count = 0
            size = 0
            file_type = ""
            if path.isdir(full_path):
                try:
                    count = os.listdir(full_path)
                    file_type = "directory"
                except:
                    valid = False
            else:
                try:
                    size = self.format_size(os.path.getsize(full_path))
                    file_type = "file"
                except:
                    valid = False
            if valid:
                for regex in self.regex_exclude:
                    if re.match(regex, f):
                        valid = False
            if valid == True:
                if file_type == "file":
                    documents.append([f, u"File: %s" % size])
                else:
                    folders.append([f, u"Folder: %d files" % len(count)])
        return sorted(folders) + sorted(documents)

    def get_root_path(self):
        return u"" if PLATFORM == "windows" else u"/"

    def get_files(self, cwd):
        self.files = [[u"..",cwd]] + self.exclude(self.get_drives() if PLATFORM == "windows" and cwd == u"" else os.listdir(cwd), cwd)
        self.window.show_quick_panel(self.files, self.check_selection)

    def back_dir(self, cwd):
        prev = path.dirname(path.dirname(cwd))
        return self.get_root_path() if prev == cwd else prev

    def get_drives(self):
        return [unicode(d + ":\\") for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if path.exists(d + ":")]

    def check_selection(self, selection):
        if selection == -1:
            PikachooseCommand.active = False
        else:
            PikachooseCommand.cwd = self.back_dir(self.cwd) if selection == 0 else path.join(PikachooseCommand.cwd, self.files[selection][0])
            if (path.isdir(self.cwd) or PikachooseCommand.cwd == self.get_root_path()):
                self.get_files(PikachooseCommand.cwd)
            else:
                # self.window.open_file(self.cwd,sublime.TRANSIENT)
                self.window.open_file(PikachooseCommand.cwd)

    def format_size(self, bytes):
        bytes = float(bytes)
        if bytes < KILO:
            return str(bytes) + ' B'
        elif bytes < MEGA:
            return str(round(bytes / KILO, 2)) + ' KB'
        elif bytes < GIGA:
            return str(round(bytes / MEGA, 2)) + ' MB'
        elif bytes < TERA:
            return str(round(bytes / GIGA, 2)) + ' GB'
        else:
            return str(round(bytes / TERA, 2)) + ' TB'
