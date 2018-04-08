# Copyright 2018 Amazon Research Cambridge
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from jnius import autoclass

Properties = autoclass("java.util.Properties")
StanfordCoreNLP = autoclass("edu.stanford.nlp.pipeline.StanfordCoreNLP")
CoreAnnotations = autoclass("edu.stanford.nlp.ling.CoreAnnotations")

CoreAnnotations.TokensAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$TokensAnnotation")
CoreAnnotations.SentencesAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$SentencesAnnotation")
CoreAnnotations.TextAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$TextAnnotation")
CoreAnnotations.NamedEntityTagAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$NamedEntityTagAnnotation")
CoreAnnotations.PartOfSpeechAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$PartOfSpeechAnnotation")
CoreAnnotations.LineNumberAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$LineNumberAnnotation")

CoreAnnotations.NumericValueAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$NumericValueAnnotation")
CoreAnnotations.NumericTypeAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$NumericTypeAnnotation")
CoreAnnotations.NumericCompositeValueAnnotation = autoclass("edu.stanford.nlp.ling.CoreAnnotations$NumericCompositeValueAnnotation")

CorefChainAnnotation = autoclass("edu.stanford.nlp.hcoref.CorefCoreAnnotations$CorefChainAnnotation")

Double = autoclass("java.lang.Double")
BigDecimal = autoclass("java.math.BigDecimal")

CoreLabel = autoclass("edu.stanford.nlp.ling.CoreLabel")
IndexedWord = autoclass("edu.stanford.nlp.ling.IndexedWord")
Annotation = autoclass("edu.stanford.nlp.pipeline.Annotation")
SemanticGraph = autoclass("edu.stanford.nlp.semgraph.SemanticGraph")

SemanticGraphCoreAnnotations = autoclass("edu.stanford.nlp.semgraph.SemanticGraphCoreAnnotations")
SemanticGraphCoreAnnotations.CollapsedCCProcessedDependenciesAnnotation = autoclass("edu.stanford.nlp.semgraph.SemanticGraphCoreAnnotations$CollapsedCCProcessedDependenciesAnnotation")


Integer = autoclass("java.lang.Integer")

SemanticGraphEdge = autoclass("edu.stanford.nlp.semgraph.SemanticGraphEdge")
CoreMap = autoclass("edu.stanford.nlp.util.CoreMap")

NumberNormalizer = autoclass("edu.stanford.nlp.ie.NumberNormalizer")


TreeCoreAnnotations = autoclass("edu.stanford.nlp.trees.TreeCoreAnnotations")
TreeCoreAnnotations.TreeAnnotation = autoclass("edu.stanford.nlp.trees.TreeCoreAnnotations$TreeAnnotation")


class SentenceSplittingPipeline:
    pipeline = None

    def __init__(self):
        if self.pipeline is None:
            props = Properties()
            props.setProperty("annotators", "tokenize,ssplit")
            props.setProperty("parse.maxlen","120")
            pipeline = StanfordCoreNLP(props)
            self.pipeline = pipeline

    def getInstance(self):
        return self.pipeline


class POSPipeline:
    pipeline = None

    def __init__(self):
        if self.pipeline is None:
            props = Properties()
            props.setProperty("annotators", "tokenize,ssplit,pos")
            props.setProperty("parse.maxlen","120")
            pipeline = StanfordCoreNLP(props)
            self.pipeline = pipeline

    def getInstance(self):
        return self.pipeline


