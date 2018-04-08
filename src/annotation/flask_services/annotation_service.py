import csv
import datetime
import logging
import os
import time
import uuid
import boto3
import flask
import json
import random

from annotation.flask_services.annotation_request import AnnotationRequest
from annotation.flask_services.user import ForwardedUserMiddleware
from collections import defaultdict
from decimal import Decimal
from flask import Flask, jsonify, request
from flask import send_from_directory
from flask_cors import CORS, cross_origin
from sqlalchemy import func

from util.wiki import get_redirects, get_wiki_clean
from annotation.schema.annotations_rds import create_session, Claim, Sentence, Annotation, LineAnnotation, \
    AnnotationVerdict
from annotation.schema.workflow import get_next_assignment
from persistence.s3_persistence import S3Writer


def get_strings_from_dynamodb_row(row, key):
    return row[key]["S"]


def prepare_item(item):
    print(item)
    return {
        key: get_strings_from_dynamodb_row(item, key)
        for key in ["entity", "sentence", "original", "mutation_type", "mutation", "uuid"]
    }




#Web app + logging
app = Flask(__name__, static_url_path='')
CORS(app)
logging.getLogger('flask_cors').level = logging.DEBUG
logger = logging.getLogger(__name__)
ddb = boto3.resource("dynamodb")
app = Flask(__name__)
app.wsgi_app = ForwardedUserMiddleware(app.wsgi_app)




with open("data/sandbox.json", "r") as f:
    sandbox = json.load(f)

with open("data/live.json", "r") as f:
    live = json.load(f)

print("Loading redirects file", end='...', flush=True)
redirects = get_redirects()
print("done")


# DEPRECATED
# Old method to get annotations - I think it's still used in the tutorial
def get_annotations_old(claim):
    file = "data/annotation/" + str(int(claim)) + ".json"

    if not os.path.isfile(file):
        json.dump([], open(file, "w+"))

    with open(file, "r+") as data_file:
        found = json.load(data_file)

    return found

# DEPRECATED
# Old mutation method - I think it's still used in the tutorial
@app.route("/mutate_old/<claim>/<pos>")
@cross_origin()
def mutate_old(claim, pos):
    article = AnnotationRequest(sandbox, claim)
    annotations = get_annotations_old(claim)

    annotations[int(pos)]["id"] = int(annotations[int(pos)]["id"])
    if "date_unix" in annotations[int(pos)]:
        annotations[int(pos)]["date_unix"] = int(annotations[int(pos)]["date_unix"])

    return jsonify({"article": article.get_dict(), "annotation": annotations[int(pos)]})


# Store the annotations from WF1 in the DDB Table
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

# On Annotation, put the annotation in the DynamoDB
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


# Get an intermediate annotation by primary-key
def get_annotations(annotation_id):
    table = ddb.Table("FeverIntermediateAnnotation")
    result = table.get_item(Key={"uuid": annotation_id})
    return result["Item"] if "Item" in result else None



# For uptime monitoring / application health check
@app.route('/ping')
def ping():
    return jsonify(ping='pong')


@app.route('/sping')
def sping():
    return jsonify(ping='pong')


# Get the next claim
@app.route("/next")
@cross_origin()
def annotate():
    annotation = AnnotationRequest(live)
    return annotation.get_json()

# Get the sentence for annotation request
@app.route("/get/<sent>")
@cross_origin()
def getsent(sent):
    annotation = AnnotationRequest(live, int(sent))
    return annotation.get_json()


# Get the sentence for the tutorial
@app.route("/get_tutorial/<sent>")
@cross_origin()
def gettut(sent):
    annotation = AnnotationRequest(sandbox, int(sent))
    return annotation.get_json()


# DEPRICATED
# Sample an annotation type  and make an annotation request for it.
# @James Thorne: we changed this so that the annotator must generate ALL mutations for a claim
@app.route("/mutate/<claim>/<pos>")
@cross_origin()
def mutate(claim, pos):
    article = AnnotationRequest(live, claim)
    annotation = get_annotations(pos)

    mutation_types = ['rephrase', 'sub', 'spec', 'gen', 'neg']
    next_mut = random.randint(0, len(mutation_types)-1)

    annotation['id'] = int(annotation['id'])
    annotation['timer'] = int(annotation['timer'])
    if "date_unix" in annotation:
        annotation["date_unix"] = int(annotation["date_unix"])

    return jsonify({"article": article.get_dict(), "annotation": annotation, "mutation": mutation_types[next_mut]})


