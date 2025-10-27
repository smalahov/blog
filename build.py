#!/bin/python3

import os, re, sys
import shutil
from pygments import highlight
from pygments.formatters import HtmlFormatter


article_start = "__________"
article_end   = "__________"
author_name = "Sergey Malahov"
domain = "smalahov.com"
magic = "945767f90d0094aa46a15ee32ce0d643a1eda59e6d24c7cb6a1caecaa67b2cdaa47d50fbbfde941610809f2a9629e1ad731cb46d38acfd9d781ef2f8fd9a04e5"


def trace(msg):
    if "debug" in sys.argv:
        print(msg)


class Node:
    start_tag = None
    end_tag = None
    options = set()

    def __init__(self, file_name, line_no, /, cwd=os.getcwd()):
        self._meta = ""
        self._content = ""
        self._cwd = cwd
        self._file_name = file_name
        self._line_no = line_no

        trace(f"Instance of {self.__class__.__name__} is created at {line_no}")

    def _read_start_tag(self, text):
        self._start_tag = text

    def _read_meta(self, text):
        self._meta = text

    def _read_content(self, text):
        self._content += text

    def _read_end(self):
        self._content = re.sub(r"[\n ]+$", r"", self._content)

    def _error(self, message):
        raise Exception(f"Node {self.__class__.__name__}: {message}")

    def get_html(self):
        return self._meta + self._content

    def get_txt(self):
        return self._meta + self._content

    def get_group_prefix_html(self):
        return ""

    def get_group_postfix_html(self):
        return ""


class TextNode(Node):
    start_tag = ".+"
    end_tag = "^$"
    options = Node.options | {"auto_end"}

    def _read_start_tag(self, text):
        self._content = self._content.strip() + " " + text

    def _read_meta(self, text):
        self._content = self._content.strip() + " " + text

    def _read_content(self, text):
        self._content = self._content.strip() + " " + text

    def _get_html_content(self):
        result = re.sub(r"`([^`]*)`", r"<code>\1</code>", self._content)
        result = re.sub(r"\*\*([^*]*)\*\*", r"<b>\1</b>", result)
        result = re.sub(r"\<\<([^|]+)\|([^>]+.(\.jpeg|\.png))\>\>", r"</p><div class=imgdiv><img src='\2' alt='\1'></div><p>", result)
        result = re.sub(r"\<\<([^|]+)\|([^>]+)\>\>", r"<a href='\2'>\1</a>", result)
        return result

    def _get_txt_content(self):
        result = self._content
        result = re.sub(r"`([^`]*)`", r"'\1'", result)
        result = re.sub(r"\*\*([^*]*)\*\*", r"\1", result)
        result = re.sub(r"\<\<([^|]+)\|([^>]+)\>\>", r"\1 (\2)", result)
        result = result.replace("\n", "")

        return result

    def get_html(self):
        return f"<p>{self._get_html_content()}</p>"

    def get_txt(self):
        return self._get_txt_content()


class ListNode(TextNode):
    start_tag="^[ ]*-[ ]*"
    options = TextNode.options | {"auto_split"}

    def _read_start_tag(self, text):
        pass

    def _read_meta(self, text):
        self._content += " " + text

    def get_html(self):
        return f"<li>{self._get_html_content()}</li>"

    def get_txt(self):
        return f"- {self._get_txt_content()}"

    def get_group_prefix_html(self):
        return "<ul>"

    def get_group_postfix_html(self):
        return "</ul>"


class CodeNode(Node):
    start_tag = "^.*```([a-z]*)"
    end_tag = "^.*```"
    from pygments.lexers import TextLexer
    lexer_class = TextLexer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_name = None

    def _read_meta(self, text):
        super()._read_meta(text)
        if text:
            self._file_name = "/".join([self._cwd, text])

    def _read_end(self):
        if self._file_name and not os.path.exists(self._file_name):
            self._error(f"File {self._file_name} not found")

        if not self._file_name and not self._content:
            self._error(f"Empty node")

        if not self._content and self._file_name:
            with open(self._file_name, "r") as f:
                self._content = f.read()

        super()._read_end()


    def get_html(self):
        match = re.match(self.start_tag, self._start_tag).groups()
        header = os.path.basename(self._file_name or "") or \
                 len(match) > 0 and match[0] or \
                 "code"

        content_html = highlight(self._content, self.lexer_class(), HtmlFormatter())

        return \
            "<div class=\"expandable\">" \
                "<div class=\"expandable-header\" onclick=\"toggleExpandable(this)\">" \
                f"{header}" \
                "</div>" \
                "<div class=\"expandable-content open\" style=\"height: auto\">" \
                    f"{content_html}" \
                "</div>" \
            "</div>"

    def get_txt(self):
        return f"\n{self._content}\n"


