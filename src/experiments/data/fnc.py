import logging
import os
import json

from persistence.s3_persistence import S3Writer

logger = logging.getLogger("fnc")


def read_fever(name, data_dir="./data"):
    fpath = os.path.join(data_dir, name)
    logger.info("Reading {0}".format(fpath))

    data = []
    with open(fpath, "r") as f:
        for line in f.readlines():
            data.append(json.loads(line))

    logger.info("Done reading")
    return data


def get_claims(data):
    claims = []
    documents = set()
    doc_ids = dict()
    for record in data:
        documents.add(record["entity"]["s"])

    i=0


    bodies = dict()
    for doc in documents:
        doc_ids[doc] = i

        s3 = S3Writer("com.amazon.evi.fever.wiki")
        bodies[i] = "\n".join([line.split("\t")[1] if len(line.split())>1 else "" for line in bytes.decode(s3.read("intro_sentences/" + s3.clean(doc))['Body'].read()).split("\n")])
        i+=1

    done_ids = set()
    for record in data:
        original = record["original"]["s"]
        mutation_type = record["mutation_type"]["s"]
        mutation = record["mutation"]["s"]
        sentence = record["sentence"]["s"]
        entity = record["entity"]["s"]

        cor_id = record["correlation"]["s"]

        if cor_id not in done_ids:
            done_ids.add(cor_id)
            claims.append({"Headline": original, "Body ID": doc_ids[entity], "Stance":"agree"})

        if mutation_type == "rephrase" or mutation_type == "general" or mutation_type=="gen":
            claims.append({"Headline": mutation, "Body ID": doc_ids[entity], "Stance":"agree"})



        if mutation_type == "neg" or mutation_type == "negate":
            claims.append({"Headline": mutation, "Body ID": doc_ids[entity], "Stance":"disagree"})

        if mutation_type == "spec" or mutation_type == "specific":
            claims.append({"Headline": mutation, "Body ID": doc_ids[entity], "Stance": "discuss"})

        if mutation_type == "sim" or mutation_type == "dis" or mutation_type == "sub" or mutation_type == "substitute_similar" or mutation_type == "substitute_dissimilar":
            claims.append({"Headline": mutation, "Body ID": doc_ids[entity], "Stance": "unrelated"})


    return claims,bodies


fever_claims,bodies = get_claims(read_fever("fever.json"))



import csv

data = fever_claims

with open('data/fever_stances.csv', 'w') as csvfile:
    fieldnames = ['Headline','Body ID','Stance']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for claim in data:
        writer.writerow(claim)

with open('data/fever_bodies.csv', 'w') as csvfile:
    fieldnames = ['Body ID','articleBody']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for id,body in bodies.items():
        writer.writerow({"Body ID":id,"articleBody":body})
