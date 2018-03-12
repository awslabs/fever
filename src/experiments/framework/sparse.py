import scipy.sparse


def sp_len(obj):
    if scipy.sparse.issparse(obj):
        return obj.shape[0]
    else:
        return len(obj)