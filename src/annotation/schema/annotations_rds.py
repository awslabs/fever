import os

from sqlalchemy import create_engine, ForeignKey, Index, BigInteger, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import Column, Integer, String, Text

LargeIntegerType = BigInteger
Base = declarative_base()


class Processed(Base):
    __tablename__ = "processed"
    id = Column(String(64), primary_key=True)
    Index("processed_uuid_idx", id)


class Entity(Base):
    __tablename__ = "entity"
    name = Column(String(191), primary_key=True)

    sentences = relationship("Sentence", back_populates="entity")

    def __repr__(self):
        return "<Entity(name='%s')>" % self.name


class Sentence(Base):
    __tablename__ = "sentence"
    id = Column(LargeIntegerType, primary_key=True)
    dataset_id = Column(LargeIntegerType)
    entity_id = Column(String(191), ForeignKey(Entity.name))
    entity = relationship("Entity", back_populates='sentences')
    text = Column(Text)
    claims = relationship("Claim", back_populates="sentence")


class ClaimMutationType(Base):
    __tablename__ = "mutation_type"
    name = Column(String(40), primary_key=True)
    mutations = relationship("Claim", back_populates="mutation_type")


class Claim(Base):
    __tablename__ = "claim"
    id = Column(LargeIntegerType, primary_key=True)
    text = Column(Text)

    sentence_id = Column(LargeIntegerType, ForeignKey(Sentence.id))
    sentence = relationship(Sentence, back_populates="claims")
    created = Column(DateTime)
    inserted = Column(DateTime)
    user = Column(String(64))
    version = Column(Integer)
    testing = Column(Boolean)
    timeTakenToAnnotate = Column(Integer)

    isOracle = Column(Boolean, default=False)
    isReval = Column(Boolean, default=False)

    mutation_type_id = Column(String(40), ForeignKey(ClaimMutationType.name))
    mutation_type = relationship(ClaimMutationType, back_populates="mutations")

    original_claim_id = Column(LargeIntegerType, ForeignKey("claim.id"))

    uuid = Column(String(64), unique=True)
    Index("uuid_idx", uuid)

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }


class Annotation(Base):
    __tablename__ = "annotation"
    id = Column(LargeIntegerType, primary_key=True)
    user = Column(String(100))
    claim_id = Column(LargeIntegerType, ForeignKey(Claim.id))
    combined = Column(Boolean)
    page = Column(String(191))
    sentencesVisited = Column(Integer)
    customPagesAdded = Column(Integer)
    timeTakenToAnnotate = Column(Integer)
    verifiable = Column(Integer)
    version = Column(Integer)
    created = Column(DateTime)

    isTestMode = Column(Boolean, default=False)
    isOracleMaster = Column(Boolean, default=False)
    isDiscounted = Column(Boolean, default=False)
    isForReportingOnly = Column(Boolean, default=False)

    Index("user_idx", user)


class AnnotationVerdict(Base):
    __tablename__ = "annotation_verdict"
    id = Column(LargeIntegerType, primary_key=True)
    annotation_id = Column(LargeIntegerType, ForeignKey(Annotation.id))
    verdict = Column(Integer)


class LineAnnotation(Base):
    __tablename__ = "verdict_line"
    id = Column(LargeIntegerType, primary_key=True)
    verdict_id = Column(LargeIntegerType, ForeignKey(AnnotationVerdict.id))
    line_number = Column(Integer)
    page = Column(String(191))


class AnnotationAssignment(Base):
    __tablename__ = "annotation_assignment"
    id = Column(LargeIntegerType, primary_key=True)
    user = Column(String(100))
    claim_id = Column(LargeIntegerType, ForeignKey(Claim.id))
    sentence_id = Column(LargeIntegerType, ForeignKey(Claim.sentence_id))
    created = Column(DateTime)
    expires = Column(DateTime)
    Index("assgn_user_idx", user)


def create_session(cs=None):
    if cs is None:
        cs = os.environ['SQLALCHEMY_DATABASE_URI']

    engine = create_engine(cs, echo=False)
    Base.metadata.create_all(engine)

    session = sessionmaker()
    session.configure(bind=engine)
    return session()
