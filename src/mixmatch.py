"""
File: mixmatch
Description: Contains functions for mixmatch
Author Lawrence Stewart <lawrence.stewart@ens.fr>
License: Mit License 
"""

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import pandas as pd
from ot.ot1d import *
from src.mixup import *
from sklearn.utils import shuffle



def generate_noise(X,stddev=0.01):
	"""
	Generates noise from a 0 centered normal 
	with stddev as an input parameter with shape
	equal to the shape of X

	Parameters
	--------
	X : array (n,m)
	stddev : float

	Output
	-------
	noise : array (n,m)
	"""
	noise = np.random.normal(size=X.shape, scale=stddev)
	return noise


def noisy_augment(X,stddev=0.01,K=10):
	"""
	Creates a list of K noisy augmentations of 
	data X using the generate_noise function

	Parameters
	----------
	X : array (n,m)
	stddev : float 
	K : int

	Output
	--------
	augs : list of size k (containing size (n,m) arrays)
	"""
	augs = [X+generate_noise(X,stddev=stddev) for i in range(K)]
	return augs



def mixmatch_ot1d(model,X,Y,U,
	stddev=0.01,alpha=0.75,K=3,naug=5):

	"""
	Computes to OT formulation of Mixmatch
	for two batches (X,Y) [labelled data] and
	(U,) [unlabelled data].

	Parameters
	----------
	model : f() -> tf.tensor (n,1) 
	X : array (n,m) labelled data
	Y : array (n,1)	data labels	
	U : array (n,m) unlabelled data
	stddev : float (for noise augmentations)
	alpha : float (for mixup beta dist)
	K : int (size of barycentre)
	naug : int (number of augmentations)


	Output
	-------
	Xprime : array (n,m) 
	Yprime : array (n,K)
	Uprime : array (n,m)
	Qprime : array (n,K)

	"""
	
	#generate noisy augmentations of X
	Xhat = X + generate_noise(X,stddev=stddev)

	#generate K noisy augmentations of U 
	Uaugs = noisy_augment(U,stddev=stddev,K=naug)
	Uhat = Uaugs[-1]

	#predict labels and convert to numpy arrays
	modeln = lambda x : model(x).numpy()
	preds = list(map(modeln,Uaugs))

	#labels for unlabelled data
	Q = np.concatenate(preds,axis=1)
	#sort labels into increasing order for barycentre calcs
	Q.sort(axis=1)

	#mix of data X and U
	W = np.concatenate((Xhat,Uhat),axis=0)

	#mix of labels for X and U 
	Wlabels = Y.tolist()+Q.tolist()
	Wlabels = np.array(Wlabels)

	#shuffle W and its labels together
	W,Wlabels = shuffle(W,Wlabels)

	l = len(W)//2

	#mixup Xhat and W
	Xprime,Yprime = mixup_ot1d(Xhat,W[:l],
		Y,Wlabels[:l],alpha=alpha,K=K)
	#mixup Uhat and W 
	Uprime,Qprime = mixup_ot1d(Uhat,W[l:],
		Q,Wlabels[l:],alpha=alpha,K=K)

	#return labelled and unlabelled batches
	return Xprime,Yprime,Uprime,Qprime


