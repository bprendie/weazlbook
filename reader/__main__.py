"""Run: python -m reader library/ --gui; or --render book.epub output.png."""
import argparse
import json
import multiprocessing as mp
from pathlib import Path
import resource
from .documents import load
from .state import Store
from .session import Session
from .layout import render, FONT


def worker(path, out):
    resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    try: out.send((True, load(path)))
    except Exception as e: out.send((False, str(e)))
    finally: out.close()


def bounded_load(path):
    receive, send = mp.Pipe(False)
    p = mp.Process(target=worker, args=(str(path), send)); p.start(); send.close()
    try:
        if not receive.poll(25): raise ValueError('Import exceeded resource/time budget')
        ok, result = receive.recv()
        if not ok: raise ValueError(result)
        return result
    except EOFError as e: raise ValueError('Import failed or exceeded resource budget') from e
    finally:
        p.join(0.1)
        if p.is_alive(): p.terminate(); p.join()
        receive.close()


def gui(library, store):
    import tkinter as tk
    from tkinter import simpledialog, messagebox
    from PIL import ImageTk, Image, ImageDraw, ImageFont
    root = tk.Tk(); root.title('WeazlBook R05 — offline reference reader')
    screen = tk.Label(root); screen.pack()
    paths = sorted(p for p in Path(library).iterdir() if p.suffix.lower() in ('.epub', '.pdf', '.md', '.markdown'))
    current = None; mode = 'library'; selected = 0; entries = []
    def draw():
        nonlocal entries
        if mode == 'reading': im = render(current.book, current.page, current.position, len(current.pages), current.size)
        else:
            im = Image.new('1', (480,800), 1); d = ImageDraw.Draw(im); f = ImageFont.truetype(str(FONT), 18)
            if mode == 'library': entries = [(p.stem, p) for p in paths]
            elif mode == 'marks': entries = [(m['name'], m['anchor']) for m in store.book(current.book.identity)['bookmarks']]
            else: entries = current.book.toc
            d.text((20,20), mode.upper(), font=f, fill=0)
            first = max(0, selected - 15)
            for i, (name, _) in enumerate(entries[first:first+19], first):
                d.text((20,70+(i-first)*30), ('> ' if i == selected else '  ')+name[:35], font=f, fill=0)
            d.text((20,700), 'Arrows: move  Enter: SELECT\nEsc: BACK  m: MARK  b: marks\nt: contents  +/-: text size', font=f, fill=0)
        pic = ImageTk.PhotoImage(im); screen.configure(image=pic); screen.image = pic
    def key(e):
        nonlocal current, mode, selected
        k = e.keysym
        try:
            if mode == 'reading':
                if k in ('Left','Right'): current.turn(-1 if k == 'Left' else 1)
                elif k in ('plus','equal','minus'):
                    sizes = (20,24,28); current.resize(sizes[max(0,min(2,sizes.index(current.size)+(1 if k != 'minus' else -1)))])
                elif k == 'm':
                    name = simpledialog.askstring('MARK', 'Bookmark name:', parent=root)
                    if name is not None: current.bookmark(name)
                elif k in ('b','t'): mode = 'marks' if k == 'b' else 'contents'; selected = 0
                elif k == 'Escape': current.save(); mode = 'library'; selected = 0
            else:
                if k in ('Up','Down'): selected = max(0,min(len(entries)-1,selected+(-1 if k=='Up' else 1)))
                elif k == 'Escape': mode = 'reading' if current else 'library'
                elif k == 'Return' and entries:
                    value = entries[selected][1]
                    if mode == 'library':
                        book = bounded_load(value); current = Session(book, store)
                        if book.warnings: messagebox.showinfo('Import notes', '\n'.join(book.warnings[:20]))
                    elif mode == 'marks': current.jump(value)
                    else: current.source(value)
                    mode = 'reading'
            draw()
        except Exception as exc: messagebox.showerror('Cannot complete action', str(exc))
    root.bind('<Key>', key)
    def close():
        if current: current.save()
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', close); draw(); root.mainloop()


def main():
    p = argparse.ArgumentParser(); p.add_argument('library', nargs='?', default='fixtures')
    p.add_argument('--state', default='.reader-state'); p.add_argument('--gui', action='store_true')
    p.add_argument('--render', nargs=2, metavar=('BOOK','PNG')); p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, choices=(20,24,28), default=24)
    p.add_argument('--export-state'); p.add_argument('--import-state')
    a = p.parse_args(); store = Store(a.state)
    if a.import_state: store.merge(a.import_state)
    if a.export_state: store.export(a.export_state)
    if a.render:
        b = bounded_load(a.render[0]); s = Session(b, store, a.size)
        s.position = max(0,min(len(s.pages)-1,a.page-1))
        render(b,s.page,s.position,len(s.pages),s.size).save(a.render[1])
        print(json.dumps({'title':b.title,'pages':len(s.pages),'warnings':b.warnings})); return
    if a.gui: gui(a.library, store)
    elif not (a.export_state or a.import_state):
        for path in sorted(Path(a.library).glob('*')):
            if path.suffix.lower() in ('.epub','.pdf'): print(path)
        print('Use --gui to read, or --render BOOK output.png for headless rendering.')


if __name__ == '__main__': main()
