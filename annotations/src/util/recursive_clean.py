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


from dataset.reader.recursive import States, accept_re

def recursive_clean_ipa(text,begin,end,pre=None):
    state = [States.OUTSIDE]
    ret = ""
    if pre is None or len(pre) == 0:
        pre = begin


    while state[-1] is not States.ACCEPT:
        if len(state) == 0:
            ret += text
            state.append(States.ACCEPT)
            break


        elif state[-1] == States.OUTSIDE:
            accept_result, _, before = accept_re(text, *pre)

            if accept_result == False:
                ret += text
                state.append(States.ACCEPT)
            else:
                ret += before
                text = accept_result
                state.append(States.IN_SQ)

        elif state[-1] == States.IN_SQ:
            accept_result, accepted, before = accept_re(text, *begin, *end)
            if accept_result == False:
                # parse error
                return ret + text
            else:
                if accepted in begin:
                    text = accept_result
                    state.append(States.IN_SQ)
                elif accepted in end:
                    if "|" in before:
                        text = " -LSB- " + "".join(before.split("|")) + " -RSB- " + accept_result
                    else:
                        text = before+accept_result

                    state.pop()


    return ret

def recursive_clean_convert(text,begin,end,pre=None):
    state = [States.OUTSIDE]
    ret = ""
    if pre is None or len(pre) == 0:
        pre = begin


    while state[-1] is not States.ACCEPT:
        if len(state) == 0:
            ret += text
            state.append(States.ACCEPT)
            break


        elif state[-1] == States.OUTSIDE:
            accept_result, _, before = accept_re(text, *pre)

            if accept_result == False:
                ret += text
                state.append(States.ACCEPT)
            else:
                ret += before
                text = accept_result
                state.append(States.IN_SQ)

        elif state[-1] == States.IN_SQ:
            accept_result, accepted, before = accept_re(text, *begin, *end)
            if accept_result == False:
                # parse error
                return ret + text
            else:
                if accepted in begin:
                    text = accept_result
                    state.append(States.IN_SQ)
                elif accepted in end:
                    if "|" in before:
                        text =  " ".join(before.split("|")[:3]) + accept_result
                    else:
                        text = before+accept_result

                    state.pop()


    return ret

def recursive_clean_lang(text,begin,end,pre=None):
    state = [States.OUTSIDE]
    ret = ""
    if pre is None or len(pre) == 0:
        pre = begin


    while state[-1] is not States.ACCEPT:
        if len(state) == 0:
            ret += text
            state.append(States.ACCEPT)
            break


        elif state[-1] == States.OUTSIDE:
            accept_result, _, before = accept_re(text, *pre)

            if accept_result == False:
                ret += text
                state.append(States.ACCEPT)
            else:
                ret += before
                text = accept_result
                state.append(States.IN_SQ)

        elif state[-1] == States.IN_SQ:
            accept_result, accepted, before = accept_re(text, *begin, *end)
            if accept_result == False:
                # parse error
                return ret + text
            else:
                if accepted in begin:
                    text = accept_result
                    state.append(States.IN_SQ)
                elif accepted in end:
                    if "|" in before:
                        text = " -LSB- " + ", ".join(before.split("|")) + " -RSB- " + accept_result
                    else:
                        text = before+accept_result

                    state.pop()


    return ret

if __name__ == "__main__":
    string = "The '''Amazon River''', usually abbreviated to '''Amazon''' ({{IPAc-en|us|ˈ|æ|m|ə|z|ɒ|n}} or {{IPAc-en|uk|ˈ|æ|m|ə|z|ən}}; [[Spanish language|Spanish]] and {{lang-pt|'''[[wikt:Amazonas|Amazonas]]'''}}), in [[South America]] is the [[List of rivers by discharge|largest river]] by [[Discharge (hydrology)|discharge]] volume of water in the world and according to some authors, the [[List of rivers by length|longest in length]]."
    string2 = "The '''United States of America''' ({{IPAc-en|ə|ˈ|m|ɛ|ɹ|ɪ|k|ə}}; '''USA'''), commonly known as the '''United States''' ('''U.S.''') or '''America''', is a [[federal republic]]"
    string3 = "'''Japan''' (English: [dʒəˈpæn]; {{lang-ja|日本}} ''Nippon'' {{IPA-ja|ɲip̚poɴ|}} or ''Nihon'' {{IPA-ja|ɲihoɴ|}}; formally {{nihongo2|日本国}} ''{{audio|help=no|Ja-nippon_nihonkoku.ogg|Nippon-koku}}'' or ''Nihon-koku'', meaning \"State of Japan\") is a [[Sovereign state|sovereign]] [[island country|island nation]] in [[East Asia]]. Located in the [[Pacific Ocean]], it lies off the eastern coast of the Asian mainland, and stretches from the [[Sea of Okhotsk]] in the north to the [[East China Sea]] and [[Taiwan]] in the southwest."
    string4 = "'''Lionel Andrés''' "'''Leo'''" '''Messi'''{{refn|group=note|According to his club's official website, FCBarcelona.com, and his authorised biography, ''Messi'' by [[Guillem Balagué]], his surname is the single \"Messi\", in accordance with Argentine customs.<ref name=\"Profile: Lionel Andrés Messi\">{{cite web |title=Profile: Lionel Andrés Messi |publisher=FC Barcelona |url=http://www.fcbarcelona.com/football/first-team/staff/players/messi |accessdate=8 September 2015}}</ref>{{sfn|Balagué|2013|pp=32–37}} Other sources, including a 2014 document by [[FIFA]], give his surname as the double \"Messi Cuccittini\" ({{IPA-es|ljoˈnel anˈdɾes ˈmesi|-|Lionel Andrés Messi - Name.ogg}}; born 24 June 1987) is an Argentine professional [[Association football|footballer]] who plays as a [[Forward (association football)|forward]] for Spanish club [[FC Barcelona]] and the [[Argentina national football team|Argentina national team]]. Often considered the best player in the world and regarded by many as the greatest of all time, Messi is the only player in history to win five [[FIFA Ballon d'Or]] awards,"
    string5 = "'''Wikipedia''' ({{IPAc-en|audio=GT Wikipedia BE.ogg|ˌ|w|ɪ|k|ɪ|ˈ|p|iː|d|i|ə}} {{respell|WIK|i|PEE|dee|ə}} or {{IPAc-en|audio=GT Wikipedia AE.ogg|ˌ|w|ɪ|k|i|ˈ|p|iː|d|i|ə}} {{respell|WIK|ee|PEE|dee|ə}}) is a free [[online encyclopedia]]"

    for target in [string,string2,string3,string4,string5]:
        print(recursive_clean_ipa(target,["\{\{IPAc-(([a-zA-Z]{2}\|)+)(audio=.*.ogg\|())?()","\{\{IPAc","\{\{IPA-(([a-zA-Z]{2}\|)+)","\{\{IPA","\{\{lang-?\|?([a-zA-Z]{2})\|"],["\|.*\|.*\.ogg\}\}","\}\}"]))
