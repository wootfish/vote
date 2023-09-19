" quit if vote is disabled
if exists('g:vote_plugin_disable')
    finish
endif

" quit if vote has already been loaded
if exists('g:vote_plugin_loaded')
    finish
endif

" default note dir
if !exists('g:vote_note_dir')
    let g:vote_note_dir = "~/Documents/notes"
endif

" quit if python3 is not available
if !has("python3")
    echo "vote requires vim to be compiled with python3 support"
    finish
endif

" get plugin's root dir
let s:vote_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

" add plugin's root dir to pythonpath, then import and run main class
python3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:vote_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
from vote import Vote
vote = Vote()
EOF

function! VoteStart()
    execute 'cd' g:vote_note_dir
    NERDTree
    normal CD
    wincmd p
    q
    normal j
    " TODO is there anything more to do here?
endfunc

" command bindings
command -nargs=0 VoteStart :call VoteStart()
command -nargs=? NoteNew :python3 vote.add_note("<args>")
command -nargs=1 NoteOpen :python3 vote.open_note("<args>")

" indicate that this file has been run
let g:vote_plugin_loaded = 1
