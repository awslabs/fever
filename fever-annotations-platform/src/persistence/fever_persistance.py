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


import logging


class DataFile:

    def __init__(self,name):
        self.logger = logging.getLogger(DataFile.__name__)
        self.name = name
        self.line_number = 0
        self.lines = []

    def add_line(self,line):
        line = str(self.line_number) + "\t" + line
        self.lines.append(line)
        self.line_number += 1
        self.logger.debug("Add line to file {0}:\t{1}".format(self.name,line))

    @staticmethod
    def format_links(self,links):
        if not len(links):
            return ""
        return "\t".join([k+"\t"+links[k] for k in links.keys()])

    def add_sentence_links(self, sentence, links):
        self.add_line(sentence + (("\t" + self.format_links(links)) if len(links) else ""))

    def save(self,persistence,namespace):
        self.logger.debug("Save {0}".format(self.name))
        print("\n".join(self.lines))
        if persistence is not None:
            persistence.save(namespace,self.name,"\n".join(self.lines))



