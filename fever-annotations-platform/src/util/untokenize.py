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


replacements = {
    "-LRB-":"(",
    "-LSB-":"[",
    "-LCB-": "{",
    "-RCB-": "}",
    "-RRB-":")",
    "-RSB-":"]",
}


def lookup(token):
    if token in replacements:
        return replacements[token]
    return token

def nospacebefore(token):
    return token not in {",",".","!","?","-RRB-","-RSB-","-RCB-","'","''","'s","'t",";",":"}


def nospaceafter(token):
    return token not in {None,"-LRB-","-LSB-","-LCB-","`","``","$","£","€"}


def untokenize(sentence):
    out = ""
    prevtok = None
    for idx,tok in enumerate(sentence.split()):

        if nospacebefore(tok) and nospaceafter(prevtok):
            out += " "

        out += lookup(tok)

        prevtok = tok


    return out

