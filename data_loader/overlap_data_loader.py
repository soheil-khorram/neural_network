# Author: Soheil Khorram
# License: Simplified BSD

import os
import pickle
from keras.utils import Sequence, np_utils
import numpy as np


class Data:
    class Subset(Sequence):
        def __init__(self):
            self.ids = None
            self.X = None  # inputs
            self.y = None  # outputs
            self._l = None  # lengths
            # Following properties are for data generation
            self.shuffle = None
            self.gen_indexes = None

        def set_params(self, prm):
            self.down_up_num = prm.down_up_num
            self.utt_in_dim = prm.utt_in_dim
            self.utt_pad_lab = prm.utt_pad_lab
            self.batch_size = prm.batch_size
            self.utt_out_dim = prm.utt_out_dim

        def load(self, mfbs, labs, shuffle):
            self.shuffle = shuffle
            self.X = mfbs
            self.y = labs
            self._l = np.array([self.X[i].shape[0] for i in range(self.X.shape[0])])
            self.ids = np.array([str(i) for i in range(self.X.shape[0])])
            self.sort_data()
            self.chunk_data()
            self.zero_pad_data()
            self.on_epoch_end()

        def sort_data(self):
            sort_inds = np.argsort(self._l)
            self.X = self.X[sort_inds]
            self.y = self.y[sort_inds]
            self._l = self._l[sort_inds]
            self.ids = self.ids[sort_inds]

        def zero_pad_data(self):
            for c in range(len(self.ids)):
                utt_len = self._l[c][-1] + 0.0
                if self.down_up_num != 0:
                    temp = 2 ** self.layer_num + 0.0
                    utt_len = (np.ceil(utt_len / temp) * temp).astype(int)
                utt_len = int(utt_len)
                utt_num = len(self.ids[c])
                batch_X = np.zeros((utt_num, utt_len, self.utt_in_dim))
                batch_y = self.utt_pad_lab * np.ones((utt_num, utt_len), dtype=int)
                for u in range(utt_num):
                    batch_X[u, :self._l[c][u], :] = self.X[c][u]
                    batch_y[u, :self._l[c][u]] = self.y[c][u]
                self.X[c] = batch_X
                self.y[c] = batch_y

        def chunk_data(self):
            num_of_chunks = int(np.ceil((len(self.ids) + 0.0) / self.batch_size))
            self.ids = np.array([self.ids[c * self.batch_size: (c + 1) * self.batch_size]
                                 for c in range(num_of_chunks)])
            self.X = np.array([self.X[c * self.batch_size: (c + 1) * self.batch_size]
                               for c in range(num_of_chunks)])
            self.y = np.array([self.y[c * self.batch_size: (c + 1) * self.batch_size]
                               for c in range(num_of_chunks)])
            self._l = np.array([self._l[c * self.batch_size: (c + 1) * self.batch_size]
                                for c in range(num_of_chunks)])

        def on_epoch_end(self):
            'Updates indexes after each epoch'
            self.gen_indexes = np.arange(len(self.ids))
            if self.shuffle:
                np.random.shuffle(self.gen_indexes)

        def __len__(self):
            'Denotes the number of batches per epoch'
            return len(self.ids)

        def __getitem__(self, index):
            'Generate one batch of data'
            batch_y = np_utils.to_categorical(self.y[self.gen_indexes[index]], self.utt_out_dim)
            return self.X[self.gen_indexes[index]], batch_y

    def parse_arguments(self, parser):
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = base_path + '/../../data_overlap'
        parser.add_argument('-mfb-file', default=data_path + '/mfbs.npy',
                            type=str, help='path for the mfb file')
        parser.add_argument('-lab-file', default=data_path + '/short_labels.npy',
                            type=str, help='path for the label file')
        parser.add_argument('-down-up-num', default=0,
                            type=int, help='in the case of down-sampling up-sampling network')
        parser.add_argument('-utt-in-dim', default=40,
                            type=int, help='dimensionality of the input')
        parser.add_argument('-utt-pad-lab', default=0,
                            type=int, help='label to be added in the case of zepo padding')
        parser.add_argument('-batch-size', default=32,
                            type=int, help='batch size')
        parser.add_argument('-utt-out-dim', default=2,
                            type=int, help='output dimensionality')

    def set_params(self, prm):
        self.mfb_file = prm.mfb_file
        self.lab_file = prm.lab_file
        self.tr.set_params(prm)
        self.de.set_params(prm)
        self.te.set_params(prm)

    def __init__(self):
        self.tr = Data.Subset()
        self.de = Data.Subset()
        self.te = Data.Subset()

    def load(self):
        all_mfbs = np.load(self.mfb_file)
        all_labs = np.load(self.lab_file)
        sample_num = all_mfbs.shape[0]
        inds = np.arange(sample_num)
        np.random.shuffle(inds)
        all_mfbs = all_mfbs[inds]
        all_labs = all_labs[inds]
        tr_mfbs = all_mfbs[:int(sample_num / 2)]
        tr_labs = all_labs[:int(sample_num / 2)]
        de_mfbs = all_mfbs[int(sample_num / 2):int(3 * sample_num / 4)]
        de_labs = all_labs[int(sample_num / 2):int(3 * sample_num / 4)]
        te_mfbs = all_mfbs[int(3 * sample_num / 4):]
        te_labs = all_labs[int(3 * sample_num / 4):]
        self.tr.load(tr_mfbs, tr_labs, shuffle=True)
        self.de.load(de_mfbs, de_labs, shuffle=False)
        self.te.load(te_mfbs, te_labs, shuffle=False)
