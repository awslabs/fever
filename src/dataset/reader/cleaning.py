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


import re

from dataset.jobs.test2 import recursive_clean_ipa, recursive_clean_lang, recursive_clean_convert
from dataset.reader.recursive import recursive_clean


def simple_clean(text):

    #html comments
    text = re.sub(r'(<!--.*?-->)', "", text, flags=re.DOTALL)


    # refs
    text = re.sub(r'<ref( name ?= ?\"?(.*?)\"?)?((>(.*?)<\/ref>)|(\ ?\/>))', r'', text, flags=re.DOTALL)


    # files
    text = recursive_clean(text,{"[["},{"]]"},{"[[File:", "[[Image:"})

    text = recursive_clean(text, {"{|"}, {"|}"})


    text = recursive_clean_convert(text, {"{{"}, {"}}"},{"{{convert","{{Convert"})

    text = re.sub(r'(?i)\{\{IPA(\-[^\|\{\}]+)*?\|([^\|\{\}]+)(\|[^\{\}]+)*?\}\}', lambda m: " -LSB- "+ m.group(2)+" -RSB- ", text)
    text = re.sub(r'(?i)\{\{Convert\|(.*?)\|(.*?)(\|.*?)\}\}', lambda m: m.group(1)+m.group(2), text)
    text = re.sub(r'(?i)\[\[wikt\:(.*?)\|.*?\]\]', lambda m: m.group(1), text)
    text = recursive_clean_ipa(text,["\{\{IPAc-(([a-zA-Z]{2}\|)+)(audio[\s]*=[\s]*.*.ogg\|?(ˌ|)?)?","\{\{IPAc","\{\{IPA-(([a-zA-Z]{2}\|)+)","\{\{IPA"],["\|.*?\|.*?\.ogg\}\}","\}\};?"])
    text = recursive_clean_lang(text,["\{\{lang(-?\|?([a-zA-Z]{2,3}))+\|([a-zA-Z0-9\=]+\|)?"],["\|.*?\|.*?\.ogg\}\}","\}\};?"])

    return text


def post_clean(text):

    #nbsp
    text = re.sub(r'&nbsp;',' ',text)
    text = re.sub(r'<br\s?/?>','\n',text)

    text = re.sub(r'\{\{cite(.*?)\}\}', r'', text, flags=re.DOTALL + re.IGNORECASE)

    text = recursive_clean(text, {"{{"}, {"}}"})
    text = recursive_clean(text, {"{|"}, {"|}"})

    text = re.sub(r'\([^a-zA-Z0-9]*\)', ' ', text)
    text = re.sub(r'\([\s]*\)', ' ', text)
    return text.strip()


