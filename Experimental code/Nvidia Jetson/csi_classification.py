#!/usr/bin/env python3

from jetson_inference import imageNet
from jetson_utils import videoSource, videoOutput

import argparse

# parse the command line
parser = argparse.ArgumentParser()
parser.add_argument("--network", type=str, default="googlenet", help="model to use, can be: googlenet, resnet-18, etc.")
parser.add_argument("--camera", type=str, default="csi://0", help="camera device to use")
parser.add_argument("--width", type=int, default=1280, help="desired width of camera stream (default is 1280 pixels)")
parser.add_argument("--height", type=int, default=720, help="desired height of camera stream (default is 720 pixels)")
args = parser.parse_args()

# create video sources & outputs
camera = videoSource(args.camera, argv=["--input-width=" + str(args.width), "--input-height=" + str(args.height)])
display = videoOutput("display://0")

# load the recognition network
net = imageNet(args.network)

# process frames until user exits
while display.IsStreaming():
    img = camera.Capture()
    if img is None:
        continue

    # classify the image
    class_idx, confidence = net.Classify(img)

    # find the object description
    class_desc = net.GetClassDesc(class_idx)

    # print out the result
    print("image is recognized as '{:s}' (class #{:d}) with {:f}% confidence".format(class_desc, class_idx, confidence * 100))

    # render the image
    display.Render(img)

    # update the title bar
    display.SetStatus("{:s} | Network {:.0f} FPS".format(net.GetNetworkName(), net.GetNetworkFPS()))

# release resources
del camera
del display
del net

