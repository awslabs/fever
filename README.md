# FEVER (Fact Extraction and VERification) Annotation Platform and Baselines

This repository contains the FEVER annotation platform code (annotation UI) and the baselines described in the [NAACL 2018 paper](https://arxiv.org/abs/1803.05355) as part of the Fact Extraction and VERification Shared Task. More information is available on [our website](https://sheffieldnlp.github.io/fever). 

### Setup
To set up the packages, run:
```bash
python3 setup.py install
```

## Guides

* [(optional) Creating the candidate sentences from the Wikipedia dump](src/annotation/README.md)
* [Running the annotation interface](src/dataset/README.md)




## Citation

If you use this work, please cite the following:

James Thorne, Andreas Vlachos, Christos Christodoulopoulos, and Arpit Mittal (2018). FEVER: a Large-scale Dataset for Fact Extraction and VERification. In *Proceedings of the 16th Annual Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)*

```
@inproceedings{Thorne18Fever,
    author = {Thorne, James and Vlachos, Andreas and Christodoulopoulos, Christos and Mittal, Arpit},
    title = {{FEVER}: a Large-scale Dataset for Fact Extraction and VERification},
    booktitle = {NAACL-HLT},
    year = {2018}
}
```

## License

This library is licensed under the Apache 2.0 License. 
