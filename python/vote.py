import vim
import os
import os.path
from pathlib import Path
from os import scandir, stat, umask
try:
    from pydantic.dataclasses import dataclass
except ImportError:
    from dataclasses import dataclass


class VoteError(Exception): pass


@dataclass
class VoteConfig:
    root_dir: str = "~/Documents/notes/"
    extra_dirs: None | dict[str, str] = None  # TODO
    mode: None | int = 0o640  # TODO
    cache: None | str = None  # TODO


def optional(var):
    assert var.startswith("g:")
    return f'get(g:, "{var[2:]}", v:none)'


class Vote:
    def __init__(self):
        # take snapshot of config options at start
        self.conf = VoteConfig(
            root_dir = vim.eval("g:vote_note_dir"),
            extra_dirs = vim.eval(optional("g:vote_extra_dirs")),
            mode = vim.eval(optional("g:vote_default_file_mode")),
        )

        # ordinarily you should keep code with side effects out of __init__ and
        # just use this for creating stuff and setting up references but i'm
        # ignoring that principle here because we know Vote will be a top-level
        # singleton object so there's nothing for the side effects to matter to
        self.ensure_folders()
        self.refs, self.backrefs = self._get_refs_and_backrefs()

    @staticmethod
    def _input(prompt):
        vim.command('call inputsave()')
        vim.command('let user_input = input("' + prompt + ': ")')
        vim.command('call inputrestore()')
        return vim.eval('user_input')

    def ensure_folders(self):
        paths = [self.conf.root_dir] + list((self.conf.extra_dirs or {}).values())
        for path in paths:
            Path(path).expanduser().mkdir(parents=True, exist_ok=True)

    def add_note(self, name=None):
        name = name or self._input("Enter new note's title")
        self._add_note(name)

    def parse_name(self, name):
        # parses eg newnote -> ("newnote", root_dir), tech:newnote -> ("newnote", extra_dirs["tech"])
        # NOTE: assumes ":" indicates a prefix, so note names with ":" in them are not allowed here, but they are otherwise legal and you can still rename a note to include them
        # NOTE: re above, maybe make the split metacharacter configurable? like it defaults to ":" but you can reassign it? TODO add this once the important stuff is stable
        if ":" in name:
            prefix, name = name.split(":", 1)
            if self.conf.extra_dirs is None or prefix not in self.conf.extra_dirs:
                raise VoteError("prefix not recognized")
        else:
            path = self.conf.root_dir
        return Path(path).expanduser() / Path(name)  # lol this concatenation operator rules

    def _add_note(self, name):
        note_path = self.parse_name(name)  # parse name (possibly of the form prefix:notename) into file's absolute path
        if not note_path.is_file():  # NOTE: technically there's a tiny race condition here. better would be to open unconditionally, but not truncate. TODO figure that out
            # create file with proper permissions and path, then close it
            os.umask(0o000)  # ooooOOoo... umask's haunted
            opener = lambda path, flags: os.open(path, flags, self.conf.mode or 0o640)
            open(note_path, "w", opener=opener).close()
        # open the new file in the currently focused buffer
        self.open_note(name)

    def open_note(self, name):
        note_path = self.parse_name(name)  # parse name (possibly of the form prefix:notename) into file path
        vim.command("e " + note_path.as_posix())

    def _get_refs_and_backrefs(self):
        ...  # TODO
        return (None, None)

    def _update_refs_and_backrefs(self):  # call this on writes, moves, etc
        ...  # TODO

    @property
    def notes(self):
        # tuple of recognized note names
        ...  # TODO
