import scipy.sparse
from experiments.framework.sparse import sp_len


class Batching():
    def __init__(self, data, labels, step):
        self.data = data
        self.labels = None

        if labels is not None:
            self.labels = labels
            assert sp_len(data) == sp_len(labels), "Data length is different to the labels length"

        if scipy.sparse.isspmatrix(self.data):
            self.data = self.data.tocsr()

        self.ptr = 0
        self.step = step

    def __iter__(self):
        return self

    def __next__(self):
        if self.ptr >= sp_len(self.data):
            self.stop()

        batch_data = self.data[self.ptr:min(sp_len(self.data), self.ptr + self.step)]

        batch_labels = None
        if self.labels is not None:
            batch_labels = self.labels[self.ptr:min(sp_len(self.data), self.ptr + self.step)]

        self.ptr += self.step

        if sp_len(batch_data) == 0:
            self.stop()

        return batch_data,batch_labels, sp_len(batch_data)

    def stop(self):
        self.ptr = 0
        raise StopIteration()
