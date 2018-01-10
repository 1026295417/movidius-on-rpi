#!/usr/bin/python3

import mvnc.mvncapi as mvnc
import numpy
import os
import sys
import socket                   # Import socket module
import time
import cv2
import cPickle as pickle
import skimage
from skimage import io, transform
NCAPPZOO_PATH           = os.path.expanduser( '~/workspace/ncappzoo' )
GRAPH_PATH              = NCAPPZOO_PATH + '/caffe/GenderNet/graph' 
LABELS_FILE_PATH        = NCAPPZOO_PATH + '/data/ilsvrc12/synset_words.txt'
IMAGE_MEAN              = [ 104.00698793, 116.66876762, 122.67891434]
IMAGE_STDDEV            = 1
IMAGE_DIM               = ( 224, 224 )

devices = mvnc.EnumerateDevices()
if len( devices ) == 0:
    print( 'No devices found' )
    quit()
device = mvnc.Device( devices[0] )
device.OpenDevice()
with open( GRAPH_PATH, mode='rb' ) as f:
    blob = f.read()
graph = device.AllocateGraph( blob )

# ---- Step 3: Offload image onto the NCS to run inference -------------------

while True:
    s = socket.socket()  # Create a socket object
    # host = socket.gethostname()     # Get local machine name
    host = 'rpi1'
    port = 33333
    s.connect((host, port))
    s.send("Hello server!")
    data = []

    while True:
        buffer = s.recv(4096)
        data.append(buffer)
        if not buffer:
            break
    joined_data = b"".join(data)  # Make the final message

    s.close()
    frame = pickle.loads(str(joined_data))
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    img = skimage.transform.resize( frame, IMAGE_DIM, preserve_range=True )

    # Convert RGB to BGR [skimage reads image in RGB, but Caffe uses BGR]
    img = img[:, :, ::-1]

    # Mean subtraction & scaling [A common technique used to center the data]
    img = img.astype( numpy.float32 )
    img = ( img - IMAGE_MEAN ) * IMAGE_STDDEV

    # Load the image as a half-precision floating point array
    graph.LoadTensor( img.astype( numpy.float16 ), 'user object' )

    # ---- Step 4: Read & print inference results from the NCS -------------------

    # Get the results from NCS
    output, userobj = graph.GetResult()

    # Print the results
    print('\n------- predictions --------')

    labels = numpy.loadtxt( LABELS_FILE_PATH, str, delimiter = '\t' )

    order = output.argsort()[::-1][:2]

    for i in range( 0, 2):
        print ('prediction ' + str(i) + ' is ' + labels[order[i]])


graph.DeallocateGraph()
device.CloseDevice()

# ==== End of file ===========================================================

