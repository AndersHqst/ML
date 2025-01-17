import numpy as np
import scipy.io
import matplotlib.pyplot as plt
import cv2
import os
from eyeVideoLoader import EyeVideoLoader
import sys
from mpl_toolkits.mplot3d import Axes3D
import svm
from sklearn.metrics import classification_report
import time

class SliderHandler:

    def __init__(self, face, mean, variance, u, imageSize, maxK = 100, minValue = -70, maxValue = 70):
        self.face = face
        self.mean = mean
        self.variance = variance
        self.imageSize = imageSize
        self.maxK = maxK
        self.u = u
        self.minValue = minValue
        self.maxValue = maxValue

        cv2.namedWindow("Sliders", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Face")

        for i in range(maxK):
            cv2.createTrackbar(str(i), "Sliders", int(self.face[i]) - minValue, maxValue - minValue, self.updateFace)
        self.updateFace()

    def updateFace(self, dummy = None):
        for i in range(self.maxK):
            sliderValue = cv2.getTrackbarPos(str(i), "Sliders")
            self.face[i] = sliderValue + minValue

        recoveredFace = recoverData(self.face, self.u, maxK = self.maxK)
        recoveredFace = deNormalize(recoveredFace, self.mean, self.variance)
        cv2.normalize(recoveredFace, recoveredFace, 0, 255, cv2.NORM_MINMAX)
        recoveredFace = recoveredFace.astype('uint8').reshape(self.imageSize)#.transpose()

        recoveredFace = cv2.pyrUp(recoveredFace)
        cv2.imshow("Face", recoveredFace)


def loadData1():
    data = scipy.io.loadmat('ex7data1.mat')
    return data['X']


def loadFaceData():
    data = scipy.io.loadmat('ex7faces.mat')
    return data['X']



def featureNormalize(data, doScale = False):
    ''' Normalizes each feature (column) of the data to a mean value of 0 and a standard deviation of 1 '''
    return normalize(data, axis = 0, doScale = doScale)


def sampleNormalize(data):
    return normalize(data, axis = 1)


# We do not need to divide by the standard deviation. This is done for the sake
# of feature scaling, and is only relevant when varibles in our data are 'different'
# For images, all variables have the same scale.
# Andrew Ng explains it here: http://www.youtube.com/watch?v=ey2PE5xi9-A?t=43m
def normalize(data, axis, doScale):
    mean = np.mean(data, axis = axis) #.reshape(-1, 1)
    normalized = data - mean
    if doScale:
        variance = np.std(normalized, axis = axis) #.reshape(-1, 1)
        normalized = normalized / variance
    else:
        variance = 1
    return normalized, mean, variance


def deNormalize(normalizedData, mean, variance):
    return normalizedData * variance + mean


def getCovarianceMatrix(normalizedData):
    ''' Returns a covariance matrix, defined as (1/m)* xT * x (1 over m times x transposed x)
        where x has a row per sample and m is the number of samples '''
    m = normalizedData.shape[0]
    transposed = np.transpose(normalizedData)
    return transposed.dot(normalizedData) / m

def kDimensionWithVaraianceRetained(data, variance):
    '''Return the minimum k dimensions needed for retaining variance
    :param variance: eg 0.99 for 99% variance retained
    :param data: data
    '''
    k = 1
    vars = []
    normalized, mean, var = featureNormalize(data)
    covMat = getCovarianceMatrix(normalized)
    (u, s, v) = np.linalg.svd(covMat)
    while k < len(data[0]):
        val = sum(s[:k]) / sum(s[:len(data)])
        vars.append(val)
        # print 'Variance calculated: %s With k: %s' % (val, k)
        if val >= variance:
            break
        k += 1
    plt.plot([x for x in range(len(vars))], vars, 'b-')    
    plt.xlabel('k')
    plt.ylabel('Variance retained')
    plt.show()
    return k


def plotOriginalData(data, u, s, v, mean):
    plt.hold('on')
    plt.plot(data[:,0], data[:,1], 'bo')
    
    p1, p2 = mean, 1.5 * s[0] * np.transpose(u[:,0]) # ved ikke lige hvad de 1.5 laver, antager det er for plottets skyld
    p3, p4 = mean, 1.5 * s[1] * np.transpose(u[:,1])
    plt.arrow(p1[0], p1[1], p2[0], p2[1])
    plt.arrow(p3[0], p3[1], p4[0], p4[1])
    
    plt.axis([0.5, 6.5, 2, 8])
    plt.show()
    plt.hold('off')


def projectData(normalizedData, u, maxK):
    u = u[:, 0:maxK]
    #In the Stanford video this is calculated as u transpose x (column vector).
    #The return below is equalivant because our data
    #has a feature per column, and not per row (row vectors).
    #Thus, to do the same as in the video, we would have to write
    #u transpose dot x transpose == x dot u
    return normalizedData.dot(u)


def recoverData(projectedData, u, maxK):
    u = np.transpose(u[:, 0:maxK])
    return projectedData.dot(u)


def plotRecoveredData(recovered, normalized):
    plt.hold('on')
    plt.plot(recovered[:, 0], recovered[:, 1], 'ro')
    diff = recovered - normalized
    for i in range(recovered.shape[0]):
        plt.arrow(normalized[i,0], normalized[i,1], diff[i,0], diff[i,1])
    
    plt.show()
    plt.hold('off')
    

def runPart1():
    ''' 2.3: 2D to 1D '''
    data = loadData1()
    (normalizedData, mean, variance) = featureNormalize(data)
    
    covarianceMatrix = getCovarianceMatrix(normalizedData)
    
    (u, s, v) = np.linalg.svd(covarianceMatrix) # numpy giver et s-array hvor kun diagonalerne fra S-matrixen beskrevet i kurset er med
    plotOriginalData(data, u, s, v, mean)
    
    projectedData = projectData(normalizedData, u, maxK = 1)
    recoveredData = recoverData(projectedData, u, maxK = 1)
    plotRecoveredData(recoveredData, normalizedData)
    

def show100Faces(faces, size):
    faces = np.copy(faces)

    plt.gray()
    display = None
    row = None
    index = 0
    for r in range(10):
        for c in range(10):
            face = faces[index].reshape(size) # .transpose()
            cv2.normalize(face, face, 0, 255, cv2.NORM_MINMAX)
            index += 1
            if (row is None):
                row = face
            else:
                row = np.concatenate((row, face), axis = 1)
        
        if display is None:
            display = row
        else:
            display = np.concatenate((display, row), axis = 0)
        row = None
        
    plt.imshow(display)
    plt.show()


def runPart2():
    ''' 2.4: Faces '''

    faces = loadFaceData()
    show100Faces(faces)

    (normalizedFaces, mean, variance) = featureNormalize(faces)
    covarianceMatrix = getCovarianceMatrix(normalizedFaces)
    (u, s, v) = np.linalg.svd(covarianceMatrix)
    show100Faces(u.transpose())

    projectedFaces = projectData(normalizedFaces, u, maxK = 100)
    recoveredFaces = recoverData(projectedFaces, u, maxK = 100)
    recoveredFaces = deNormalize(recoveredFaces, mean, variance)

    show100Faces(recoveredFaces)

    sliderFace = projectedFaces[0]
    sliderHandler = SliderHandler(sliderFace, mean, variance, u, (32,32), 100)

    while True:
        cv2.waitKey(10)


def plotProjectedData2D(data, targets = None):
    params = ('bo', 'ro', 'go', 'yo')

    if targets is None:
        plt.plot(data[:,0].flatten(),
                 data[:,1].flatten(), 
                 'bo')
    else:
        for target in range(4):
            ii = np.nonzero(targets == target + 1)[0]
            plt.plot(data[ii,0].flatten(),
                     data[ii,1].flatten(), 
                     params[target])
    plt.show()


def plotProjectedData3D(data, targets):
    params = ('bo', 'ro', 'go', 'yo')
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for target in range(4):
        ii = np.nonzero(targets == target + 1)[0]
        ax.plot(data[ii,0].flatten(),
                data[ii,1].flatten(),
                data[ii,2].flatten(),
                params[target])
    plt.show()


def stuffWeDidWithAllData(eyeData, targets):   

    #k = kDimensionWithVaraianceRetained(eyeData, 0.99)

    interval = int(eyeData.shape[0] / 100)
    #show100Faces(eyeData[::interval], (28,42))

    normalizedData, mean, variance = featureNormalize(eyeData, doScale = False) #sampleNormalize(eyeData) # 

    covarianceMatrix = getCovarianceMatrix(normalizedData)
    (u, s, v) = np.linalg.svd(covarianceMatrix)

    #show100Faces(u.transpose(), (28,42))


    k = 6
    projectedData = projectData(normalizedData, u, maxK = k)

    #plotProjectedData2D(projectedData, targets)

    recoveredData = recoverData(projectedData, u, maxK = k)
    recoveredData = deNormalize(recoveredData, mean, variance)

    #show100Faces(recoveredData[::interval], (28,42))

    sliderEye = projectedData[4000]

    projectedChanged = np.zeros((100, k), dtype = type(projectedData[0,0]))

    minValue = int(np.min(projectedData))
    maxValue = int(np.max(projectedData))

    values = range(minValue, maxValue, 414)

    for i in range(10):
        projectedChanged[i*10:i*10+10, 0] = values


    for i in range(10):
        projectedChanged[i::10, 1] = values


    recoveredData = recoverData(projectedChanged, u, maxK = k)
    recoveredData = deNormalize(recoveredData, mean, variance)

    show100Faces(recoveredData, (28,42))

    #plotProjectedData2D(projectedChanged)


    sliderHandler = SliderHandler(sliderEye, mean, variance, u, (28,42), maxK = k, minValue = minValue, maxValue = maxValue)

    while True:
        cv2.waitKey(10)


def validate(eyeData, people, targets, testPerson, k, C, gamma, kernel):
    trainingIndices = np.nonzero(people != testPerson)
    testIndices = np.nonzero(people == testPerson)
    
    trainingData = eyeData[trainingIndices]
    trainingTargets = targets[trainingIndices]
    testData = eyeData[testIndices]
    testTargets = targets[testIndices]
    
    # normalize training data, get mean
    (normalizedTraining, mean, variance) = featureNormalize(trainingData, doScale = False)
    
    # normalize test data with mean from above
    normalizedTest = testData - mean
    
    if k is None:
        projectedTraining = normalizedTraining
        projectedTest = normalizedTest
    else:
        # run PCA with some value of k to get (u,s,v) from training data
        covarianceMatrix = getCovarianceMatrix(normalizedTraining)
        (u, s, v) = np.linalg.svd(covarianceMatrix)
    
        # project training data & test data
        projectedTraining = projectData(normalizedTraining, u, k)
        projectedTest = projectData(normalizedTest, u, k)
    
    # learn through projected training data
    classifier = svm.classifier(projectedTraining, trainingTargets, C, gamma, kernel)
    
    # try to predict projected test data
    testResults = classifier.predict(projectedTest)
    

    # left/right classification
    #correct = np.sum((testTargets-1)/2 == (testResults-1)/2) / float(len(testResults))
    
    # classification among four directions
    correct = np.sum(testTargets == testResults) / float(len(testResults))

    #print classification_report(testTargets, testResults)

    return correct


def crossValidate(eyeData, people, targets, k = 2, C = 1, gamma = 1e-8, kernel = 'rbf'):
    results = []

    for testPerson in range(np.max(people)):
        correctFraction = validate(eyeData, people, targets, testPerson, k, C, gamma, kernel)
        results.append(correctFraction)
        
    return np.average(results)


def findBestParameters():
    i = 1
    print "round; k; C; gamma; kernel; prediction; time; support vectors"
    for k in [2, 3, 5, 14, 29, 131, 588, None]:
        for C in [1, 1e3, 1e5]:
            for gamma in [1e-1, 1e-3, 1e-5]:
                for kernel in ['rbf']:
                    if k is None and gamma == 1e-5:
                        continue
                    
                    start = time.clock()
                    correctFraction = crossValidate(eyeData, people, targets, k, C, gamma, kernel)
                    elapsed = (time.clock() - start)

                    supportVectors = countSupportVectors(eyeData, targets, k, C, gamma, kernel)

                    print i, ";", k, ";", C, ";", gamma, ";", kernel, ";", correctFraction, ";", elapsed, ";", supportVectors
                    i += 1


def plotDecisionBoundary(eyeData, targets, k, C, gamma, kernel): 
    
    (normalizedTraining, mean, variance) = featureNormalize(eyeData, doScale = False)
    covarianceMatrix = getCovarianceMatrix(normalizedTraining)
    (u, s, v) = np.linalg.svd(covarianceMatrix)
    projectedTraining = projectData(normalizedTraining, u, k)
    classifier = svm.classifier(projectedTraining, targets, C, gamma, kernel)
        
    minx = np.min(projectedTraining[:,0])
    maxx = np.max(projectedTraining[:,0])
    stepx = (maxx - minx) / 600.0
    xx = np.array(np.arange(minx, maxx, stepx))
    miny = np.min(projectedTraining[:,1])
    maxy = np.max(projectedTraining[:,1])
    stepy = (maxy - miny) / 400.0
    yy = np.array(np.arange(miny, maxy, stepy))
    
    results = np.zeros((len(xx), len(yy)))
    
    for i,x in enumerate(xx):
      for j,y in enumerate(yy):
        results[i, j] = classifier.predict(np.array([[x, y]]))[0]

    params = ('b,', 'r,', 'g,', 'y,')
    params2 = ('bo', 'ro', 'go', 'yo')
    plt.hold('on')

    for target in range(4):
        ii = np.nonzero(results == target + 1)
        plt.plot(xx[ii[0]].flatten(),
                 yy[ii[1]].flatten(), 
                 params[target])

    for target in range(4):
        ii2 = np.nonzero(targets == target + 1)[0]
        plt.plot(projectedTraining[ii2,0].flatten(),
                 projectedTraining[ii2,1].flatten(), 
                 params2[target])

    plt.show()







def plotSingleFeature(singleFeature, targets):
    data = []

    for target in [1,2,3,4]:
        ii = targets == target
        data.append(singleFeature[ii])


    plt.hist(data, 15, histtype = 'bar', color = ['blue', 'red', 'green', 'yellow'], label = ['direction 1', 'direction 2', 'direction 3', 'direction 4'])
    plt.legend()
    plt.xlabel('feature value')
    plt.ylabel('number of samples')

    plt.show()


def debugSingleFeature(eyeData, singleFeature, targets):
    index3 = np.nonzero(targets == 3)[0]
    index4 = np.nonzero(targets == 4)[0]

    direction3 = eyeData[index3]
    direction4 = eyeData[index4]

    feature3 = singleFeature[index3]
    feature4 = singleFeature[index4]

    worst3 = np.argmin(feature3)
    worst4 = np.argmax(feature4)

    image3 = direction3[worst3].reshape((28, 42))#.transpose()
    image4 = direction4[worst4].reshape((28, 42))#.transpose()

    image3 = cv2.pyrUp(image3)
    image4 = cv2.pyrUp(image4)

    cv2.namedWindow("singlefeature")

    cv2.imshow("singlefeature", image3)
    cv2.waitKey(0)
    cv2.imshow("singlefeature", image4)
    cv2.waitKey(0)


    
def countSupportVectors(eyeData, targets, k, C, gamma, kernel): 
    (normalizedTraining, mean, variance) = featureNormalize(eyeData, doScale = False)
    covarianceMatrix = getCovarianceMatrix(normalizedTraining)
    (u, s, v) = np.linalg.svd(covarianceMatrix)
    projectedTraining = projectData(normalizedTraining, u, k)
    classifier = svm.classifier(projectedTraining, targets, C, gamma, kernel)

    return classifier.support_vectors_.shape[0]

    #print "here"



loader = EyeVideoLoader()


#loader.showFeatureLocations([2095])

#loader.normalizeSampleImages()
#sys.exit()

# loader.resizeEyeVideos()

#(eyeData, targets, people) = loader.loadDataFromVideos()

#singleFeature = loader.loadSingleFeatureData()

#np.save('eyeData.npy', eyeData)
#np.save('targets.npy', targets)
#np.save('people.npy', people)
#np.save('singleFeature.npy', singleFeature)
eyeData = np.load('eyeData.npy')
targets = np.load('targets.npy')
people = np.load('people.npy')
singleFeature = np.load('singleFeature.npy')
eyeData = eyeData / 255.0


#runPart1()
#runPart2()
stuffWeDidWithAllData(eyeData, targets)
#findBestParameters()
#plotDecisionBoundary(eyeData, targets, k = 2, C = 1e9, gamma = 1e-5, kernel = 'rbf')

# plotSingleFeature(singleFeature, targets)


#debugSingleFeature(eyeData, singleFeature, targets)



# best parameters
#showSupportVectors(eyeData, targets, k = 131, C = 1000, gamma = 1e-3, kernel = 'rbf')

# best parameters for k = 2
#countSupportVectors(eyeData, targets, k = 2, C = 1, gamma = 1e-3, kernel = 'rbf')



print "Done!"
raw_input()
