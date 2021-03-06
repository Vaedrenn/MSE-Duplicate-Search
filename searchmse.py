import os
import pickle

import numpy as np
import cv2
import imghdr
from tcontainer import tcontainer


# creates a list of tensors for a given directory
def create_tensor_list(root, px_size=50):
    tensor_list = []
    # create list of all files in directory
    folder_files = [os.path.join(root, f) for root, dirs, files in os.walk(root) for f in files]
    for file in folder_files:
        # only process images don't process gifs
        if imghdr.what(file) and not imghdr.what(file) == "gif" and not imghdr.what(file) == "psd":
            tensor = create_tensor(file)
            tensor_list.append(tensor)
    return tensor_list


# read the image data and convert it into a tensor
def create_tensor(file):
    # Open the image as a color image to prevent errors caused by grayscale images
    tensor = cv2.imdecode(np.fromfile(file, dtype=np.uint8), cv2.IMREAD_COLOR)
    if type(tensor) == np.ndarray:
        #  check if it has been successfully converted to a numpy n-dimensional array, and has 3 layers at maximum.
        tensor = tensor[..., 0:3]
        # resize the image to speed up comparisons
        tensor = cv2.resize(tensor, dsize=(50, 50), interpolation=cv2.INTER_CUBIC)

    ret = tcontainer(file, tensor)
    return ret


# Function that calulates the mean squared error (mse) between two image matrices
def mse(first, second):
    tensor1 = first.tensor
    tensor2 = second.tensor

    try:
        err = np.sum((tensor1.astype("float") - tensor2.astype("float")) ** 2)
        err /= float(tensor1.shape[0] * tensor1.shape[1])

        return err
    # Still want the program to continue, don't count the images as dupes and continue
    except ValueError:
        print("Value Error: ", first.path, second.path)
        return 1000000
    except AttributeError:
        print("Attribute Error: ", first.path, second.path)
        return 1000000


# # Searches for duplicates and removes them from the array when found, should speed up program in theory
# arr: array of tcontainer objects
# threshold: the threshold at which the MSE is less than that we consider two images as duplicates.
#            When two images are completely different the MSE is usually over 1000 or so.
#            Visually similar images such as edited images range from 50-100
# dupe_matrix:  returns something like this where each array is a set of duplicate images
#               [[tcontainer, tcontainer, tcontainer],
#                [tcontainer, tcontainer, tcontainer],
#                [tcontainer, tcontainer, tcontainer]]
# tcontainer: has a file path and a ndarray: self.path, self.tensor
def mse_search(arr, threshold=20):
    dupe_matrix = []
    while len(arr) > 0:
        # reset i and dupes arr before each cycle, ignore the squiggly line
        i = 1
        dupes = []

        dupes.append(arr[0])
        # go through the tensors and find the mse
        while len(arr) >= 2 and i < len(arr):
            ratio = mse(arr[0], arr[i])
            # if the mse is less than the threshold add it to the bundle of dupes for this image
            if ratio < threshold:
                dupes.append(arr.pop(i))
                i = i - 1

            i = i + 1

        # If dupes has more than one object then put it into the return matrix
        if len(dupes) >= 2:
            dupe_matrix.append(dupes)
        arr.pop(0)

    return dupe_matrix


# searches duplicates from folder 1 in folder 2
def mse_search_two(src, dst, threshold=20):
    dupe_matrix = []
    while len(src) > 0:
        dupes = []
        dupes.append(src[0])

        for dst_img in dst:
            ratio = mse(dst_img, src[0])

            if ratio < threshold:
                dupes.append(dst_img)
                break  # Assume all images in folder2 are unique

        if len(dupes) >= 2:
            dupe_matrix.append(dupes)
        src.pop(0)

    return dupe_matrix


# Exports the tlist into a pickle file to be reused later. Like a cache or something
def export_tensors(tlist, filename="tensors.pickle"):
    file = open(filename, "wb")
    pickle.dump(tlist, file)
    file.close()
    return True


# Imports the pickle file to be used.
def import_tensors(path=r"tensors.pickle"):
    file = open(path, "rb")
    ret = pickle.load(file)
    file.close()
    return ret
