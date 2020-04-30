from functools import partial
from math import cos, sin, pi
import matplotlib.image as matImg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.pyplot import hist
from matplotlib.ticker import MaxNLocator
from os import mkdir, listdir, remove, rmdir, getcwd
from PIL import Image, ImageTk
from random import randint
from time import perf_counter
import tkinter as tk
import tkinter.ttk
from tkinter import filedialog



class particle():
    def __init__(self, coordinates, image, threshold):
        self.coordinates = coordinates
        self.centre = [0, 0]
        self.diameters = []
        self.diameter = 0
        self.roundness = 0
        self.calc_all(image, threshold)

    def calc_all(self, image, threshold):
        #Performs all possible calcuclations for the object in the correct order
        self.calc_centre()
        self.calc_diameter(image, threshold)

    def calc_centre(self):
        #Calculates the centre of an object given its coordinates
        total = [0, 0]
        for C in self.coordinates:
            for x in range(2):
                total[x] += C[x]#Add individual pixel's coordinates to total list
        self.centre = [total[x]/len(self.coordinates) for x in range(2)]#Centre = mean of all pixels

    def calc_diameter(self, image, threshold):
        #Calcultes diameters and the average diameter
        radii = []
        times = 20#Number of radii checked, double number of diameters calculated
        for x in range(times):
            radii.append(0)
            angle = (x*2*pi) / times
            hyp = 0#Length of radius being checked
            done = False
            while not done:
                pos = [round((hyp*sin(angle))+self.centre[0]), round((hyp*cos(angle)+self.centre[1]))]
                if (not (0<=pos[0]<len(image))) or (not (0<=pos[1]<len(image[0]))):
                    done = True
                    radii[x-1] += 0.5
                elif image[pos[0]][pos[1]] > threshold:
                    done = True
                    radii[x-1] += 0.5
                else:
                    radii[x-1] = hyp#If pixel checked within image then radius set to current length
                hyp += 1
        self.diameters= []
        for x in range(len(radii)//2):
            self.diameters.append(radii[x] + radii[x+(len(radii)//2)])#Diameter = 2 opposing radi
        total = 0
        for D in self.diameters:
            total += D
        self.diameter = total / len(self.diameters)#Average diameter  = mean of all diameters



class image():
    def __init__(self, imgFile, outputDir):
        self.fileName = imgFile
        self.outputDir = outputDir
        self.raw = matImg.imread(self.fileName)
        self.processed1 = [[Y[0]  for Y in X]  for X in self.raw]
        self.processed2 = [[Y[0]  for Y in X]  for X in self.raw]
        self.equationDiff = [[-7.32865362, 0.7848573668], [-4.023877903, 0.5443113373]]
        self.equationAvg = [[1.184266903, -0.550559971], [0.5989025455, -0.159198544]]
        self.sampleNum = 1000
        self.sampleWidth = 10

    def background_check(self):
        #Find the average value and noisiness of background
        corners = []
        for x in range(self.sampleNum):#each item is a random coordinate within image, and has at least 1 pixel on each side of sample
            corners.append([randint(1,len(self.raw)-self.sampleWidth-1), randint(1,len(self.raw[0])-self.sampleWidth-1)])
        average = 0#Mean value
        difference = 0#Mean of mean difference between pixel and neighbours
        for c, C in enumerate(corners):#For each sample
            for x in range(self.sampleWidth):#For each row...
                for y in range(self.sampleWidth):#...and column within sample
                    pos = [C[0]+x, C[1]+y]#Position of current pixel
                    average += self.raw[pos[0]][pos[1]][0]
                    for a in range(3):
                        for b in range(3):#For all adjacent pixels
                            if a!=1 or b!=1:#If not current pixel
                                adjacent = [pos[0]+a-1, pos[1]+b-1]
                                difference += abs(self.raw[adjacent[0]][adjacent[1]][0] - self.raw[pos[0]][pos[1]][0])
        average /= len(corners)*(self.sampleWidth**2)# / by total number of pixels sampled
        difference /= len(corners)*(self.sampleWidth**2)*8#* 8 because includes all adjacent pixels
        return average, difference

    def check_adjacent(self, image, coordinate, checkValue, markValue):
        #Checks all adjacent pixels to given pixel, returns all with value below checkValue
        check = self.get_adjacent(coordinate)
        checked = []#List that stores all pixels with value below checkValue
        for pos in check:
            try:
                if image[pos[0]][pos[1]] < checkValue:
                    checked.append(pos)#If pixel value below checkValue add to checked
                    image[pos[0]][pos[1]] = markValue#Mark as already visited
            except IndexError:
                pass
        return image, checked

    def calc_thresholds(self):
        #Calculates the threshold values
        average, difference = self.background_check()#Get average, difference
        resultDiff = [(E[0] * difference) + E[1]  for E in self.equationDiff]#Calc thresholds by difference
        resultAvg = [(E[0] * average) + E[1]  for E in self.equationAvg]#Calc thresholds by average
        average = [(resultDiff[r] + resultAvg[r]) / 2  for r in range(len(resultDiff))]#Average thesholds
        self.threshold1 = average[0]
        self.threshold2 = average[1]
        if self.threshold1 < 0:
            self.threshold = 0
        if self.threshold2 < self.threshold1:
            self.threshold2 = self.threshold1

    def create_objects(self):
        #Creates a list of particle objects from 1 image and progress bar
        #Tkinter setup
        root = tk.Tk()
        tk.Label(root, text="Analysis in progress", justify="center", font=("Calibri", 20)).pack()
        loader = tk.ttk.Progressbar(root, length=300)
        loader.pack(padx=10, pady=10)
        root.update()
        self.load(root, loader, 0)
        #Analysis
        self.calc_thresholds()
        self.load(root, loader, 10.3)
        centres = self.find_objects(self.processed1, self.threshold1, [root, loader])
        starts = [C[0] for C in centres]#Contains a single pixel from the centre of each object
        starts.append(None)#Used to terminate the while loop in find_objects
        coordinates = self.find_objects(self.processed2, self.threshold2, None, starts)
        coordinates = self.fill_gaps(coordinates)
        duplicates = []
        for c, C in enumerate(coordinates):#For each particle
            for d, D in enumerate(coordinates[c+1:]):#Check each particle after
                if D[0] in C:#If they overlap at all
                    duplicates.append(d+c+1)#Mark as duplicate
        coordinates = [C  for c, C in enumerate(coordinates)  if not c in duplicates]
        self.draw(coordinates)
        particles = [particle(C, [[Y[0] for Y in X] for X in self.raw], self.threshold2) for C in coordinates]
        self.load(root, loader, 100)
        root.destroy()
        return particles

    def draw(self, coordinates):
        #Creates an image given a list
        img = [[0 for y in range(len(self.raw[0]))] for x in range(len(self.raw))]
        for c, C in enumerate(coordinates):
            for D in C:
                img[D[0]][D[1]] = 1
        matImg.imsave(self.outputDir+"\\"+self.fileName[self.fileName.rindex('/')+1:self.fileName.rindex('.')]+"-analysed.png", img)

    def fill_gaps(self, coordinates):
        #Fills blank in pixels bordering at least 3 coloured pixels
        for s, shape in enumerate(coordinates):
            for pos in shape:
                adjacent = self.get_adjacent(pos)#All adjacent coordinates
                for A in adjacent:
                    if not A in shape:#If pixel is blank
                        adjacent2 = self.get_adjacent(A)#Get all adjacent pixels
                        total = 0
                        for A2 in adjacent2:
                            if A2 in shape:#If pixel is filled
                                total += 1#Add total
                        if total >= 3:#If blank borders 3+ filleds, record position
                            coordinates[s].append(A)
        return coordinates

    def find_objects(self, image, threshold, loadBar, startPos=None):
        #Finds all pixels in objects in an image, seperated in to sub lists by object
        if loadBar != None:
            barCount = 1
        if startPos == None:
            startPos = [self.find_start(image, threshold)]
        startIndex = 0
        coordinates = []
        while startPos[startIndex] != None:#Repeat until all pixels recorded
            if loadBar != None:
                if startPos[startIndex][0] > (len(image)*barCount)//14:
                    self.load(loadBar[0], loadBar[1], 10.3+(5.5*barCount))
                    barCount += 1
            coordinates.append([startPos[startIndex]])#Create sublist for coordinates of specific object
            image[startPos[startIndex][0]][startPos[startIndex][1]] = 2#Set initial coordinate to 2
            image, checked = self.check_adjacent(image, startPos[startIndex], threshold, 2)
            for C in checked:
                coordinates[-1].append(C[:])
            start = [0, len(coordinates[-1])]#Contains start of new set of coordinates and set after that
            checked = []
            done = False
            while not done:
                for pos in coordinates[-1][start[0]:]:#Loop through all coordinates in new set of results
                    image, checked = self.check_adjacent(image, pos, threshold, 2)
                    for pos in checked:
                        coordinates[-1].append(pos[:])#Add new coordinates to coordinates sub list
                done = len(coordinates[-1]) == start[1]
                start[0] = start[1]
                start[1] = len(coordinates[-1])#Reset start to fit next set
            if (len(startPos)-1 == startIndex):
                startPos.append(self.find_start(image, threshold))#Setup for next object
            startIndex += 1
        return coordinates

    def find_start(self, image, threshold):
        #Finds the first coloured pixel in an image
        for y in range(len(image)):
            for x in range(len(image[y])):
                if image[y][x] < threshold:
                    return [y, x]

    def get_adjacent(self, coordinate):
        #Returns the position of all adjacent pixels to a given pixel
        check = [coordinate[:] for x in range(4)]#List of coordinates to check before being set to correct values
        index = 0#Index of check being edited
        for plane in range(2):
            for mod in range(2):
                mod = (2*mod)-1#Mod = changes values 0,1 in to -1,1
                check[index][plane] += mod
                index += 1
        return check

    def load(self, root, bar, value):
        #Updates progress bar
        bar["value"] = value
        root.update_idletasks()


class GUI():
    def __init__(self, tempDir):
        self.tempDir = tempDir
        self.done = False
        self.bg = "#f0f0f0"
        self.btnCol = "light grey"
        self.files = []
        self.scales = [1  for x in range(10)]
        self.empty = [True  for x in range(10)]
        self.data = [0  for x in range(10)]
        self.figures = [0  for x in range(10)]
        self.views = [-1  for x in range(10)]
        self.addresses = [0  for x in range(10)]
        self.resultTypes = [0  for x in range(10)]
        self.current = 0

    def main_menu(self):
        #Displays the main menu page
        #========== Setup
        root = tk.Tk()
        root.configure(bg=self.bg)
        root.state("zoomed")
        h = root.winfo_screenheight()
        #========== Weighting
        root.rowconfigure(1, weight=1)
        root.rowconfigure(3, weight=1)
        root.rowconfigure(5, weight=1)
        root.rowconfigure(7, weight=1)
        root.rowconfigure(9, weight=1)
        root.columnconfigure(0, weight=1)
        #========== Widgets
        #===== Row 0, 1, 2
        tk.Frame(root, bg=self.bg, height=round(h*0.1)).grid(row=0, column=0)
        tk.Label(root, bg=self.bg, text="Microscope image analyser", justify="center", font=("Arial", round(h*0.06))).grid(row=1, column=0)
        tk.Frame(root, bg=self.bg, height=round(h*0.1)).grid(row=2, column=0)
        #===== Row 3, 4
        tk.Button(root, bg=self.btnCol, text="Image analysis", justify="center", font=("Calibri", round(h*0.03)), width=30, command=partial(self.select_file,root,"Select image to analyse",("Png files","*.png"),0)). grid(row=3, column=0)
        tk.Frame(root, bg=self.bg).grid(row=4, column=0)
        #===== Row 5, 6
        tk.Button(root, bg=self.btnCol, text="Load saved data", justify="center", font=("Calibri", round(h*0.03)), width=30, command=partial(self.select_file,root,"Select results file",("Text files","*.txt"),1)).grid(row=5, column=0)
        tk.Frame(root, bg=self.bg).grid(row=6, column=0)
        #===== Row 7, 8
        tk.Button(root, bg=self.btnCol, text="View results", justify="center", font=("Calibri", round(h*0.03)), width=30, command=lambda:[root.destroy(),self.results()]).grid(row=7, column=0)
        tk.Frame(root, bg=self.bg).grid(row=8, column=0)
        #===== Row 9
        tk.Button(root, bg=self.btnCol, text="Quit", justify="center", font=("Calibri", round(h*0.03)), width=30, command=root.destroy).grid(row=9, column=0)
        #===== Row 10
        tk.Frame(root, height=round(h*0.2)).grid(row=10, column=0)
        #========== Mainloop
        root.mainloop()

    def plot_histogram(self):
        #Creates a figure containing a histogram
        fig = Figure()
        fig.patch.set_facecolor(self.bg)
        plot = fig.gca()#Creates plot for histogram to be on
        plot.hist(self.data[self.current], 30)#Plot histogram with 30 bins
        plot.yaxis.set_major_locator(MaxNLocator(integer=True))#Make ticks integers
        plot.set_xlabel("Diameter", fontsize=20)#Set label size
        plot.set_ylabel("Frequency", fontsize=20)
        plot.tick_params(labelsize=15)#Set tick label size
        self.figures[self.current] = fig#Record new figure

    def remove_entry(self, index, refresh, root=None):
        #Removes an item from the stored results, given the index
        def remove(array, index):
            #Removes 1 item from a list given its index
            return [array[x]  for x in range(len(array))  if x != index]
        self.files = remove(self.files, index)
        self.scales = remove(self.scales, index)
        self.scales.append(1)
        self.empty = remove(self.empty, index)
        self.empty.append(True)
        self.data = remove(self.data, index)
        self.data.append(0)
        self.figures = remove(self.figures, index)
        self.figures.append(0)
        self.views = remove(self.views, index)
        self.views.append(-1)
        self.addresses = remove(self.addresses, index)
        self.addresses.append(0)
        self.resultTypes = remove(self.resultTypes, index)
        self.resultTypes.append(0)
        if refresh:
            if self.current > index:
                self.current -= 1
            if self.current>=len(self.files) and len(self.files)>0:
                self.current = len(self.files)-1
            root.destroy()
            self.results()

    def results(self):
        #Displays analysis results page
        #========== Setup
        root = tk.Tk()
        root.configure(bg=self.bg)
        root.state("zoomed")
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        #========== Weighting / padding
        root.rowconfigure(0, pad=h*0.05)
        root.rowconfigure(12, pad=h*0.05)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)
        root.columnconfigure(3, weight=1)
        root.columnconfigure(4, weight=1)
        #========== Widgets
        #===== Row 0
        tk.Button(root, bg=self.btnCol, text="Main menu", justify="center", font=("Calibri", round(h*0.02)), command=lambda:[root.destroy(),self.main_menu()]).grid(row=0, column=0, sticky="NW")
        self.resultsTitle = tk.StringVar()
        tk.Label(root, bg=self.bg, textvariable=self.resultsTitle, justify="center", font=("Arial", round(h*0.04))).grid(row=0, column=0, columnspan=6)
        #===== Other results
        tk.Label(root, bg=self.bg, text="Other results:", justify="left", font=("Calibri", round(h*0.03))).grid(row=1, column=5)
        self.others = []
        for x in range(10):
            try:
                self.others.append(tk.Button(root, bg=self.btnCol, text=self.files[x], justify="left", font=("Calibri", round(h*0.02)), width=20, command=partial(self.set_results, x, root)))
            except IndexError:
                self.others.append(tk.Button(root, bg=self.btnCol, text="", justify="left", font=("Calibri", round(h*0.02)), width=20, command=partial(self.set_results, x, root)))
            self.others[x].grid(row=x+2, column=5)
            tk.Button(root, bg=self.btnCol, text="X", justify="center", font=("Arial", round(h*0.02)), width=2, command=partial(self.remove_entry,x,True,root)).grid(row=x+2, column=6)
        #===== Row 12
        tk.Label(root, bg=self.bg, text="Scale:", font=("Calibri", round(h*0.03))).grid(row=12, column=0, sticky="E")
        root.bind("<Return>", partial(self.update_scale, root))
        self.scaleEntry = tk.StringVar()
        tk.Entry(root, textvariable=self.scaleEntry, font=("Calibri", round(h*0.03)), width=10).grid(row=12, column=1, sticky="W")
        tk.Button(root, bg=self.btnCol, text="Original image", width=15, font=("Calibri", round(h*0.03)), command=partial(self.set_view,root,1)).grid(row=12, column=2)
        tk.Button(root, bg=self.btnCol, text="Analysed image", width=15, font=("Calibri", round(h*0.03)), command=partial(self.set_view,root,2)).grid(row=12, column=3)
        tk.Button(root, bg=self.btnCol, text="Histogram", width=15, font=("Calibri", round(h*0.03)), command=partial(self.set_view,root,0)).grid(row=12, column=4)
        tk.Button(root, bg=self.btnCol, text="Save", width=10, font=("Calibri", round(h*0.03)), command=self.save).grid(row=12, column=5)
        self.set_results(self.current, root)
        self.set_view(root, 0)
        root.mainloop()

    def save(self):
        #Writes the scale adjusted diameters to txt file in csv format
        name = self.files[self.current]#Get shorter identifier
        name = name[:name.rindex(".")]+"-results.txt"
        address = filedialog.asksaveasfilename(title="Save results file", initialfile=name, filetype=(("Text files","*.txt"),("All files","*.*")))
        file = open(address, "w+")
        file.write(','.join([str(X)  for X in self.data[self.current]]))
        file.close()#Store diameters including scale adjustment, fstring used so it is 1 argument

    def select_file(self, root, title, filetype, resultType):
        #Allows the user to select an image file from a directory
        file = filedialog.askopenfilename(title=title, filetypes=(filetype,("All files","*.*")))
        if file != "":#If operation not cancelled
            self.files.append(file[file.rindex("/")+1:])#Get filename only
            if len(self.files) > 10:#If list full, replace oldest item
                self.remove_entry(0, False)
                self.current = 9
            self.current = len(self.files)-1
            self.addresses[self.current] = file
            self.resultTypes[self.current] = resultType
            root.destroy()
            if resultType == 0:#Image analysis
                pic = image(file, self.tempDir)#Do overall analysis
                particles = pic.create_objects()#Do particle analysis
                self.data[self.current] = [P.diameter  for P in particles]
            elif resultType == 1:#Reading results file
                text = open(file, "r").read()
                self.data[self.current] = text.split(",")
                self.data[self.current] = [float(X)  for X in self.data[self.current]]
            self.plot_histogram()#Create histogram figure
            self.results()

    def set_results(self, new, root):
        #Changes to a new set of analysis results
        if len(self.files) > new:#If results exist
            self.others[self.current].config(relief="raised")#Deselect previous
            self.current = new
            self.others[self.current].config(relief="sunken")#select current
            self.resultsTitle.set(f"Results - {self.files[self.current]}")#Change title
            if self.empty[self.current]:
                self.scaleEntry.set("")#If no scale set don't display scale
            else:
                self.scaleEntry.set(str(float(self.scales[self.current] * 127)))#Else do display scale
            self.set_view(root)

    def set_view(self, root, view=None):
        #Changes to viewing histogram, original image, or analysed image
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        if self.views[self.current] == 0:
            try:
                self.histogram.destroy()#Destroy histogram
            except Exception:
                pass
        elif self.views[self.current]==1 or self.views[self.current]==2:#If previous was image
            try:
                self.picWidget.destroy()#Destroy image
            except Exception:
                pass
        if view != None:
            self.views[self.current] = view#Update to new view
        if self.views[self.current] == 0:
            self.histogram = FigureCanvasTkAgg(self.figures[self.current], master=root).get_tk_widget()#Get widget
            self.histogram.config(width=round(w*0.75), height=round(h*0.7))#Resize cavas
            self.histogram.grid(row=1, column=0, rowspan=11, columnspan=5)#Place canvas
        elif self.views[self.current]==1 or self.views[self.current]==2:
            if self.resultTypes[self.current] == 0:
                if self.views[self.current] == 1:
                    file = self.addresses[self.current]#Get shorter version of file name
                    pic = ImageTk.PhotoImage(Image.open(file))#Get original image
                else:
                    file = self.files[self.current]
                    file = self.tempDir+"\\"+file[:file.rindex('.')]+"-analysed"+file[file.rindex('.'):]
                    pic = ImageTk.PhotoImage(Image.open(file))#Get analysed image
                self.picWidget = tk.Label(root, image=pic, width=round(w*0.75), height=round(h*0.7))#Image label
                self.picWidget.image = pic#Stops the image being discarded by memory manager
                self.picWidget.grid(row=1, column=0, rowspan=11, columnspan=5)
            else:
                self.views[self.current] = 0
                self.set_view(root, 0)

    def update_scale(self, root, key):
        #Records the scale if it is valid
        old = self.scales[self.current]
        try:
            self.scales[self.current] = float(self.scaleEntry.get()) / 127#Get scale
            if self.scales[self.current] > 0:
                for x in range(len(self.data[self.current])):#Adjust each item to new scale
                    self.data[self.current][x] *= self.scales[self.current] / old
                self.plot_histogram()#Replot histogram
                self.empty[self.current] = False#Record that scale has been set
                self.set_results(self.current, root)#Redraw canvas
            else:
                self.scales[self.current] = old
        except ValueError:
            pass#Unless not valid



def delete(directory):
    #Deletes a directory and contents given directory path
    contents = listdir(directory)#Get contents
    for C in contents:
        remove(f"{directory}\\{C}")#Delete all contents
    rmdir(directory)#Delete directory



directory = getcwd()+"\\Image-analysis-temporary"
mkdir(directory)
gui = GUI(directory)
gui.main_menu()
delete(directory)
