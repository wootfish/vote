# vote
vim-notes spiritual successor with emphasis on tracking links between notes.

Optional dependency: pydantic (provides config typechecking)

Extra note dirs are handled by separate paths rather than symlinks because in principle this means we get to use arbitrary URIs for them
(though in practice I don't think that will work yet because the Python code assumes they're always file paths)

NOTE: If ~/Documents/notes exists, this plugin will do its business there unless told not to
so if you already have that folder and you don't want it touched then fucken uh take care of that before running this
probably u want to set g:vote_root_dir to somewhere else

TKTK
