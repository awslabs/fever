import json
import math
import os
import random
from collections import defaultdict
from subprocess import run, PIPE

from tqdm import tqdm

from annotation.schema.annotations_rds import create_session

r = random.Random(124)
#TODO check if text is the same in original/mutation
version = "fever_2017_9_22_4way_oc"
session = create_session()

result = session.execute(
    """
    select original.text as ot, mutation.text as mt, mutation.mutation_type_id, sentence.entity_id
    from claim as mutation
    inner join claim as original on mutation.original_claim_id = original.id
    inner join sentence on original.sentence_id = sentence.id
    order by sentence.entity_id
    """)

claims = defaultdict(list)


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

from corenlp.corenlpy import POSPipeline, CoreAnnotations, Annotation

def tok_pos(sentence):
    doc = Annotation(sentence)
    POSPipeline().getInstance().annotate(doc)

    tokens = []
    pos = []
    for sid in range(doc.get(CoreAnnotations.SentencesAnnotation).size()):
        sentence = doc.get(CoreAnnotations.SentencesAnnotation).get(sid)

        for i in range(sentence.get(CoreAnnotations.TokensAnnotation).size()):
            corelabel = sentence.get(CoreAnnotations.TokensAnnotation).get(i)
            tokens.append(corelabel.get(CoreAnnotations.TextAnnotation))
            pos.append(corelabel.get(CoreAnnotations.PartOfSpeechAnnotation))
    return tokens,pos

for claim in tqdm(result):
    if claim['mutation_type_id'] in ["negate","rephrase","general","specific","gen","spec","neg"]:
        ot_tokens, ot_pos = tok_pos(claim['ot'])
        mt_tokens, mt_pos = tok_pos(claim['mt'])

        claims[claim["entity_id"]].append({
            "original":" ".join(ot_tokens),
            "original_pos": " ".join(ot_pos),
            "mutation":" ".join(mt_tokens),
            "mutation_pos": " ".join(mt_pos),
            "type":claim["mutation_type_id"]})

k = list(claims.keys())
r.shuffle(k)

train = k[:math.ceil(len(k)*.8)]
dev = k[math.ceil(len(k)*.8):math.ceil(len(k)*.9)]
test = k[math.ceil(len(k)*.9):]


def get_claims(ds):
    cl = []
    for key in ds:
        cl.extend(claims[key])
    return cl


def write(ds,name):
    with open("data/"+name,"w+") as f:
        for datum in ds:
            f.write(json.dumps(datum)+"\n")

    print(name + " - " + str(len(ds)))


write(get_claims(train),"train_"+version+".jsonl")
write(get_claims(dev),"dev_"+version+".jsonl")
write(get_claims(test),"test_"+version+".jsonl")