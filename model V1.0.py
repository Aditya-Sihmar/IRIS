# -*- coding: utf-8 -*-
"""Model 1.0

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NGHFiPSaD_Trya8PIvksAkzWp8KeQrFv
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
import tensorflow as tf
import os
from tqdm import tqdm

path = '/content/drive/My Drive/Anomaly detection/UCF/Anomaly-Detection-Dataset/Normal_Videos_for_Event_Recognition'

videos = []
vid_len = []
img_dim = (128, 128)
n = 0
for vd in tqdm(os.listdir(path)):
  vid = cv2.VideoCapture(os.path.join(path, vd))
  frames = []
  cnt = 0
  n += 1
  while vid.isOpened():
    ret, frame = vid.read()
    if not ret:
      print("Can't receive frame (stream end?). Exiting ...")
      break
    cnt += 1
    gray = cv2.resize((cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))/256, img_dim).reshape([img_dim[0], img_dim[1], 1])
    #cv2.imshow(gray)

    frames.append(gray)
    #if cv2.waitKey(25) & 0xFF == ord('q'): 
     # break
  vid.release()
  #cv2.destroyAllWindows()
  videos.append(frames)
  vid_len.append(cnt)
  if n == 1:
    break

def augment(videos, stride, vid_len, frames = 10):
  agmted = np.zeros((frames, img_dim[0], img_dim[1], 1))
  cnt = 0
  clips = []
  for vid in range(len(vid_len)):
    for strd in stride:
      for frm in range(0, vid_len[vid], strd):
        agmted[cnt, :, :, :] = videos[vid][frm]
        cnt += 1
        if cnt == frames:
          clips.append(agmted)
          cnt = 0
  return np.array(clips)

frames = 10
videos = augment(videos, [1, 2], vid_len,frames)

epochs = 5
def batch_div(videos):
  batches = np.zeros((frames, img_dim[0],img_dim[1],1))
  n = 0 
  for bth in range(0,videos.shape[0],frames):
    if bth+frames <= videos.shape[0]:
      batches[n] = videos[bth:bth+frames]
      n += 1
  return batches

"""keras"""

!pip install keras-layer-normalization

import keras
from keras.layers import Conv2DTranspose, ConvLSTM2D, BatchNormalization, TimeDistributed, Conv2D
from keras.models import Sequential, load_model
from keras_layer_normalization import LayerNormalization

videos[1:1+frames].shape

def model():
    training_set = videos
    seq = Sequential()
    seq.add(TimeDistributed(Conv2D(128, (11, 11), strides=4, padding="same"), batch_input_shape=(None, frames, img_dim[0], img_dim[1], 1)))
    seq.add(LayerNormalization())
    seq.add(TimeDistributed(Conv2D(64, (5, 5), strides=2, padding="same")))
    seq.add(LayerNormalization())
    # # # # #
    seq.add(ConvLSTM2D(64, (3, 3), padding="same", return_sequences=True))
    seq.add(LayerNormalization())
    seq.add(ConvLSTM2D(32, (3, 3), padding="same", return_sequences=True))
    seq.add(LayerNormalization())
    seq.add(ConvLSTM2D(64, (3, 3), padding="same", return_sequences=True))
    seq.add(LayerNormalization())
    # # # # #
    seq.add(TimeDistributed(Conv2DTranspose(64, (5, 5), strides=2, padding="same")))
    seq.add(LayerNormalization())
    seq.add(TimeDistributed(Conv2DTranspose(128, (11, 11), strides=4, padding="same")))
    seq.add(LayerNormalization())
    seq.add(TimeDistributed(Conv2D(1, (11, 11), activation="sigmoid", padding="same")))
    print(seq.summary())
    seq.compile(loss='mse', optimizer=keras.optimizers.Adam(lr=1e-4, decay=1e-5, epsilon=1e-6))
    seq.fit(training_set, training_set,
            batch_size=frames, epochs=epochs, shuffle=False)
    #seq.save(Config.MODEL_PATH)
    return seq

seq = model()

