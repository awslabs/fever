sentence = "Ayn Ghazal -LRB- Ain Ghazal , ʿayn ġazāl عين غزال -RRB- is a neolithic archaeological site located in metropolitan Amman , Jordan , about 2 km north-west of Amman Civil Airport ."

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

