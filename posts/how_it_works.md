# How the program works
This post gives a brief overview of how the program works.
It will focus on the analysis part of the program because even though the GUI is a large portion of the code, it is boring and not unique in any way.
Currently there are no images but I will add some later if I receive confirmation that I can use them.


## Overview
The overview is probably easiest to explain working backwards from the goal, but the rest of this post will be done in the same order as the analysis itself.

The aim of the program is to work out the diameter of each cluster, and to work out the diameter of a cluster you need to know the coordinates of each of the pixels within it.

Working out the pixels in an image is a bit tricky. I initially tried just setting a threshold so that all pixels below a certain value are counted as part of a cluster, but this picked up a lot of noise. After a bit of experimentation I decided on a 2 threshold method, where a lower threshold is used to find the centre of each cluster, then a high threshold is used to find the whole cluster.


## Sanitisation
The image format for the sample of images I was given is png where each pixel is an array like this: (Red,Green,Blue,Transparency).

Since the image is greyscale the RGB values are identical, and every pixel had a transparency of 1 (fully opaque), so each pixel could be reduced to a singe value. I used the Red value since it was the first value in the list.

Doing this made the image easier to process later on because much less indexing had to be used.


## Setting thresholds
The value that the 2 thresholds should be set to depends on how light/dark the background is and how noisy the background is. Since the clusters haven't been identified at this point, this actually means the brightness of the image, and the noisiness of the image.

Overall brightness can be measured by the average pixel value of the image. The images used each have a value from 0 to 1, so the brightness does too.

Noisiness can be measured by calculating the average difference between pixels and their neighbours. The total number of pixels in the images used was about 460 000, so sampling them all for this would have been too time inefficient. To solve the problem the program takes a 1000 10x10 samples. This means that the process can be completed about 4.6 times faster with very little accuracy loss. The samples are taken at random locations which can cause results to vary slightly, although it's only noticeable when the number of clusters is very small.

Once the brightness and noisiness have been measured, I manually set the thresholds. Plotting a using all of this data, it turns out there is a linear relationship between the brightness/noisiness and the lower threshold/ upper threshold/ difference between thresholds. I used the data I had to calculate a regression line that can be used to calculate the thresholds given the brightness and noisiness of an image.


## Identifying the pixels in each cluster
The basic algorithm that does this, takes a starting pixel and marks it as visited, then it checks all adjacent pixels to see if they are below the threshold and records them if they are and marks them as visited. This is repeated for the new pixels and so on.

First of all this is used on the image using a the lower threshold, this gives the centres of the clusters. These centres can still be multiple pixels so only the first pixel is taken from each as a starting point.

Then the starting points are used on the image using the upper threshold, which gives the whole clusters, but without the noise. Often there are multiple starting points that end up being in the same cluster, so you also have to go through and removee duplicates. A little bit of cleanup is also done where pixels that aren't part of a cluster but which border at least 3 pixels within the same cluster are added to that cluster. This removes some of the holes from them, and further reduces the impact of noise.


## Calculating the diameter
The first step to calculating the average diameter is to work out the centre of the cluster, which can be done by taking the mean of the coordinates of every pixel in it.

Next you can calculate multiple radii by starting at the centre point and repeatedly checking further and further outwards 1 pixel at a time in a straight line, until the pixel you are checking is no longer part of the cluster. 

Then adding opposite radii together gives you several diameters, which you can use to work out the average diameter.

Once you have the diameters of each cluster you can plot the histogram of frequency against diameter.
