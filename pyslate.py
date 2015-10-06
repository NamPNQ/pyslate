import re
import os
import yaml
import codecs
import argparse
import jinja2
import misaka as m
import unidecode
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from flask import escape


RE_NON_WORD = re.compile(r'\W+')
def slugify(s):
    s = unidecode.unidecode(s).lower()
    return RE_NON_WORD.sub('-', s)


# Create a custom renderer
class PySlateRenderer(m.HtmlRenderer, m.SmartyPants):
    def header(self, header, n):
        header = header.strip()
        slug = slugify(header)
        return "\n<h{n} id=\"{slug}\">{header}</h{n}>\n".format(**locals())

    def block_code(self, text, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                escape(text.strip())
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter(cssclass="highlight %s" % lang)
        return highlight(text, lexer, formatter)


# And use the renderer
renderer = PySlateRenderer()
markdown = m.Markdown(renderer,
                      extensions=m.EXT_FENCED_CODE |
                      m.EXT_NO_INTRA_EMPHASIS | m.EXT_TABLES)


def render():
    if not os.path.exists('source/index.md'):
        return 'No file index.md found!'
    md = codecs.open('source/index.md', encoding='utf8').read()
    md_datas = md.split('\n---\n')
    if md_datas[0].startswith('---'):
        md_datas[0] = md_datas[0][4:]
    metadata = yaml.load(md_datas[0])
    content = markdown.render(md_datas[1])
    if metadata.get('includes', []):
        content += '\n'.join([
            markdown.render(
                codecs.open(
                    'source/includes/_%s.md' % include, encoding='utf8'
                    ).read()
                )
            for include in metadata['includes']
        ])
    template = jinja2.Template(open('layouts/layout.html').read())
    return template.render(
        {
            'metadata': metadata,
            'content': content
        })


def run_server(host='localhost', port=9000):
    from flask import Flask
    app = Flask(__name__, static_folder='build/static')

    @app.route('/')
    def index():
        return render()

    app.run(host, port, debug=True)


def build():
    with codecs.open('build/index.html', 'w', encoding='utf8') as outfile:
        outfile.write(render())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PySlate', add_help=False)
    parser.add_argument('action', default='run')
    parser.add_argument(
        "-p", "--port", dest="port",
        help="port of server (default:%(default)s)",
        type=int, default=9000)
    parser.add_argument(
        "-h", "--host", dest="host",
        help="domain or IP of server (default:%(default)s)",
        type=str, default='0.0.0.0')
    cmd_args = parser.parse_args()
    if cmd_args.action == 'build':
        build()
    else:
        run_server(cmd_args.host, cmd_args.port)
