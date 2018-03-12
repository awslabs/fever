import csv
import datetime
import logging
import os
import time
import uuid
import botocore
import boto3

from collections import defaultdict
from decimal import Decimal
from flask import Flask, jsonify, request
from flask import send_from_directory
from flask_cors import CORS, cross_origin
from sqlalchemy import func

from annotation.schema.annotations_rds import create_session, Claim, Sentence, Annotation, LineAnnotation, \
    AnnotationVerdict
from annotation.schema.workflow import get_next_assignment
from dataset.jobs.test3 import untokenize
from persistence.s3_persistence import S3Writer

app = Flask(__name__, static_url_path='')
CORS(app)

logging.getLogger('flask_cors').level = logging.DEBUG

logger = logging.getLogger(__name__)

import json
from random import Random

r = Random()
r2 = Random()

ddb = boto3.resource("dynamodb")

port = os.environ["FEVER_PORT"]

from flask import Flask
import flask


class ForwardedUserMiddleware(object):
    def __init__(self, application):
        self.app = application

    def __call__(self, environ, start_response):
        user = environ.pop('HTTP_X_FORWARDED_USER', None)
        if user is not None:
            environ['REMOTE_USER'] = user.split("@")[0]

        return self.app(environ, start_response)


app = Flask(__name__)
app.wsgi_app = ForwardedUserMiddleware(app.wsgi_app)


def get_redirects():
    redirs = os.path.join("data", "redirect.txt")
    rd = dict()
    for line in open(redirs, encoding='utf-8'):
        bits = line.strip().split("\t")
        if len(bits) == 2:
            frm, to = bits
            rd[frm] = to
    return rd


def recursive_redirect_lookup(redirects_list, word):
    if word in redirects_list:
        try:
            return recursive_redirect_lookup(redirects_list, redirects_list[word])
        except RecursionError:
            return word
    else:
        return word


def get_wiki_entry(name):
    name = name.strip()
    s3 = S3Writer("com.amazon.evi.fever.wiki")
    try:
        key = s3.clean("intro/"+name)

        body = s3.read_string(key)
        return {"text": body, "canonical_entity": name}
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "NoSuchKey":
            if name[0].islower():
                return get_wiki_entry(name[0].upper()+name[1:])
            else:
                try:
                    return get_wiki_entry(recursive_redirect_lookup(redirects, redirects[name]))
                except RecursionError:
                    logger.error("Couldn't resolve {0} from dictionary: recursive redirect loop".format(name))
                    return None

                except KeyError:
                    logger.error("{0} has no redirect lookup".format(name))
                    return None
        else:
            logger.error("Could not resolve {0} from dictionary because it doesnt exist".format(name))
            return None


with open("data/sandbox.json", "r") as f:
    sandbox = json.load(f)

with open("data/live.json", "r") as f:
    live = json.load(f)

print("Loading redirects file", end='...', flush=True)
redirects = get_redirects()
print("done")


def on_annotate(annotation):
    u = uuid.uuid1()

    table = ddb.Table("FeverIntermediateAnnotation")

    item = dict()
    item.update(annotation)
    item.update({'uuid': str(u)})
    item["date"] = str(datetime.datetime.utcnow())
    item["date_unix"] = int(datetime.datetime.utcnow().timestamp())
    table.put_item(Item=item)

    return u


def get_annotations_old(claim):
    file = "data/annotation/" + str(int(claim)) + ".json"

    if not os.path.isfile(file):
        json.dump([], open(file, "w+"))

    with open(file, "r+") as data_file:
        found = json.load(data_file)

    return found


@app.route("/mutate_old/<claim>/<pos>")
@cross_origin()
def mutate_old(claim, pos):
    article = AnnotationRequest(sandbox, claim)
    annotations = get_annotations_old(claim)

    annotations[int(pos)]["id"] = int(annotations[int(pos)]["id"])
    if "date_unix" in annotations[int(pos)]:
        annotations[int(pos)]["date_unix"] = int(annotations[int(pos)]["date_unix"])

    return jsonify({"article": article.get_dict(), "annotation": annotations[int(pos)]})


