'''
    File name:      vignette_data.py
    Author:         Sijie Shen
    Date created:   05/08/2018
    Copyright:      2018-2020, DJI Japan Solution Team. Private.
    Python Version: 3.5.2 [python3 should all work]
'''
import numpy as np


def vignette_correct(img, k_radial=np.array([0.0018787752725863, -0.0171544589747222, 0.063879037499455, -0.1062075650846842, 0.1341353369677361, 0.0727451182520206])):
    #print("\t", 'Use Vignette Factors: ', k_radial)

    vignette_center_x = float(img.shape[0]) / 2.
    vignette_center_y = float(img.shape[1]) / 2.

    x_dim, y_dim = img.shape[0], img.shape[1]
    x, y = np.meshgrid(np.arange(x_dim), np.arange(y_dim))
    x = x.T
    y = y.T
    r = np.hypot((x - vignette_center_x), (y - vignette_center_y))

    k_t = np.append(k_radial, [1.0])
    V = np.polyval(k_t, r * 0.003)  # Change pixel value to real value: 4.8 cm / 1600 [pix]

    return img * V
