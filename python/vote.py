import vim
import os
import os.path
from pathlib import Path
from os import scandir, stat, umask, fsdecode
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
    bullets = ('•', '◦', '▸', '▹', '▪', '▫')

    def __init__(self):
        # take snapshot of config options at start
        self.conf = VoteConfig(
            root_dir = vim.eval("g:vote_note_dir"),
            extra_dirs = vim.eval(optional("g:vote_extra_dirs")),
            mode = vim.eval(optional("g:vote_default_file_mode")),
        )

        # ordinarily you should keep code with side effects out of __init__ and
        # just use this for creating stuff and setting up references, but i'm
        # ignoring that principle here because we know Vote will be a top-level
        # singleton object so there's nothing for the side effects to matter to
        self.ensure_folders()
        self.refs, self.backrefs = self._get_refs_and_backrefs()
        for path in self.dirs:
            self._ft_autocmd(path)

    @property
    def _root_dir(self):
        return Path(self.conf.root_dir).expanduser()

    @property
    def _extra_dirs(self):
        if self.conf.extra_dirs is None: return {}
        return {key: Path(val).expanduser() for key, val in self.conf.extra_dirs.items()}

    @property
    def dirs(self):
        yield self.conf.root_dir
        if self.conf.extra_dirs is not None:
            yield from self.conf.extra_dirs.values()

    @staticmethod
    def _input(prompt):
        vim.command('call inputsave()')
        vim.command('let user_input = input("' + prompt + ': ")')
        vim.command('call inputrestore()')
        return vim.eval('user_input')

    @staticmethod
    def _ft_autocmd(raw_path):
        tree = (Path(raw_path).expanduser() / "*").as_posix()
        vim.command(f'autocmd BufRead {tree} setlocal filetype=markdown')

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
        # NOTE: if it is configurable we will have to handle that in other places like self.notes() too
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
        names = self.notes
        refs = {name: [] for name in names}
        brefs = {name: [] for name in names}
        for src_name in names:
            path = self.parse_name(src_name)
            targets = list(names)
            found = []
            with open(path, "r") as f:  # TODO FIXME replace with grep
                for line in f:
                    for target in targets[:]:
                        if target in line:
                            found.append(target)
                            targets.remove(target)
                    if len(targets) == 0:
                        break
            refs[src_name] += found
            for dst_name in found:
                brefs[dst_name].append(src_name)
        return (refs, brefs)

    def _update_refs_and_backrefs(self):  # call this on writes, moves, etc
        self.refs, self.backrefs = self._get_refs_and_backrefs()  # TODO FIXME absurdly inefficient - should update dicts in-place & only look at changed files

    @property
    def notes(self):
        in_root_dir = tuple(fsdecode(entry.name) for entry in scandir(self._root_dir) if entry.is_file() and not entry.name.startswith("."))
        in_extra_dirs = tuple(key + ":" + fsdecode(entry.name)
                              for key, path in self._extra_dirs for entry in scandir(path) if entry.is_file() and not entry.name.startswith("."))
        return in_root_dir + in_extra_dirs
