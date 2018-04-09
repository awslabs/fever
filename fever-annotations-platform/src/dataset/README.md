# FEVER Wikipedia Parser

### About

This repository contains two programs. The first reads a Wikipedia dump file and copies the article bodies to an S3 bucket and writes the redirects to a text file.

The second program listens to an SQS Queue for an article name and parses that article with mwparserfromhell and CoreNLP . This is independent and parallelisable. 

### Pre-Requisites

1) SQS Queue
2) S3 Bucket with Read and Write privileges.


### Data

We used the June 2017 English Wikipedia XML bz2 dump file from [Wikimedia Downloads](https://dumps.wikimedia.org/).

### Environment

Written for Python 3.5+. Requires Java 8 and Gradle.

```bash
python3 setup.py install
```


```bash
export AWS_DEFAULT_REGION=eu-west-1
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
```

### Read Wikipedia Dump and Write Redirects File

```bash
PYTHONPATH=src python src/dataset/jobs/wiki_reader.py --s3_bucket=$BUCKET --sqs_queue=$QUEUE --wiki_file=$DUMP.XML.BZ2 --redirects_file=redirects.txt
```

### Parse Wikipedia (can run multiple instances in parallel)
This will use Gradle to install CoreNLP and automatically build the Java classpath. The classpath will be written to build/classpath.txt. On first run, this may take some time. 

```bash
PYTHONPATH=src python src/dataset/jobs/wiki_parser.py --s3_bucket=$BUCKET --sqs_queue=$QUEUE
```

### Generate WF1 Candidate Sentences for Annotation Interface

After Wikipedia has been parsed, these articles can be used to generate the candidate sentences for WF1.

You must provide a list of pages. We used this: [https://en.wikipedia.org/wiki/User:West.andrew.g/Popular_pages](https://en.wikipedia.org/wiki/User:West.andrew.g/Popular_pages)

We will also add pages which are directly linked to these. This is output into the file specified in the out_pages option
 
```bash
PYTHONPATH=src python src/annotation/jobs/one_off_jobs/generate_wf1_data.py --s3_bucket=$BUCKET --pages=pages.txt --out_file=live.json --out_pages=extra_pages.txt
```