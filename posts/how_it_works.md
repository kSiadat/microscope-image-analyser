# How the program works
This post gives a brief overview of how the program works.
It will focus on the analysis part of the program because even though the GUI is a large portion of the code, it is boring and not unique in any way.

## Overview
The overview is probably easiest to explain working backwards from the goal, but the rest of this post will be done in the same order as the analysis itself.
The aim of the program is to work out the diameter of each cluster, and to work out the diameter of a cluster you need to know the coordinates of each of the pixels within it.
Working out the pixels in an image is a bit tricky. I initially tried just setting a threshold so that all pixels below a certain value are counted as part of a cluster, but this picked up a lot of noise. After a bit of experimentation I decided on a 2 threshold method, where a lower threshold is used to find the centre of each cluster, then a high threshold is used to find the whole cluster.

## Setting thresholds
The value that the 2 thresholds should be set to depends on 

## Identifying the pixels in each cluster

## Calculating the diameter