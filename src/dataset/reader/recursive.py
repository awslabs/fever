from enum import Enum, auto
import re


# A very simple left-recursive parser for removing image, file and link tags from wikipedia.
# As these tags are non-regular, we must model the this as a context-free language


class States(Enum):
    OUTSIDE = auto()
    IN_FILE = auto()
    IN_SQ = auto()
    ACCEPT = auto()



def try_accept(text, query):
    try:
        pos = text.index(query)
        return text[pos + len(query):], query, text[:pos]
    except ValueError:
        return False, None, None

def try_accept_re(text,query):
    srch = re.search(query,text)
    if srch is None:
        return False,None,None
    pos = srch.start()

    return text[srch.end():], query, text[:pos]

def accept_re(text,*query):
    if len(query) == 1:
        return try_accept_re(text, query[0])

    results = dict()
    for q in query:
        results[q] = try_accept_re(text, q)

    minlen = float("inf")
    shortest = None
    last = None
    for result in results:
        last = results[result]
        if results[result][2] is not None and len(results[result][2]) < minlen:
            minlen = len(results[result][2])
            shortest = results[result]
    return shortest if shortest is not None else last


def accept(text, *query):
    if len(query) == 1:
        return try_accept(text, query[0])

    results = dict()
    for q in query:
        results[q] = try_accept(text, q)

    minlen = float("inf")
    shortest = None
    last = None
    for result in results:
        last = results[result]
        if results[result][2] is not None and len(results[result][2]) < minlen:
            minlen = len(results[result][2])
            shortest = results[result]
    return shortest if shortest is not None else last


def recursive_clean(text,begin,end,pre=None):
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
            accept_result, _, before = accept(text, *pre)

            if accept_result == False:
                ret += text
                state.append(States.ACCEPT)
            else:
                ret += before
                text = accept_result
                state.append(States.IN_SQ)

        elif state[-1] == States.IN_SQ:
            accept_result, accepted, before = accept(text, *begin, *end)
            if accept_result == False:
                # parse error
                return ret + text
            else:
                if accepted in begin:
                    text = accept_result
                    state.append(States.IN_SQ)
                elif accepted in end:
                    text = accept_result
                    state.pop()

    return ret

if __name__ == "__main__":
    print(recursive_clean("This text has {{some}} curly braces {{wrapped {{in }} a {{funny}} manner}} end.",{"{{"},{"}}"}))
    print(recursive_clean("This [[is the]] [[File: has some [[hidden]] atrributes]] end.",{"[["},{"]]"},{"[[File:","[[Image:"}))