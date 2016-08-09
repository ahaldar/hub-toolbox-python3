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

import numpy as np
from hub_toolbox.Hubness import hubness
from hub_toolbox.KnnClassification import score
from hub_toolbox.GoodmanKruskal import goodman_kruskal_index
from hub_toolbox.IntrinsicDim import intrinsic_dimension
from hub_toolbox.MutualProximity import MutualProximity, Distribution
from hub_toolbox.LocalScaling import nicdm
from hub_toolbox.SharedNN import shared_nearest_neighbors
from hub_toolbox.Centering import centering, weighted_centering, \
                                  localized_centering
from hub_toolbox.Distances import cosine_distance


class HubnessAnalysis():
    """
    The main hubness analysis class.
    
    Usage:
        hub = HubnessAnalysis()
        hub.analyse_hubness()
            - Load the example data set and perform a quick hubness analysis 
            with some of the functions provided in this toolbox.

        hub = HubnessAnalysis(D, classes, vectors)
        hub.analyse_hubness()
             - Use the distance matrix D (NxN) together with an optional 
             class labels vector (classes) and the original (optional) 
             data vectors (vectors) to perform a full hubness analysis.
    """
    
    def __init__(self, D:np.ndarray=None, classes:np.ndarray=None, 
                 vectors:np.ndarray=None):
        """Initialize a quick hubness analysis.
        
        Parameters:
        -----------
        D : ndarray, optional (default: None)
            The n x n symmetric distance (similarity) matrix.
            Default: load example dataset (dexter).
            
        classes : ndarray, optional (default: None)
            The 1 x n class labels. Required for k-NN, GK.
            
        vectors : ndarray, optional (default: None)
            The m x n vector data. Required for IntrDim estimation.
        """        
        
        self.haveClasses, self.haveVectors = False, False
        if D is None:
            self.D, self.classes, self.vectors = self.load_dexter()
            self.haveClasses, self.haveVectors = True, True
        else:
            # copy data and ensure correct type (not int16 etc.)
            self.D = np.copy(D).astype(np.float64)
           
            self.classes = np.copy(classes).astype(np.float64)
            self.vectors = np.copy(vectors).astype(np.float64)
            if classes is not None:
                self.haveClasses = True
            if vectors is not None:
                self.haveVectors = True
        self.n = len(self.D)
                
    def analyse_hubness(self, origData=True, mp=True, mp_gauss=False, 
                        mp_gaussi=True, mp_gammai=False, ls=True, snn=True, 
                        cent=True, wcent=False, wcent_g=0.4, 
                        lcent=True, lcent_k=40, lcent_g=1.4, Sk10=False):
        """Analyse hubness in original data and rescaled distances.
        
        Parameters:
        -----------
        args : bool
            - origData ... original data
            - mp ... Mutual Proximity (empiric)
            - mp_gauss ... Mutual Proximity (Gaussian)
            - mp_gaussi ... Mutual Proximity (independent Gaussian)
            - mp_gammai ... Mutual Proximity (independent Gamma)
            - ls ... Local Scaling (NICDM)
            - snn ... Shared Nearest Neighbors
            - cent ... Centering
            - wcent ... Weighted Centering
            - lcent ... Localized Centering
        args : float
            - wcent_g ... Weighted Centering gamma parameter
            - lcent_k ... Localized Centering kappa parameter
            - lcent_g ... Localized Centering gamma parameter
            
        Returns:
        --------
        None : print summary of results to stdout
        """
        
        print()
        print("Hubness Analysis")
            
        if not (origData or mp or mp_gauss or mp_gaussi or mp_gammai or \
                ls or snn or cent or wcent or lcent):
            print("---Nothing to do. Please specify tasks to be performed.---")
        if origData:
            Sn5, Nk5 = hubness(self.D)[::2]
            self.print_results('ORIGINAL DATA', self.D, Sn5, Nk5, True)
        if mp or mp_gaussi or mp_gammai or mp_gauss:
            mut_prox = MutualProximity(self.D)
            if mp:  
                # Hubness in empiric mutual proximity distance space
                Dn = mut_prox.calculate_mutual_proximity(Distribution.empiric)
                Sn5, Nk5 = hubness(Dn)[::2]
                self.print_results('MUTUAL PROXIMITY (Empiric/Slow)', \
                                   Dn, Sn5, Nk5)
            if mp_gauss:    
                # Hubness in mutual proximity distance space, Gaussian model
                Dn = mut_prox.calculate_mutual_proximity(Distribution.gauss)
                Sn5, Nk5 = hubness(Dn)[::2]
                self.print_results('MUTUAL PROXIMITY (Gaussian)', Dn, Sn5, Nk5)
            if mp_gaussi:
                # Hubness in mutual proximity distance space, independent Gaussians
                Dn = mut_prox.calculate_mutual_proximity(Distribution.gaussi)
                Sn5, Nk5 = hubness(Dn)[::2]
                self.print_results('MUTUAL PROXIMITY (Independent Gaussians)', \
                                   Dn, Sn5, Nk5)
            if mp_gammai:
                # Hubness in mutual proximity distance space, indep. Gamma distr.
                Dn = mut_prox.calculate_mutual_proximity(Distribution.gammai)
                Sn5, Nk5 = hubness(Dn)[::2]
                self.print_results('MUTUAL PROXIMITY (Independent Gamma)', \
                                   Dn, Sn5, Nk5)
        if ls:
            # Hubness in local scaling distance space
            radius = 10
            scalingType = 'nicdm' # 'original'
            Dn = nicdm(self.D, radius)
            Sn5, Nk5 = hubness(Dn)[::2]
            self.print_results('LOCAL SCALING ({}, k={})'.format(\
                scalingType, radius), Dn, Sn5, Nk5)
        if snn:
            # Hubness in shared nearest neighbors space
            Dn = shared_nearest_neighbors(self.D)
            Sn5, Nk5 = hubness(Dn)[::2]
            self.print_results('SHARED NEAREST NEIGHBORS (k={})'.format(\
                radius), Dn, Sn5, Nk5)
        if cent or wcent or lcent:
            if not self.haveVectors:
                print("Centering is currently only supported for vector data.")
            else:
                if cent:
                    # Hubness after centering
                    D_cent = cosine_distance(centering(self.vectors, 'vector'))
                    Sn5, Nk5 = hubness(D_cent)[::2]
                    self.print_results('CENTERING', D_cent, Sn5, Nk5)                    
                    # TODO remove again
                    if Sk10:
                        Sn10, Nk10 = hubness(D_cent, k=10)[::2]
                        self.print_results('CENTERING', D_cent, Sn10, Nk10, Sn10=True)
                    
                if wcent:        
                    # Hubness after weighted centering
                    D_wcent = cosine_distance(weighted_centering(
                                self.vectors, metric='cosine', gamma=wcent_g))
                    Sn5, Nk5 = hubness(D_wcent)[::2]
                    self.print_results('WEIGHTED CENTERING (gamma={})'.format(\
                                        wcent_g), D_wcent, Sn5, Nk5)

                    # TODO remove again
                    if Sk10:
                        Sn10, Nk10 = hubness(D_wcent, k=10)[::2]
                        self.print_results('WEIGHTED CENTERING (gamma={})'.format(\
                                        wcent_g), D_wcent, Sn10, Nk10, Sn10=True)
                if lcent:
                    # Hubness after localized centering
                    D_lcent = localized_centering(self.vectors, metric='cosine',
                                                  kappa=lcent_k, gamma=lcent_g)
                    Sn5, Nk5 = hubness(D_lcent)[::2]
                    self.print_results(\
                        'LOCALIZED CENTERING (k={}, gamma={})'.format(\
                        lcent_k, lcent_g), D_lcent, Sn5, Nk5)
    
    def print_results(self, heading:str, D:np.ndarray, Sn5:float, Nk5:float, 
                      calc_intrinsic_dimensionality:bool=True, Sn10=False):
        """Print the results of a hubness analysis."""     
        
        if Sn10:
            print('data set hubness (S^n=10)                : {:.3}'.format(Sn5)) 
            return
        
        print()
        print(heading + ':')
        print('data set hubness (S^n=5)                 : {:.3}'.format(Sn5))
        print('% of anti-hubs at k=5                    : {:.4}%'.format(\
            100 * sum(Nk5==0)/self.n))
        print('% of k=5-NN lists the largest hub occurs : {:.4}%'.format(\
            100 * max(Nk5)/self.n))
        if self.haveClasses:
            k_params = [1, 5, 20]
            acc = score(D, self.classes, k_params, 'distance', None, 0)[0]
            for i, k in enumerate(k_params):
                print('k={:2}-NN classification accuracy          : {:.4}%'.format(\
                        k, 100*float(acc[i])))                
            print('Goodman-Kruskal index (higher=better)    : {:.3}'.format(\
                goodman_kruskal_index(D, self.classes, 'distance')))
        else:
            print('k=5-NN classification accuracy           : No classes given')
            print('Goodman-Kruskal index (higher=better)    : No classes given')
        
        if calc_intrinsic_dimensionality:
            if self.haveVectors:
                print('original dimensionality                  : {}'.format(\
                    np.size(self.vectors, 1)))
                print('intrinsic dimensionality estimate        : {}'.format(\
                    round(intrinsic_dimension(self.vectors))))
            else:
                print('original dimensionality                  : No vectors given')
                print('intrinsic dimensionality estimate        : No vectors given')
        
    def load_dexter(self):
        """Load the example data set (dexter)."""
        
        print('\nNO PARAMETERS GIVEN! Loading & evaluating DEXTER data set.\n');
        print('DEXTER is a text classification problem in a bag-of-word');
        print('representation. This is a two-class classification problem');
        print('with sparse continuous input variables.');
        print('This dataset is one of five datasets of the NIPS 2003 feature');
        print('selection challenge.\n');
        print('http://archive.ics.uci.edu/ml/datasets/Dexter\n');
        
        import os
    
        n = 300
        dim = 20000
        
        # Read class labels
        classes_file = os.path.dirname(os.path.realpath(__file__)) +\
            '/example_datasets/dexter_train.labels'
        classes = np.loadtxt(classes_file)  

        # Read data
        vectors = np.zeros((n, dim))
        data_file = os.path.dirname(os.path.realpath(__file__)) + \
            '/example_datasets/dexter_train.data'
        with open(data_file, mode='r') as fid:
            data = fid.readlines()       
        row = 0
        for line in data:
            line = line.strip().split() # line now contains pairs of dim:val
            for word in line:
                    col, val = word.split(':')
                    vectors[row][int(col)-1] = int(val)
            row += 1
        
        # Calc distance
        D = cosine_distance(vectors)
        return D, classes, vectors
                
if __name__ == "__main__":
    hub = HubnessAnalysis()
    hub.analyse_hubness()
    """hub.analyse_hubness(origData=True, 
                           mp=True,
                           mp_gauss=False,
                           mp_gaussi=True,
                           mp_gammai=False,
                           ls=True, 
                           snn=False, 
                           cent=False, 
                           wcent=False, 
                           lcent=False
                          )
    """    