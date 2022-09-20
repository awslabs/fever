# FEVER Annotation Web Service

### Running

* **View Only Mode**: Requires: MySQL
* **Full Interface**: Requires: MySQL + Amazon DynamoDB

MySQL can be installed locally or provisioned through a service such as [Amazon Relational Database Service](https://aws.amazon.com/rds/).

### Pre-Requisites

1) Install MySQL
2) *Optional* Create DynamoDB tables: FeverAnnotations (PK uuid (S)), FeverIntermediateAnnotation (PK uuid (S)), AnnotationStatistics (PK source (S)) and create appropriate user 

### Data

The annotation targets should be saved to the data directory and saved in live.json, sandbox.json and redirects.txt file.

You may use your own, or use the data we used from the June 2017 Wikipedia dump. Please reach out to our [Slack channel](https://join.slack.com/t/feverworkshop/shared_invite/zt-4v1hjl8w-Uf4yg~diftuGvj2fvw7PDA) if you want to request access to those files.

### Environment

Written for Python 3.5+ 

```bash
python3 setup.py install
```


```bash
export AWS_DEFAULT_REGION=eu-west-1
export MYSQL_USER=xxx
export MYSQL_PASS=xxx

export AWS_ACCESS_KEY_ID=xxx #optional
export AWS_SECRET_ACCESS_KEY=xxx #optional

export SQLALCHEMY_DATABASE_URI=mysql+pymysql://$MYSQL_USER:$MYSQL_PASS@localhost/annotations
```

#### MySQL Setup

In the MySQL Terminal
```mysql
create database annotations;
--- Replace XXX with your username
create user XXX
GRANT SELECT, INSERT, UPDATE ON annotations.* TO 'XXX'@'localhost'; 
```

### Start annotation service

```bash
FEVER_PORT=8080 PYTHONPATH=src python src/annotation/flask_services/annotation_service.py
```

### Jobs

ETL WF1 Claims into WF2

```bash
PYTHONPATH=src python src/annotation/jobs/periodic_jobs/annotation_wf2_construct.py
```

Sample claims for oracle evaluation

```bash
PYTHONPATH=src python src/annotation/jobs/one_off_jobs/sample_annotations_for_oracle.py
```

Oracle Statistics

```bash
PYTHONPATH=src python src/annotation/jobs/periodic_jobs/annotation_reporting_service.py
```
