########################################
#     import requirement libraries     #
########################################
import os
import numpy as np
import random
import cv2
import glob
import re

# one hot encoding relate
from keras.utils import to_categorical
#from keras.preprocessing.image import ImageDataGenerator

saction = ['brush_hair','cartwheel','catch','chew','clap','climb','climb_stairs',
      'dive','draw_sword','dribble','drink','eat','fall_floor','fencing',
      'flic_flac','golf','handstand','hit','hug','jump','kick_ball',
      'kick','kiss','laugh','pick','pour','pullup','punch',
      'push','pushup','ride_bike','ride_horse','run','shake_hands','shoot_ball',
      'shoot_bow','shoot_gun','sit','situp','smile','smoke','somersault',
      'stand','swing_baseball','sword_exercise','sword','talk','throw','turn','walk','wave']

class MakePreprocessData():

    def __init__(self, _L): #, _bgr_min_max, _flow_min_max):
        self._frames_root = '/home/jm/Two-stream_data/HMDB51/frames'
        self._flow_root = '/home/jm/Two-stream_data/HMDB51/flow'
        self._save_path = '/home/jm/Two-stream_data/HMDB51/npy'
        self._L = _L

    def sampling_stack_frame(self, _flow_path):

        # extract start frame number using number of still image frame
        flow_all_list = os.listdir(_flow_path)
        flow_list = {'x': [], 'y': []}
        frame_length = len(flow_all_list)/2

        assert frame_length > self._L
        sampling_interval = int(frame_length/self._L)

        for flow in flow_all_list:
            if re.split('[_.]', flow)[1] == 'x':
                flow_list['x'].append(flow)

            elif re.split('[_.]', flow)[1] == 'y':
                flow_list['y'].append(flow)

        flow_list['x'] = sorted(flow_list['x'])
        flow_list['y'] = sorted(flow_list['y'])


        _sampled_x_flow = []
        _sampled_y_flow = []
        for index in range(0,self._L):
            clip_idx = index * sampling_interval
            _sampled_x_flow.append(flow_list['x'][clip_idx])
            _sampled_y_flow.append(flow_list['y'][clip_idx])

        return _sampled_x_flow, _sampled_y_flow

    """
    def select_flow_frame(self,_flow_path, _start_num):

        # To make flow data format, select start frame to L'th flow frame
        flow_all_list = os.listdir(_flow_path)
        flow_list = {'x':[], 'y':[]}

        # separate x and y disparity images
        for flow in flow_all_list:
            if re.split('[_.]', flow)[1] == 'x':
                flow_list['x'].append(flow)

            elif re.split('[_.]', flow)[1] == 'y':
                flow_list['y'].append(flow)

        print(flow_list['x'])
        _flow_x_list = sorted(flow_list['x'])
        _flow_y_list = sorted(flow_list['y'])
        print(_flow_x_list)

        return _flow_x_list[_start_num: _start_num+self._L], _flow_y_list[_start_num: _start_num+self._L]
    """
    @staticmethod
    def make_temporal_data(_flow_path, _flow_x_list, _flow_y_list):

        assert len(_flow_x_list) == len(_flow_y_list)

        """
        # mean flow substraction
        opt_mean_x = opt_mean_y = None
        for idx in range(len(_flow_x_list)):
            x_name = _flow_path + '/' + _flow_x_list[idx]
            y_name = _flow_path + '/' + _flow_y_list[idx]

            if idx == 0:
                opt_mean_x = cv2.imread(x_name, cv2.IMREAD_GRAYSCALE)
                opt_mean_y = cv2.imread(y_name, cv2.IMREAD_GRAYSCALE)
                continue

            opt_mean_x = opt_mean_x + cv2.imread(x_name, cv2.IMREAD_GRAYSCALE)
            opt_mean_y = opt_mean_y + cv2.imread(y_name, cv2.IMREAD_GRAYSCALE)

        opt_mean_x = opt_mean_x / len(_flow_x_list)
        opt_mean_y = opt_mean_y /  len(_flow_y_list)
        """


        for idx in range(len(_flow_x_list)):
            x_name = _flow_path + '/' + _flow_x_list[idx]
            y_name = _flow_path + '/' + _flow_y_list[idx]

            opt_x = cv2.imread(x_name, cv2.IMREAD_GRAYSCALE) #- opt_mean_x
            opt_y = cv2.imread(y_name, cv2.IMREAD_GRAYSCALE) #- opt_mean_y

            opt = np.dstack([opt_x, opt_y])
            normalized_opt = opt/255

            if idx == 0:
                #stacked_opt = np.dstack([resized_opt_x, resized_opt_y])
                stacked_opt = normalized_opt
                continue

            stacked_opt = np.dstack([stacked_opt, normalized_opt])

        resized_opt = random_cropping(stacked_opt, 224)

        return resized_opt.astype(np.float)

    @staticmethod
    def make_label(_action):

        assert _action in saction

        label = saction.index(_action)
        categorical_label = to_categorical(label, num_classes=51)

        return categorical_label.astype(np.uint8)

    def make_spatial_data(self, _frame_path, _action, _vnumber):
        spatial_save_path = os.path.join(self._save_path, 'frame')
        for _frame_name in os.listdir(_frame_path):
            img_name = _frame_path + '/' + _frame_name
            img = cv2.imread(img_name)

            save_name = "%s-%05d" % (_action, int(_vnumber))
            save_name = spatial_save_path + save_name

            # save original image after resize
            resized_img = cv2.resize(img, 224)
            resized_img = resized_img/255          # for normalize
            resized_save_path = save_name + '-original.npy'
            np.save(resized_save_path, resized_img.astype(np.float16))

            # save augmentation image after cropping and flipping
            for i in range(5):
                cropped_img = random_cropping(img, 224)
                flipped_img = horizontal_flip(cropped_img)

                cropped_img = cropped_img/255
                flipped_img = flipped_img/255   # for normalize

                cropped_save_path = save_name + '-cropped-%d.npy' % i
                flipped_save_path = save_name + '-flipped-%d.npy' % i

                np.save(cropped_save_path, cropped_img)
                np.save(flipped_save_path, flipped_img)

        return 0

    def run(self):

        for action in os.listdir(self._flow_root):
            action_frame_path = self._frames_root + '/' + action
            action_flow_path = self._flow_root + '/' + action

            for video_number in os.listdir(action_flow_path):
                frame_path = action_frame_path + '/' + video_number
                flow_path = action_flow_path + '/' + video_number

                flow_x_list, flow_y_list = self.sampling_stack_frame(flow_path)

                #run all preprocess procedure
                self.make_spatial_data(frame_path, action, video_number)
                result_flow = self.make_temporal_data(flow_path, flow_x_list, flow_y_list)
                result_label = self.make_label(action)


def random_cropping(_image, _size):
    row, col, _ = _image.shape
    left, top = random.choice(range(0, row - _size)), random.choice(range(0, col - _size))

    return _image[left:left+_size, top:top+_size]

def horizontal_flip(_image):
    return cv2.flip(_image,1)

def normalize(_data_path):

    data = []
    for file_name in os.listdir(_data_path):
        full_path = _data_path + '/' + file_name
        dat = np.load(full_path)
        data.append(dat)

    mean = np.mean(data,axis=0)
    std = np.std(data,axis=0)
    del data

    """
    save_path = "/home/jm/Two-stream_data/npy/255_norm_flow/"
    for file_name in os.listdir(_data_path):
        full_path = _data_path + '/' + file_name
        dat = np.load(full_path)
        dat = dat/255
        # dat.astype(np.uint8)
        np.save(save_path+file_name, dat)
        del dat
    """

if __name__ == '__main__':

    """
    bgr_min_max = {'b': [0, 255],
                   'g': [0, 255],
                   'r': [0, 255]}
    flow_min_max = {'x': [0, 255],
                    'y': [0, 255]}
    """

    preprocess = MakePreprocessData(10)
    preprocess.run()

    #preprocess = MakePreprocessData(10)
    #preprocess.run()


