from html.parser import HTMLParser

class MyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.line = 1

    def handle_starttag(self, tag, attrs):
        if tag not in ['input', 'br', 'hr', 'img', 'link', 'meta', 'path', 'svg', 'defs', 'filter', 'feGaussianBlur', 'feMerge', 'feMergeNode', 'line', 'circle', 'text']:
            self.stack.append((tag, self.line))

    def handle_endtag(self, tag):
        if tag not in ['input', 'br', 'hr', 'img', 'link', 'meta', 'path', 'svg', 'defs', 'filter', 'feGaussianBlur', 'feMerge', 'feMergeNode', 'line', 'circle', 'text']:
            if not self.stack:
                self.errors.append(f"Line {self.line}: Extra closing tag </{tag}>")
                return
            last_tag, start_line = self.stack.pop()
            if last_tag != tag:
                self.errors.append(f"Line {self.line}: Expected </{last_tag}> (opened at line {start_line}), got </{tag}> instead.")
                self.stack.append((last_tag, start_line)) # Push back

    def handle_data(self, data):
        self.line += data.count('\n')

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# We only care about the JSX return block string!
jsx_start = text.find('return (') + len('return (')
jsx_end = text.rfind(')', 0, text.rfind('ReactDOM.createRoot'))

jsx_text = text[jsx_start:jsx_end]

parser = MyParser()
for line in jsx_text.split('\n'):
    try:
        parser.feed(line + '\n')
    except Exception as e:
        print(f"Error parsing: {e}")

print("ERRORS:")
for e in parser.errors:
    print(e)
print("UNCLOSED:", parser.stack)
