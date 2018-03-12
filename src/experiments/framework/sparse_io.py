import scipy.sparse


def save_sparse_matrix(x):
    row = x.row
    col = x.col
    data = x.data
    shape = x.shape
    return {'row':row, 'col':col, 'data':data, 'shape':shape}


def load_sparse_matrix(y):
    y = y.item()
    return scipy.sparse.coo_matrix((y['data'], (y['row'], y['col'])), shape=y['shape'])
