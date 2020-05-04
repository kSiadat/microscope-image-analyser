# microscope-image-analyser
Calculates number and diameter of particle clusters in TEM microscope images, has GUI and results saving

## Features
+ Image analysis
  + The program can analyse images to identify clusters of particles within it
  + For each cluster it calculates an average diameter in pixels
  + Analysis can probably be applied to similar images in different contexts, but I don't know because I haven't tested it
+ Results display
  + The user is shown a histogram of frequency against diameter
  + You can also switch between viewing the histogram, the original image, or an 'analysed version' of the image which allows the user to check the analysis worked properly
  + Up to 10 results can be open at a time, and you can switch between them and delete them
+ Saving/loading results
  + There is the option to save results after analysis
  + Results are saved in comma seperated value format so that they can be imported in to other programs for further use

## Limitations
+ For images with high amounts of clusters, analysis may take several minutes
+ For images with very low amounts of clusters, the results can vary
+ It doesn't work if multiple objects overlap each other, as they will be detected as 1 object
+ Scale entry is very limited since it currently only works if the scale bar is about 127 pixels long, I plan on fixing this in the future
+ You are limited to having 10 results open at once
+ There is no inbuilt method for saving the analysed image
+ Saving results in a text file is inefficient use of space

## How it works
I plan on creating an article about how the program works soon

## Other
+ I will add some sample images in the future
+ This project was made for a materials science researcher at Newcastle University
+ This project was also made for computer science A level coursework