class CppNode(CodeNode):
    start_tag = "^.*```(cpp)"
    from pygments.lexers import CppLexer
    lexer_class = CppLexer


class AsmNode(CodeNode):
    start_tag = "^.*```(asm)"
    from pygments.lexers import NasmLexer
    lexer_class = NasmLexer


class OnelineNode(Node):
    options = Node.options | {"auto_end"}

class HeaderNode(OnelineNode):
    def get_html(self):
        if self._tag:
            return f"<{self._tag}>{self._meta}</{self._tag}>"
        else:
            return self._meta

    def get_txt(self):
        return f"\n[ {self._meta} ]\n"


class H1Node(HeaderNode):
    start_tag = "^[ \t]*#"
    _tag = None


class H2Node(HeaderNode):
    start_tag = "^[ \t]*##"
    _tag = "h2"


class H3Node(HeaderNode):
    start_tag = "^[ \t]*###"
    _tag = "h3"


class DescNode(OnelineNode):
    start_tag = "^.*//DESC:"


class TodoNode(OnelineNode):
    start_tag = "^.*//TODO:"

    def get_html(self):
        return ""

    def get_txt(self):
        return ""

class DateNode(OnelineNode):
    start_tag = "^.*//DATE:"


class TipNode(TextNode):
    start_tag = "^[ ]*```tip"
    end_tag = "^[ ]*```"
    options = Node.options

    def _read_start_tag(self, text):
        pass

    def get_html(self):
        return f"<div class=\"tip\">{self._get_html_content()}</div>"


Nodes = [DescNode, DateNode, TodoNode, TipNode, CppNode, AsmNode, CodeNode, H3Node, H2Node, H1Node, ListNode, TextNode]


class Article:
    info_nodes = {
            "Title": H1Node,
            "Date": DateNode,
            "Description": DescNode,
        }

    def __init__(self, artcile_dir):
        self._info = {}
        self._nodes = []
        self._dir = os.path.splitext(artcile_dir)[0]

    def add_node(self, node):
        for info in self.info_nodes:
            if isinstance(node, self.info_nodes[info]):
                if info in self._info:
                    raise Exception(f"{info} is already specified: {self._info[info] = }, new title {node.get_html() = }")
                self._info[info] = node
                node = None

        if node:
            self._nodes.append(node)

    def verify(self):
        for info in self.info_nodes:
            if info not in self._info:
                raise Exception(f"Node {info} of class {self.info_nodes[info].__name__} is missing in {self}")

    def __iter__(self):
        return self._nodes

    def __len__(self):
        return len(self._nodes)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._nodes[index]
        else:
            return self._info[index]

    def __str__(self):
        return self._dir


def parse_article(article_dir, file_name):
    article = Article(article_dir)
    current_node = None
    article_started = False

    with open("/".join([article_dir, file_name]), "r") as f:
        line_no = 0
        while line := f.readline():
            line_no += 1

            try:
                if not article_started:
                    article_started |= line.startswith(article_start)
                    continue
                elif article_started and line.startswith(article_end):
                    break;

                if current_node and current_node.end_tag and re.match(current_node.end_tag, line):
                    current_node._read_end()
                    article.add_node(current_node)
                    current_node = None
                else:
                    if not current_node or "auto_end" in current_node.options:
                        for node_class in Nodes:
                            if node_class.start_tag and re.match(node_class.start_tag, line) and (not isinstance(current_node, node_class) or current_node and "auto_split" in current_node.options):
                                if current_node:
                                    current_node._read_end()
                                    article.add_node(current_node)

                                current_node = node_class(file_name, line_no, cwd=article_dir)

                                if current_node.start_tag:
                                    start = re.match(current_node.start_tag, line)[0]
                                    current_node._read_start_tag(start)
                                    current_node._read_meta(line[len(start):].strip())
                                    line = ""

                                break

                    if line and current_node:
                        current_node._read_content(line)

            except Exception as e:
                e.add_note(f"File {file_name} at line {line_no}")
                raise

        if current_node:
            if "auto_end" in current_node.options:
                current_node._read_end()
                article.add_node(current_node)
            else:
                raise Exception(f"Incomplete node {node_class.__name__} at {line_no}")

        article.verify()

        return article


