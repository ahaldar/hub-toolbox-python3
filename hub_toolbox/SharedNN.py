#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of the HUB TOOLBOX available at
http://ofai.at/research/impml/projects/hubology.html
Source code is available at
https://github.com/OFAI/hub-toolbox-python3/
The HUB TOOLBOX is licensed under the terms of the GNU GPLv3.

(c) 2011-2016, Dominik Schnitzer and Roman Feldbauer
Austrian Research Institute for Artificial Intelligence (OFAI)
Contact: <roman.feldbauer@ofai.at>
"""

import sys
import numpy as np
from hub_toolbox import IO

def snn_sample(D:np.ndarray, k:int=10, metric='distance', 
               train_ind:np.ndarray=None, test_ind:np.ndarray=None):
    """Transform distance matrix using shared nearest neighbors [1]_.
    
    __DRAFT_VERSION__
    
    SNN similarity is based on computing the overlap between the `k` nearest 
    neighbors of two objects. SNN approaches try to symmetrize nearest neighbor 
    relations using only rank and not distance information [2]_.
    
    Parameters
    ----------
    D : np.ndarray
        The ``n x n`` symmetric distance (similarity) matrix.
        
    k : int, optional (default: 10)
        Neighborhood radius: The `k` nearest neighbors are used to calculate SNN.
        
    metric : {'distance', 'similarity'}, optional (default: 'distance')
        Define, whether the matrix `D` is a distance or similarity matrix

    train_ind : ndarray, optional
        If given, use only these data points as neighbors for rescaling.

    test_ind : ndarray, optional (default: None)
        Define data points to be hold out as part of a test set. Can be:
        
        - None : Rescale all distances
        - ndarray : Hold out points indexed in this array as test set. 

    Returns
    -------
    D_snn : ndarray
        Secondary distance SNN matrix

    References
    ---------- 
    .. [1] R. Jarvis and E. A. Patrick, “Clustering using a similarity measure 
           based on shared near neighbors,” IEEE Transactions on Computers, 
           vol. 22, pp. 1025–1034, 1973.

    .. [2] Flexer, A., & Schnitzer, D. (2013). Can Shared Nearest Neighbors 
           Reduce Hubness in High-Dimensional Spaces? 2013 IEEE 13th 
           International Conference on Data Mining Workshops, 460–467. 
           http://doi.org/10.1109/ICDMW.2013.101
    """
    IO._check_sample_shape_fits(D, train_ind)
    IO._check_valid_metric_parameter(metric)
    if metric == 'distance':
        self_value = 0.
        sort_order = 1
        exclude = np.inf
    if metric == 'similarity':
        self_value = 1.
        sort_order = -1
        exclude = -np.inf
    distance = D.copy()
    n = distance.shape[0]
    if test_ind is None:
        n_ind = range(n)    
    else:
        n_ind = test_ind
    # Exclude self distances
    for j, sample in enumerate(train_ind):
        distance[sample, j] = exclude

    knn = np.zeros_like(distance, bool)
    
    # find nearest neighbors for each point
    for i in range(n):
        di = distance[i, :]
        nn = np.argsort(di)[::sort_order]
        knn[i, nn[0:k]] = True
    
    D_snn = np.zeros_like(distance)
    for i in n_ind:
        knn_i = knn[i, :]
        
        # using broadcasting
        Dij = np.sum(np.logical_and(knn_i, knn[train_ind, :]), 1)
        if metric == 'distance':
            D_snn[i, :] = 1. - Dij / k
        else: # metric == 'similarity':
            D_snn[i, :] = Dij / k

    # Ensure correct self distances and return sec. dist. matrix
    if test_ind is None:
        np.fill_diagonal(D_snn, self_value)
        return D_snn
    else:
        for j, sample in enumerate(train_ind):
            D_snn[sample, j] = self_value
        return D_snn[test_ind]


def shared_nearest_neighbors(D:np.ndarray, k:int=10, metric='distance'):
    """Transform distance matrix using shared nearest neighbors [1]_.
    
    SNN similarity is based on computing the overlap between the `k` nearest 
    neighbors of two objects. SNN approaches try to symmetrize nearest neighbor 
    relations using only rank and not distance information [2]_.
    
    Parameters
    ----------
    D : np.ndarray
        The ``n x n`` symmetric distance (similarity) matrix.
        
    k : int, optional (default: 10)
        Neighborhood radius: The `k` nearest neighbors are used to calculate SNN.
        
    metric : {'distance', 'similarity'}, optional (default: 'distance')
        Define, whether the matrix `D` is a distance or similarity matrix

    Returns
    -------
    D_snn : ndarray
        Secondary distance SNN matrix
        
    References
    ---------- 
    .. [1] R. Jarvis and E. A. Patrick, “Clustering using a similarity measure 
           based on shared near neighbors,” IEEE Transactions on Computers, 
           vol. 22, pp. 1025–1034, 1973.
    
    .. [2] Flexer, A., & Schnitzer, D. (2013). Can Shared Nearest Neighbors 
           Reduce Hubness in High-Dimensional Spaces? 2013 IEEE 13th 
           International Conference on Data Mining Workshops, 460–467. 
           http://doi.org/10.1109/ICDMW.2013.101
    """
    IO._check_distance_matrix_shape(D)
    IO._check_valid_metric_parameter(metric)
    if metric == 'distance':
        self_value = 0.
        sort_order = 1
        exclude = np.inf
    if metric == 'similarity':
        self_value = 1.
        sort_order = -1
        exclude = -np.inf
    
    distance = D.copy()
    np.fill_diagonal(distance, exclude)
    n = np.shape(distance)[0]
    knn = np.zeros_like(distance, bool)
    
    # find nearest neighbors for each point
    for i in range(n):
        di = distance[i, :]
        nn = np.argsort(di)[::sort_order]
        knn[i, nn[0:k]] = True
    
    D_snn = np.zeros_like(distance)
    for i in range(n):
        knn_i = knn[i, :]
        j_idx = slice(i+1, n)
        
        # using broadcasting
        Dij = np.sum(np.logical_and(knn_i, knn[j_idx, :]), 1)
        if metric == 'distance':
            D_snn[i, j_idx] = 1. - Dij / k
        else: # metric == 'similarity':
            D_snn[i, j_idx] = Dij / k
        
    D_snn += D_snn.T
    np.fill_diagonal(D_snn, self_value)
    return D_snn

class SharedNN(): # pragma: no cover
    """
    .. note:: Deprecated in hub-toolbox 2.3
              Class will be removed in hub-toolbox 3.0.
              Please use static functions instead.
    """
    def __init__(self, D, k=10, isSimilarityMatrix=False):
        """
        .. note:: Deprecated in hub-toolbox 2.3
                  Class will be removed in hub-toolbox 3.0.
                  Please use static functions instead.
        """
        print("DEPRECATED: Please use SharedNN.shared_nearest_neighbors() "
              "instead.", file=sys.stderr)
        self.D = np.copy(D)
        self.k = k
        if isSimilarityMatrix:
            self.sort_order = -1
        else:
            self.sort_order = 1
        
    def perform_snn(self):
        """Transform distance matrix using shared nearest neighbor.

        .. note:: Deprecated in hub-toolbox 2.3
                  Class will be removed in hub-toolbox 3.0.
                  Please use static functions instead.
        """
        if self.sort_order == -1:
            metric = 'similarity'
        else:
            metric = 'distance'
        return shared_nearest_neighbors(self.D, self.k, metric)
