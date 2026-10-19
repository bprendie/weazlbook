from .layout import paginate, locate


class Session:
    def __init__(self, book, store, size=24):
        self.book, self.store, self.size = book, store, size
        self.pages = paginate(book, size)
        self.position = locate(self.pages, store.book(book.identity).get('resume'))

    @property
    def page(self): return self.pages[self.position]

    @property
    def progress(self):
        if self.position == len(self.pages)-1: return 100.0
        a=self.page.anchor
        total=sum(len(b.text) for b in self.book.blocks)
        consumed=sum(len(b.text) for b in self.book.blocks[:a['block']])+a['offset']
        return min(99.9,round(100*consumed/max(1,total),1))

    def save(self):
        record=self.store.book(self.book.identity)
        record['resume'] = self.page.anchor
        record['progress'] = self.progress
        self.store.save()

    def turn(self, delta):
        self.position = max(0, min(len(self.pages)-1, self.position+delta));
        if delta>0 and self.position==len(self.pages)-1: self.store.book(self.book.identity)['read']=True
        self.save()

    def resize(self, size):
        mark = self.page.anchor
        self.size = size; self.pages = paginate(self.book, size)
        self.position = locate(self.pages, mark)
        # Keep original semantic anchor until a deliberate navigation event.
        self.store.book(self.book.identity)['resume'] = mark; self.store.save()

    def bookmark(self, name):
        marks = self.store.book(self.book.identity)['bookmarks']
        if len(marks) >= 1000: raise ValueError('Bookmark limit reached')
        marks.append({'name': name[:120] or f'Mark {len(marks)+1}', 'anchor': self.page.anchor})
        self.store.save()

    def jump(self, mark):
        self.position = locate(self.pages, mark); self.save()

    def source(self, target):
        source, _, ident = target.partition('#')
        for i, block in enumerate(self.book.blocks):
            if block.source == source and (not ident or block.id == ident):
                self.jump({'block': i, 'offset': 0}); return
        raise ValueError('Link target is not in supported text')