def on_annotate2(annotation):
    mutation_types = ['rephrase', 'substitute_similar', 'substitute_dissimilar', 'specific', 'general', 'negate']

    orig = get_annotations(annotation["id"])
    if orig is None:
        return

    sentence_id = int(orig["id"])
    original_task = live[sentence_id]
    time_spent = int(orig['timer']) + annotation['timer']
    # Since we are storing the time spent on each mutation, add the total time and divide by the # of mutations
    # We also need to count the original claims
    mutations_done = len(orig['true_claims'].split("\n"))
    for anno_type in mutation_types:
        for key in annotation["claims"][anno_type].keys():
            for line in annotation["claims"][anno_type][key].split("\n"):
                if len(line.strip()) > 0:
                    mutations_done += 1
    time_spent = round(time_spent / mutations_done)

    table = ddb.Table("FeverAnnotations")

    for anno_type in mutation_types:
        for key in annotation["claims"][anno_type].keys():
            for line in annotation["claims"][anno_type][key].split("\n"):
                u = uuid.uuid1()

                item = dict()
                item['original'] = key.strip()
                if len(line.strip()) > 0:
                    item['mutation'] = line.strip()
                else:
                    continue

                item['mutation_type'] = anno_type
                item['correlation'] = annotation['id']
                item['entity'] = original_task["entity"]
                item['sentence'] = original_task["sentence"]
                item['sentence_id'] = sentence_id
                item["version"] = 5
                item["testing"] = annotation["testing"]
                item["user"] = flask.request.remote_user if flask.request.remote_user is not None else "guest"
                item["date"] = str(datetime.datetime.utcnow())
                item["date_unix"] = int(datetime.datetime.utcnow().timestamp())
                item['timer'] = time_spent
                item.update({'uuid': str(u)})

                table.put_item(Item=item)


def get_annotations(annotation_id):
    table = ddb.Table("FeverIntermediateAnnotation")
    result = table.get_item(Key={"uuid": annotation_id})

    return result["Item"] if "Item" in result else None


class AnnotationRequest:
    def __init__(self, dataset, claim=None):
        super().__init__()

        if claim is None:
            self.example = dataset[r.randint(0, len(dataset))]
        else:
            self.example = dataset[int(claim)]

        while len(self.example["sentence"].strip()) == 0:
            self.example = dataset[r.randint(0, len(dataset)-1)]

    def get_dict(self):
        annotation_dict = dict()
        annotation_dict.update(self.example)
        return annotation_dict

    def get_json(self):
        return jsonify(self.get_dict())


@app.route('/ping')
def ping():
    return jsonify(ping='pong')


@app.route('/sping')
def sping():
    return jsonify(ping='pong')


@app.route("/next")
@cross_origin()
def annotate():
    annotation = AnnotationRequest(live)
    return annotation.get_json()


@app.route("/get/<sent>")
@cross_origin()
def getsent(sent):
    annotation = AnnotationRequest(live, int(sent))
    return annotation.get_json()


@app.route("/get_tutorial/<sent>")
@cross_origin()
def gettut(sent):
    annotation = AnnotationRequest(sandbox, int(sent))
    return annotation.get_json()


@app.route("/mutate/<claim>/<pos>")
@cross_origin()
def mutate(claim, pos):
    article = AnnotationRequest(live, claim)
    annotation = get_annotations(pos)

    mutation_types = ['rephrase', 'sub', 'spec', 'gen', 'neg']
    next_mut = r2.randint(0, len(mutation_types)-1)

    annotation['id'] = int(annotation['id'])
    annotation['timer'] = int(annotation['timer'])
    if "date_unix" in annotation:
        annotation["date_unix"] = int(annotation["date_unix"])

    return jsonify({"article": article.get_dict(), "annotation": annotation, "mutation": mutation_types[next_mut]})


@app.route("/submit-claim", methods=["POST"])
@cross_origin()
def submit():
    annotation = request.get_json()
    annotation_id = on_annotate(annotation)
    return jsonify({"pos": annotation_id})


@app.route("/submit-stats", methods=["POST"])
@cross_origin()
def submit_stats():
    stats = request.get_json()
    u = uuid.uuid1()
    table = ddb.Table("AnnotationStatistics")

    item = dict()
    item.update(stats)
    item.update({'source': str(u), 'time': Decimal(time.time())})

    item["user"] = flask.request.remote_user if flask.request.remote_user is not None else "guest"
    item["testing"] = stats["testing"]
    item["date"] = str(datetime.datetime.utcnow())
    item["date_unix"] = int(datetime.datetime.utcnow().timestamp())
    table.put_item(Item=item)

    return jsonify({})


