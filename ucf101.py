########################################
#     import requirement libraries     #
########################################
import os
import numpy as np
import random
import cv2

from keras.utils import to_categorical
li = []
class Spatial():
    def __init__(self, root_dir, batch_size):
        self._data_list = None
        self._root_dir = root_dir
        self._batch_size = batch_size
        self._front_idx = 0
        self._end_idx = batch_size

    def set_data_list(self, _data_txt, _shuffle=True):
        self._data_list = self.data_dir_reader(_data_txt)

        if _shuffle:
            random.shuffle(self._data_list)


    @staticmethod
    def data_dir_reader(_txt_path):

        tmp = []
        f = open(_txt_path, 'r')
        for dir_name in f.readlines():
            tmp.append(dir_name)

        return tmp

    def next_batch(self):

        data = []
        label = []
        end_of_file = False

        for video_name in self._data_list[self._front_idx: self._end_idx]:
            video_name = video_name.replace('\n', '')
            label_name = int(video_name.split(' ')[-1]) - 1
            video_name = video_name.split(' ')[0]
            video_name = video_name.split('.')[0]
            video_name = video_name.split('/')[-1]


            file_root = self._root_dir + video_name + '/'
            file_list = os.listdir(file_root)
            random.shuffle(file_list)
            file_list = file_list[0:19]         # TODO: 19 must be modified variable params
            file_list = sorted(file_list)

            data.append(self.make_input_shape(file_list, file_root))
            li.append(label_name)
            onehot_label = to_categorical(label_name, num_classes=101)
            label.append(onehot_label)
            # TODO: make label using video_name

        self._front_idx += self._batch_size
        self._end_idx += self._batch_size

        if self._end_idx > len(self._data_list):
            self._end_idx = len(self._data_list)

        if self._front_idx > len(self._data_list):
            end_of_file = True
            self._front_idx = 0
            self._end_idx = self._batch_size

        if not data:
            print("Data is empty!!")

        if not label:
            print('Label is empty!!')

        return np.asarray(data), np.asarray(label), end_of_file

    @staticmethod
    def make_input_shape(_file_list, _file_root):

        result = None
        for file in _file_list:
            file_path = _file_root + file
            img = cv2.imread(file_path,cv2.IMREAD_COLOR)
            if img is None:
                print(file_path)
            img = cv2.resize(img,(224,224) )

            if result is not None:
                # result = np.concatenate((result, img), axis=2)
                result = np.dstack((result, img))
                del img
                continue

            result = img


        return result

    def shuffle(self):

        if not self._data_list:
            print('Data list is None')
        random.shuffle(self._data_list)


class Temporal(Spatial):
    pass


if __name__=='__main__':

    # UCF-101 data loader
    root = '/home/jm/Two-stream_data/jpegs_256/'
    txt_root = '/home/jm/Two-stream_data/trainlist01.txt'

    loader = Spatial(root, batch_size=300)
    loader.set_data_list(txt_root)


    n = 0
    for epoch in range(5):
        while 1:
            x, y, eof = loader.next_batch()

            print(x.shape)
            n += 1

            if eof:
                break

    a = list(set(li))
    print(a)