# Post Claim
@app.route("/submit-claim", methods=["POST"])
@cross_origin()
def submit():
    annotation = request.get_json()
    annotation_id = on_annotate(annotation)
    return jsonify({"pos": annotation_id})


# Submit the number of claims that the annotator has completed and store in
# DynamoDB to allow for tracking of annotation rate
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


# Submit the mutations and store these in DynamoDB
@app.route("/submit-mutations", methods=["POST"])
@cross_origin()
def submit2():
    annotation = request.get_json()
    on_annotate2(annotation)
    return jsonify({})


# Return the number of annotations made for a given user
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


# Return an annotation report for a user
@app.route('/report/<path:path>')
def send_report(path):
    return send_from_directory(os.path.join(os.getcwd(), 'data', 'reports'), path)


# Display the annotation dashboard
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


# Display the current logged in user
@app.route("/user")
def get_user():
    return jsonify({"username": flask.request.remote_user if flask.request.remote_user is not None else "guest"})


# Get the next sentence for annotation in WF1 generation
@app.route("/nextsentence")
def get_next_sentence():
    session = create_session()

    user = flask.request.remote_user if flask.request.remote_user is not None else "guest"
    claim = get_next_assignment(session, user, testMode='test' in request.args,
                                oracleAnnotatorMode='oracle' in request.args)

    session.close()

    return jsonify(claim)

# Get a claim by ID
@app.route("/claim/<claim_id>")
def get_claim(claim_id):
    session = create_session()
    claim = session.query(Claim).join(Sentence).filter(Claim.id == int(claim_id)).first()

    doc = get_wiki_clean(claim.sentence.entity_id,redirects)["text"]

    ret = {
        "id": claim.id,
        "entity": claim.sentence.entity_id,
        "body": doc,
        "claim": {"text": claim.text},
        "sentence": claim.sentence.text


    }

    session.close()
    return jsonify(ret)


# Get an item from the dictionary
@app.route("/dictionary/<path:entity_path>")
def get_dictionary(entity_path):

    path_split = entity_path.split("/")
    entity, sentence_id = "/".join(path_split[:-1]), path_split[-1]

    lines = get_wiki_clean(entity,redirects)["text"].split("\n")

    sentence_id = int(sentence_id)

    ret = dict()
    if sentence_id < len(lines):
        entities = lines[sentence_id].split("\t")[3::2]

        for e1 in entities:
            w = get_wiki_clean(e1,redirects)
            if w is None:
                continue
            body = w["text"]

            if w["canonical_entity"].strip().lower() != entity.strip().lower():
                ret[w["canonical_entity"]] = "\n".join([t[1] if len(t) > 1 else ""
                                                        for t in [b.split("\t")
                                                                  for b in body[:len(body)-1].split("\n")]])

    return jsonify(ret)


# Get a wikipedia page
@app.route("/wiki/<name>")
def get_wiki(name):
    return jsonify(get_wiki_clean(name,redirects))


# Get a setntence by ID from Dynamo
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


# Save annotation
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

# Static routes for html, css and js
@app.route('/', defaults={'path': 'index.html'})
def send_index(path):
    return send_from_directory(os.path.join(os.getcwd(), 'www'), path)


# Static routes for html, css and js
@app.route("/css/<path:path>")
def send_css(path):
    return send_from_directory(os.path.join(os.getcwd(), 'www', 'css'), path)

# Static routes for html, css and js
@app.route("/views/<path:path>")
def send_view(path):
    return send_from_directory(os.path.join(os.getcwd(), 'www', 'views'), path)

# Static routes for html, css and js
@app.route("/js/<path:path>")
def send_js(path):
    return send_from_directory(os.path.join(os.getcwd(), 'www', 'js'), path)


port = os.environ["FEVER_PORT"]
app.run("0.0.0.0", port, threaded=True)
