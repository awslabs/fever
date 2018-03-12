## FEVER (Fact Extraction and VERification) Annotation Platform and Baselines

This repository contains the FEVER annotation platform code (annotation UI) and the baselines described in the [NAACL 2018 paper](TODO).

### Setup
To set up the packages, run:
```bash
python3 setup.py install
```

### Running the annotation UI
To run the annotation UI, run:
```bash
export AWS_ACCESS_KEY_ID=<YOUR_ID> 
export AWS_SECRET_ACCESS_KEY=<YOUR_SECRET>

export SQLALCHEMY_DATABASE_URI=<URI>


export AWS_DEFAULT_REGION=eu-west-1

python3  src/annotation/flask_services/annotation_service.py
```

### Running the baseline experiments
TODO

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
