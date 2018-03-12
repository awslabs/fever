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