@app.route("/submit-mutations", methods=["POST"])
@cross_origin()
def submit2():
    annotation = request.get_json()
    on_annotate2(annotation)
    return jsonify({})


@app.route("/count")
def item_count():
    user = flask.request.remote_user

    if user is None:
        return jsonify({"count": 0, "count_wf2": 0})

    dates = defaultdict(int)
    with open("data/reports/live_daily.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            dates[row["Date"]] = row[user] if user in row else 0
    cnt = dates[str(datetime.datetime.now().date())]

    dates = defaultdict(int)
    cnt_wf2 = 0
    if os.path.exists("data/reports/live_daily_wf2.csv"):
        with open("data/reports/live_daily_wf2.csv") as file:
            reader = csv.DictReader(file)
            for row in reader:
                dates[row["Date"]] = row[user] if user in row else 0
        cnt_wf2 = dates[str(datetime.datetime.now().date())]

    return jsonify({"count": cnt, "count_wf2": cnt_wf2})


@app.route('/report/<path:path>')
def send_report(path):
    return send_from_directory(os.path.join(os.getcwd(), 'data', 'reports'), path)


@app.route("/dashboard")
def dashboard():
    with open("data/state.json", "r") as file:
        model = json.load(file)

    with open("data/state_wf2.json", "r") as file:
        model2 = json.load(file)

    oracle = {}
    if os.path.exists("data/oracle.json"):
        with open("data/oracle.json", "r") as file:
            oracle = json.load(file)

    return jsonify({"wf1": model, "wf2": model2, "oracle": oracle})


@app.route("/user")
def get_user():
    return jsonify({"username": flask.request.remote_user if flask.request.remote_user is not None else "guest"})


@app.route('/', defaults={'path': 'index.html'})
def send_index(path):
    return send_from_directory(os.path.join(os.getcwd(), 'www'), path)


@app.route("/css/<path:path>")
def send_css(path):
    return send_from_directory(os.path.join(os.getcwd(), 'www', 'css'), path)


@app.route("/views/<path:path>")
def send_view(path):
    return send_from_directory(os.path.join(os.getcwd(), 'www', 'views'), path)


@app.route("/js/<path:path>")
def send_js(path):
    return send_from_directory(os.path.join(os.getcwd(), 'www', 'js'), path)


def get_strings_from_dynamodb_row(row, key):
    return row[key]["S"]


def prepare_item(item):
    print(item)
    return {
        key: get_strings_from_dynamodb_row(item, key)
        for key in ["entity", "sentence", "original", "mutation_type", "mutation", "uuid"]
    }


@app.route("/nextsentence")
def get_next_sentence():
    session = create_session()

    user = flask.request.remote_user if flask.request.remote_user is not None else "guest"
    claim = get_next_assignment(session, user, testMode='test' in request.args,
                                oracleAnnotatorMode='oracle' in request.args)

    session.close()

    return jsonify(claim)


@app.route("/claim/<claim_id>")
def get_claim(claim_id):
    session = create_session()
    claim = session.query(Claim).join(Sentence).filter(Claim.id == int(claim_id)).first()

    doc = get_wiki_clean(claim.sentence.entity_id)["text"]

    ret = {
        "id": claim.id,
        "entity": claim.sentence.entity_id,
        "body": doc,
        "claim": {"text": claim.text},
        "sentence": claim.sentence.text


    }

    session.close()
    return jsonify(ret)


@app.route("/dictionary/<path:entity_path>")
def get_dictionary(entity_path):

    path_split = entity_path.split("/")
    entity, sentence_id = "/".join(path_split[:-1]), path_split[-1]

    lines = get_wiki_clean(entity)["text"].split("\n")

    sentence_id = int(sentence_id)

    ret = dict()
    if sentence_id < len(lines):
        entities = lines[sentence_id].split("\t")[3::2]

        for e1 in entities:
            w = get_wiki_clean(e1)
            if w is None:
                continue
            body = w["text"]

            if w["canonical_entity"].strip().lower() != entity.strip().lower():
                ret[w["canonical_entity"]] = "\n".join([t[1] if len(t) > 1 else ""
                                                        for t in [b.split("\t")
                                                                  for b in body[:len(body)-1].split("\n")]])

    return jsonify(ret)


@app.route("/wiki/<name>")
def get_wiki(name):
    return jsonify(get_wiki_clean(name))


def get_wiki_clean(name):
    """

    First tries to get the entity from S3 without modifying the entity name
    If the key is not found, it will apply camel-case capitalisation and look up entity in redirects.txt

    :param name: The name of the entity
    :return: a dictionary containing the body of the intro for the entity
             and the canonical entity name after resolving it
    """
    entry = get_wiki_entry(name)
    if entry is None:
        return None

    text = entry["text"]
    # Replace problematic dictionary entries (e.g. claim #195054)
    # for some reason, there are line breaks between the linked text and the URL of the entry
    text = text.replace('\n\t', '\t')

    out = []
    for line in text.split("\n"):
        if len(line.split("\t")) > 1:
            linebits = line.split("\t")
            linebits[1] = untokenize(linebits[1])

            out.append("\t".join(linebits))
        else:
            out.append(line)

    entry["text"] = "\n".join(out)
    return entry


@app.route("/sentence/<sent_id>")
def get_sentence(sent_id):

    client = boto3.client("dynamodb")

    s3 = S3Writer("com.amazon.evi.fever.wiki")

    matching_items = client.query(
        TableName="FeverAnnotations",
        IndexName="sentence_id-index",
        Select="ALL_ATTRIBUTES",
        KeyConditionExpression="sentence_id = :v1",
        ExpressionAttributeValues={
            ":v1": {"N": str(sent_id)}
        }
    )

    claims_for_annotation = []
    if "Items" in matching_items:
        claims_for_annotation.extend([prepare_item(item) for item in matching_items["Items"]])

    originals = {claim["original"] for claim in claims_for_annotation}
    claims = []

    for claim in claims_for_annotation:
        claims.append({"text": claim["mutation"]})

    for claim in originals:
        claims.append({"text": claim})

    entity = claims_for_annotation[0]["entity"]

    doc = s3.read_string("intro/"+s3.clean(entity))
    return jsonify(
        {
            "entity": claims_for_annotation[0]["entity"],
            "body": doc,
            "claims": claims,
            "sentence": claims_for_annotation[0]["sentence"]
        }

    )


@app.route("/labels/<label_id>", methods=["POST"])
def post_labels(label_id):
    labels = request.get_json()

    session = create_session()
    claim = session.query(Claim).join(Sentence).filter(Claim.id == int(label_id)).first()

    user = flask.request.remote_user if flask.request.remote_user is not None else "guest"

    anno = Annotation(
        user=user,
        claim_id=claim.id,
        created=func.now(),
        sentencesVisited=int(labels["countAll"]),
        customPagesAdded=int(labels["customCount"]),
        timeTakenToAnnotate=int(labels["timer"]),
        isTestMode=bool(labels['testingMode']),
        isOracleMaster=bool(labels['oracleMode']),
        page=claim.sentence.entity_id,
        version=4,
        verifiable=int(labels["verifiable"]))
    session.add(anno)
    session.commit()

    # Treat flagged-but-submitted claims as normal submissions
    if int(labels['verifiable']) == 1 or int(labels['verifiable']) == -1:
        for verdict in labels["supporting"]:
            vdct = AnnotationVerdict(
                annotation_id=anno.id,
                verdict=1
            )
            session.add(vdct)
            session.commit()

            session.add(LineAnnotation(
                page=claim.sentence.entity_id,
                line_number=verdict,
                verdict_id=vdct.id
            ))

            for doc in labels['sentences'][str(verdict)].keys():
                for line in labels['sentences'][str(verdict)][doc].keys():
                    if bool(labels['sentences'][str(verdict)][doc][line]):
                        session.add(LineAnnotation(page=doc, line_number=int(line), verdict_id=vdct.id))

        for verdict in labels["refuting"]:
            vdct = AnnotationVerdict(
                annotation_id=anno.id,
                verdict=2
            )
            session.add(vdct)
            session.commit()

            session.add(LineAnnotation(
                page=claim.sentence.entity_id,
                line_number=verdict,
                verdict_id=vdct.id
            ))

            for doc in labels['sentences'][str(verdict)].keys():
                for line in labels['sentences'][str(verdict)][doc].keys():
                    if bool(labels['sentences'][str(verdict)][doc][line]):
                        session.add(LineAnnotation(page=doc, line_number=int(line), verdict_id=vdct.id))

    session.commit()

    session.close()

    return jsonify([])


app.run("0.0.0.0", port, threaded=True)
