import boto3
import json
import os

from multiprocessing import Queue, Process

s3 = boto3.resource("s3")
bucket = s3.Bucket(os.getenv("BUCKET"))
q = Queue(maxsize=4000)

id = 0
keys = []


shutdown = False

# On notification, read the wikipedia article and write it to file
def process_article():
    while not (shutdown and q.empty()):
        try:
            a,b = q.get(15)
            contents = bucket.Object(a).get()["Body"].read().decode("utf-8")
            lines = contents.split("\n")
            lines = map(lambda line: line.split("\t")[1] if len(line.split("\t"))>1 else "",lines)
            with open(b,"w+") as f:
                f.write("\n".join(lines))
        except:
            print("QException")
    print("Queue finished")

# Start clients
for _ in range(500):
    t = Process(target=process_article)
    t.start()

# For each item in the bucket, add it to the queue to process pages
for obj in bucket.objects.filter(Prefix="intro_sentences/").page_size(100):
    keys.append(obj.key)

    store_path = "data/intros/"+str(id).zfill(10)+".txt"
    q.put((obj.key,store_path))

    if id % 1e4 == 0:
        print("Done",id)
    id += 1


print("Finished indexing. Writing keys")
json.dump(keys, open("data/intro.keys.json", "w+"))
print("Shutting down")


shutdown = True
print("Waiting for queues to stop")