def build_article_html(article_dir, output_dir):

    article = parse_article(article_dir, "article.txt")
    os.makedirs(f"{output_dir}/{article}", exist_ok=True)

    if len(article) < 1:
        raise Exception(f"Expected at least one node in article \"{article}\" in dir \"{article_dir}\"")

    content_html = ""
    content_txt = ""
    prev_node = None
    for i in range(len(article)):
        if not prev_node or article[i].__class__ != prev_node.__class__:
            if prev_node:
                content_html += prev_node.get_group_postfix_html()
            content_html += article[i].get_group_prefix_html()

        content_html += article[i].get_html() + "\n"
        content_txt += article[i].get_txt() + "\n"
        prev_node = article[i]

    with open("article.html", "r") as template:
        result_html = template.read()
        result_html = result_html.replace("###H1", article["Title"].get_html())
        result_html = result_html.replace("###DATE", article["Date"].get_html())
        result_html = result_html.replace("###OTS", f"article.txt.ots")
        result_html = result_html.replace("###TXT", f"article.txt")
        result_html = result_html.replace("###CONTENT", content_html)

        with open(f"{output_dir}/{article}/article.html", "w") as result:
            result.write(result_html)

    with open(f"{output_dir}/{article}/article.txt", "w") as result:
        result.write(f"Written by: {author_name}\n")
        result.write(f"Published: {article['Date'].get_txt()} @ {domain}\n")
        result.write(f"{magic}\n\n")
        result.write(content_txt)

    return article


if __name__ == "__main__":
    print("Build started...")

    output_dir = "dist"

    if len(sys.argv) > 1:
        print(f"Options: {sys.argv[1:]}")

    ots_files = []
    for dirpath, dirnames, filenames in os.walk(output_dir):
        ots_files.extend(map(lambda x: f"{dirpath}/{x}", filter(lambda x: os.path.splitext(x)[1] == ".ots", filenames)))

    if "verify" in sys.argv:
        for file in ots_files:
            res = os.system(f"ots verify {file}");
            print(f"Verify result for file {file} is {res}")

        sys.exit(0)

    if "upgrade" in sys.argv:
        for file in ots_files:
            res = os.system(f"ots upgrade {file}");
            print(f"Upgrade result for file {file} is {res}")

        sys.exit(0)

    #if len(ots_files):
    #    sys.exit(f"Some .ots files are found in {output_dir = }, delete them before building")

    articles = []
    with os.scandir("./") as dirs:
        for article_dir in filter(lambda x: x.is_dir() and x.name.endswith(".art"), dirs):
            print(f"Processing {article_dir.name = } ...")
            article = build_article_html(article_dir.name, output_dir)
            articles.append(article)
            with os.scandir(f"./{article_dir.name}") as attachments:
                for att in filter(lambda x: x.name.endswith((".png", ".jpeg")), attachments):
                    shutil.copy(att.path, f"{output_dir}/{article}/")



    # Build index.html with the list of articles
    with open("index.html", "r") as template:
        html = template.read()

        articles_html = ""
        for article in articles:
            articles_html += \
                "<div class=\"article\"> " \
                "  <div class=\"article-content\"> " \
                f"    <h3>{article['Title'].get_html()}</h3>" \
                f"    <p>{article['Description'].get_html()}</p>"\
                f"<div class=\"article-meta\">Published: {article['Date'].get_html()} <a href=\"{article}/article.html\">Read →</a></div>" \
                "  </div>"\
                "</div>"

        html = html.replace("###ARTICLES", articles_html)

        with open(f"{output_dir}/index.html", "w") as result:
            result.write(html)

    os.system("cp *.css dist/")

    if "sign" in sys.argv:
        for dirpath, dirnames, filenames in os.walk(output_dir):
            for file in filter(lambda x: os.path.splitext(x)[1] == ".txt", filenames):
                if not os.path.exists(f"{dirpath}/{file}.ots"):
                    print(f"Starting sign process for {dirpath}/{file}")
                    os.system(f"ots stamp {dirpath}/{file}");

    print("Build finished.")
