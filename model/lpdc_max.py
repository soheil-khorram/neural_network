# Author: Soheil Khorram
# License: Simplified BSD


from keras.layers import Conv1D, Input, Add, MaxPooling1D
from keras.models import Model
from keras.optimizers import Adam
from keras.regularizers import l2
from model.keras_net import KerasNet


class Net(KerasNet):
    def __init__(self):
        super(Net, self).__init__()

    def parse_arguments(self, parser):
        super(Net, self).parse_arguments(parser)
        parser.add_argument('-lpdc-num', default=5, type=int)
        parser.add_argument('-lpdc-depth', default=4, type=int)
        parser.add_argument('-kernel-size', default=3, type=int)
        parser.add_argument('-pool-size', default=3, type=int)
        parser.add_argument('-dilation-size', default=3, type=int)
        parser.add_argument('-kernel-num', default=512, type=int)
        parser.add_argument('-activation', default='relu', type=str)
        parser.add_argument('-l2', default=0.0, type=float)
        parser.add_argument('-step-size', default=0.0001,
                            type=float, help='learning rate')
        parser.add_argument('-epoch-num', default=20,
                            type=int, help='number of epochs')
        # parser.add_argument('-utt-out-dim', default=3393,
        #                     type=int, help='dimensionality of the output')
        # parser.add_argument('-utt-in-dim', default=40,
        #                     type=int, help='dimensionality of the input feats')

    def set_params(self, prm):
        super(Net, self).set_params(prm)
        self.lpdc_num = prm.lpdc_num
        self.lpdc_depth = prm.lpdc_depth
        self.kernel_size = prm.kernel_size
        self.pool_size = prm.pool_size
        self.dilation_size = prm.dilation_size
        self.kernel_num = prm.kernel_num
        self.activation = prm.activation
        self.l2 = prm.l2
        self.step_size = prm.step_size
        self.epoch_num = prm.epoch_num
        self.utt_in_dim = prm.utt_in_dim
        self.utt_out_dim = prm.utt_out_dim

    def lpdc(self, x):
        x = self.dilated_conv(x, 1)
        y = x
        for i in range(self.lpdc_depth - 1):
            x = MaxPooling1D(pool_size=self.pool_size,
                             strides=1, padding='same',
                             data_format='channels_last')(x)
            x = self.dilated_conv(x, self.dilation_size ** (i + 1))
            y = Add()([y, x])
        return y

    def dilated_conv(self, x, dilation_rate):
        return Conv1D(filters=self.kernel_num,
                      kernel_size=self.kernel_size,
                      strides=1,
                      padding='same',
                      data_format='channels_last',
                      dilation_rate=dilation_rate,
                      activation=self.activation,
                      use_bias=True,
                      kernel_initializer='glorot_uniform',
                      bias_initializer='zeros',
                      kernel_regularizer=l2(self.l2),
                      bias_regularizer=l2(self.l2),
                      activity_regularizer=None)(x)

    def last_conv(self, x):
        return Conv1D(filters=self.utt_out_dim,
                      kernel_size=1,
                      strides=1,
                      padding='same',
                      data_format='channels_last',
                      dilation_rate=1,
                      activation='softmax',
                      use_bias=True,
                      kernel_initializer='glorot_uniform',
                      bias_initializer='zeros',
                      kernel_regularizer=l2(self.l2),
                      bias_regularizer=l2(self.l2),
                      activity_regularizer=None)(x)

    def construct(self):
        inp = Input(shape=(None, self.utt_in_dim))
        x = inp
        x = self.dilated_conv(x, 1)
        for i in range(self.lpdc_num):
            x = self.lpdc(x)
        x = self.last_conv(x)
        outp = x
        self._net = Model(inputs=inp, outputs=outp)
        self._net.compile(optimizer=Adam(lr=self.step_size),
                          loss='categorical_crossentropy')
