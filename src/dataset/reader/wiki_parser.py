import os
import mwparserfromhell
import logging

from dataset.reader.cleaning import simple_clean, post_clean
from dataset.util.text_util import is_blank, exact_match
from persistence.fever_persistance import DataFile
from subprocess import run, PIPE
from corenlp.corenlpy import *


#Load Java classpath for stanford corenlp using gradle. this will also install it if missing
if 'CLASSPATH' not in os.environ:
    if not (os.path.exists('build') and os.path.exists('build/classpath.txt')):
        print("Generating classpath")
        r=run(["./gradlew", "writeClasspath"],stdout=PIPE, stderr=PIPE, universal_newlines=True)
        print(r.stdout)
        print(r.stderr)

    print("Loading classpath")
    os.environ['CLASSPATH'] = open('build/classpath.txt','r').read()
    print("Done")


class WikiParser:
    def __init__(self, persistence):
        self.logger = logging.getLogger(WikiParser.__name__)
        self.persistence = persistence


    def article_callback(self, title, source):
        self.logger.debug("Process article {0}".format(title))
        parsed = mwparserfromhell.parse(simple_clean(source))

        before_headings = []
        after_headings = []

        before_links = []
        after_links = []

        is_lead = True

        for line in parsed.get_sections(include_lead=True):
            if len(line.filter_headings()) > 0:
                if is_lead == True:
                    idx = str(line).index((str(line.filter_headings()[0])))
                    before = mwparserfromhell.parse(line[0:idx])
                    after = mwparserfromhell.parse(line[idx:])

                    before_headings.append(before)
                    after_headings.append(after)

                    before_links.append(before.filter_wikilinks())
                    after_links.append(after.filter_wikilinks())

                    is_lead = False
                    continue


                is_lead = False

            links = line.filter_wikilinks()
            if is_lead:
                before_headings.append(line)
                before_links.append(links)

            else:
                after_headings.append(line)
                after_links.append(links)

        self.first_sentence(title,zip(before_headings,before_links))
        self.get_sentences(title,zip(before_headings,before_links),"intro")
        self.get_sentences(title,zip(after_headings,after_links),"body")


    def first_sentence(self,title,sections):
        first_sentence = None
        for section in sections:
            section_text = post_clean(str(section[0].strip_code()))
            if not is_blank(section_text):

                try:
                    doc = Annotation(section_text)
                    SentenceSplittingPipeline().getInstance().annotate(doc)
                    if doc.get(CoreAnnotations.SentencesAnnotation).size() > 0:
                        sentence = doc.get(CoreAnnotations.SentencesAnnotation).get(0)

                        tokens = []
                        for i in range(sentence.get(CoreAnnotations.TokensAnnotation).size()):
                            corelabel = sentence.get(CoreAnnotations.TokensAnnotation).get(i)
                            tokens.append(corelabel.get(CoreAnnotations.TextAnnotation))

                        first_sentence = " ".join(tokens)
                        print(first_sentence)

                except TypeError as e:
                    self.logger.warning(e)

                break

        if first_sentence is not None:
            file_logger = DataFile(title)
            file_logger.add_line(first_sentence)
            file_logger.save(self.persistence,"dictionary")


    def get_sentences(self, title, sections, namespace):
        file_logger = DataFile(title)

        for section in sections:
            section_text = post_clean(str(section[0].strip_code()))

            if not is_blank(section_text):
                for block in section_text.split("\n"):
                    try:
                        doc = Annotation(block)
                        SentenceSplittingPipeline().getInstance().annotate(doc)
                        for sid in range(doc.get(CoreAnnotations.SentencesAnnotation).size()):
                            sentence = doc.get(CoreAnnotations.SentencesAnnotation).get(sid)

                            tokens = []
                            for i in range(sentence.get(CoreAnnotations.TokensAnnotation).size()):
                                corelabel = sentence.get(CoreAnnotations.TokensAnnotation).get(i)
                                tokens.append(corelabel.get(CoreAnnotations.TextAnnotation))

                            sentence = " ".join(tokens)
                            file_logger.add_sentence_links(" ".join(str(sentence).split()), self.resolve_links(sentence,section[1]))

                        file_logger.add_line("")

                    except TypeError as e:
                        self.logger.warning(e)


        file_logger.save(self.persistence,namespace)


    def resolve_links(self,sentence,links):
        ret = dict()
        if sentence is not None and links is not None:

            for link in links:
                link = link.replace("[[", "")
                link = link.replace("]]", "")

                link_parts = link.split("|")

                surface_form = link_parts[0] if len(link_parts) == 1 else link_parts[1]
                if exact_match(surface_form, str(sentence)):
                    ret[surface_form] = link_parts[0]


        remove = []
        for link in ret.keys():
            for link2 in ret.keys():
                if len(link) > len(link2):
                    try:
                        link.index(link2)
                        remove.append(link2)
                    except:
                        pass

        for link in remove:
            del ret[link]

        return ret