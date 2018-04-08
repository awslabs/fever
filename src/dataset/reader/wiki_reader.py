# Copyright 2018 Amazon Research Cambridge
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import xml.sax
import logging

class WikiReader(xml.sax.ContentHandler):
    def __init__(self,filter_namespace,article_callback,redirect_callback):
        super().__init__()
        self.logger = logging.getLogger(WikiReader.__name__)
        self.logger.debug("Init WikiPageSplitter")

        self.stack = []
        self.text = None
        self.title = None
        self.redirTarget = None
        self.ns = 0

        self.num_articles = 0
        self.num_redirects = 0
        self.tick = 0

        self.filter_namespace = filter_namespace
        self.article_callback = article_callback
        self.redirect_callback = redirect_callback

    def startElement(self, name, attributes):
        if name == "ns":
            assert self.stack == ["page"]
            self.ns = 0
        elif name == "page":
            assert self.stack == []
            self.text = None
            self.title = None
            self.redirTarget = None
        elif name == "title":
            assert self.stack == ["page"]
            assert self.title is None
            self.title = ""
        elif name == "text":
            assert self.stack == ["page"]
            assert self.text is None

            if self.redirTarget is not None:
                return
            self.text = ""
        elif name == "redirect":
            assert self.stack == ["page"]
            assert self.redirTarget is None
            assert self.title is not None
            self.redirTarget = attributes['title']
        else:
            assert len(self.stack) == 0 or self.stack[-1] == "page"
            return

        self.stack.append(name)

    def endElement(self, name):
        if len(self.stack) > 0 and name == self.stack[-1]:
            del self.stack[-1]

        if self.filter_namespace(self.ns):
            if self.redirTarget is None and name == "text":
                self.num_articles += 1
                self.article_callback(self.title, self.text)
                self.tick += 1
                self.report_status()
            elif name == "redirect":
                self.num_redirects += 1
                self.redirect_callback(self.title,self.redirTarget)
                self.tick += 1
                self.report_status()

    def report_status(self):
        if self.tick % 250 == 0:
            self.logger.info('Redirects {0}, Articles {1} imported'.format(self.num_redirects,self.num_articles))

    def characters(self, content):
        assert content is not None and len(content) > 0
        if len(self.stack) == 0:
            return

        if "redirect" not in self.stack:
            if self.stack[-1] == "text":
                assert self.title is not None
                self.text += content
                self.logger.debug("Set text to string[{0}]".format(len(self.text)))


        if self.stack[-1] == "title":
            self.title += content
            self.logger.debug("Set title to {0}".format(self.title))

        if self.stack[-1] == "ns":
            self.ns += int(content)
            self.logger.debug("Set ns to {0}".format(self.ns))


