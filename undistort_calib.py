'''
    File name:      undistort_calib.py
    Author:         Sijie Shen
    Date created:   10/31/2018
    Copyright:      2018-2020, DJI Japan Solution Team. Private.
    Python Version: 3.5.2 [python3 should all work]
'''
import numpy as np
import cv2


def undistort_image(img,
                    dewarp_fx=1913.33333333, dewarp_fy=1913.33333333,
                    dewarp_cx=800.0, dewarp_cy=650.0,
                    dewarp_param=np.array([-0.3942273061584405, 0.2456273792422532, 0.0, 0.0, -0.121852202339528])):
    h, w = img.shape[:2]
    camera_matrix = np.array([[dewarp_fx, 0.0, dewarp_cx],
                              [0.0, dewarp_fy, dewarp_cy],
                              [0.0, 0.0, 1.0]])

    #print('\t', 'Dewarp camera matrix:\n', camera_matrix)
    #print('\t', 'Dewarp parameters:', dewarp_param)

    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dewarp_param, (w, h), 1, (w, h), False)

    dst = cv2.undistort(img, camera_matrix, dewarp_param, None, newcameramtx)

    # crop the image
    x, y, w, h = roi
    dst = dst[y:y + h, x:x + w]

    return cv2.resize(dst, (1600, 1300))
