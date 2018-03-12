
from botocore.exceptions import ClientError

from dataset.reader.wiki_parser import WikiParser
from persistence.s3_persistence import S3Writer

s3 = S3Writer("com.amazon.evi.fever.wiki")
parser = WikiParser(s3)


with open("data/pages.txt") as f:
    files = f.readlines()

files = [file.replace(" ","_").strip() for file in files]

for file in files:
    try:
        obj = s3.read("article/"+file)
        text = bytes.decode(obj['Body'].read())

        parser.article_callback(file,text)
    except ClientError:
        print("CE" + file)
