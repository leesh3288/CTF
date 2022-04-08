#!/usr/bin/env python3
# Based on cmark-gfm wrapper_ext sample source code
import ctypes

# Pin MMAP_THRESHOLD so that cmark_arenas are always mmaped & munmaped
libc = ctypes.CDLL('libc.so.6')
libc.mallopt(-3, 128*1024)

cmark = ctypes.CDLL('./libs/libcmark-gfm.so.0.29.0.gfm.2')
cmark_ext = ctypes.CDLL('./libs/libcmark-gfm-extensions.so.0.29.0.gfm.2')

# Options for the GFM rendering call
OPTS = 0  # defaults

# The GFM extensions that we want to use
EXTENSIONS = (
    b'autolink',
    b'table',
    b'strikethrough',
    b'tagfilter',
    b'tasklist',
)

# Use ctypes to access the functions in libcmark-gfm

F_cmark_parser_new_with_mem = cmark.cmark_parser_new_with_mem
F_cmark_parser_new_with_mem.restype = ctypes.c_void_p
F_cmark_parser_new_with_mem.argtypes = (ctypes.c_int, ctypes.c_void_p)

F_cmark_arena_reset = cmark.cmark_arena_reset
F_cmark_arena_reset.restype = None
F_cmark_arena_reset.argtypes = ( )

F_cmark_get_arena_mem_allocator = cmark.cmark_get_arena_mem_allocator
F_cmark_get_arena_mem_allocator.restype = ctypes.c_void_p
F_cmark_get_arena_mem_allocator.argtypes = ( )
P_CMARK_ARENA_MEM_ALLOCATOR = F_cmark_get_arena_mem_allocator()

F_cmark_parser_feed = cmark.cmark_parser_feed
F_cmark_parser_feed.restype = None
F_cmark_parser_feed.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t)

F_cmark_parser_finish = cmark.cmark_parser_finish
F_cmark_parser_finish.restype = ctypes.c_void_p
F_cmark_parser_finish.argtypes = (ctypes.c_void_p,)

F_cmark_parser_attach_syntax_extension = cmark.cmark_parser_attach_syntax_extension
F_cmark_parser_attach_syntax_extension.restype = ctypes.c_int
F_cmark_parser_attach_syntax_extension.argtypes = (ctypes.c_void_p, ctypes.c_void_p)

F_cmark_parser_get_syntax_extensions = cmark.cmark_parser_get_syntax_extensions
F_cmark_parser_get_syntax_extensions.restype = ctypes.c_void_p
F_cmark_parser_get_syntax_extensions.argtypes = (ctypes.c_void_p,)

F_cmark_find_syntax_extension = cmark.cmark_find_syntax_extension
F_cmark_find_syntax_extension.restype = ctypes.c_void_p
F_cmark_find_syntax_extension.argtypes = (ctypes.c_char_p,)

F_cmark_render_html = cmark.cmark_render_html
F_cmark_render_html.restype = ctypes.c_char_p
F_cmark_render_html.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)

# Set up the libcmark-gfm library and its extensions
F_register = cmark_ext.cmark_gfm_core_extensions_ensure_registered
F_register.restype = None
F_register.argtypes = ( )
F_register()

# Prepare list of extensions
syntax_exts = []
for name in EXTENSIONS:
    ext = F_cmark_find_syntax_extension(name)
    assert ext
    syntax_exts.append(ext)


def md2html(stream):
    try:
        parser = F_cmark_parser_new_with_mem(OPTS, P_CMARK_ARENA_MEM_ALLOCATOR)
        assert parser
        
        for ext in syntax_exts:
            rv = F_cmark_parser_attach_syntax_extension(parser, ext)
            assert rv
        exts = F_cmark_parser_get_syntax_extensions(parser)

        while True:
            chunk = stream.read(0x1000)
            if len(chunk) == 0:
                break
            F_cmark_parser_feed(parser, chunk, len(chunk))
        
        doc = F_cmark_parser_finish(parser)
        assert doc

        output = F_cmark_render_html(doc, OPTS, exts)
    except:
        output = b'<p>Error!</p>'
    finally:
        F_cmark_arena_reset()
    
    return output

def leak():
    return P_CMARK_ARENA_MEM_ALLOCATOR
