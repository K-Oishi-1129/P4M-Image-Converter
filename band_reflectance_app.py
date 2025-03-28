import os
import cv2
import numpy as np
from glob import glob
from shutil import copyfile

import argparse
from argparse import RawTextHelpFormatter

from vignette_calib import vignette_correct
from undistort_calib import undistort_image
import pyexifinfo as exiftool

import csv

import datetime
from datetime import datetime
import astropy.time
import astropy.units as u
from astropy.coordinates import get_sun

from pysolar.solar import get_altitude, get_azimuth

import pytz
import re
import math

black_level = 4096.0

def run_processing_pipeline(input_path, output_dir, mode="反射率"):
    # 出力ファイル名を生成
    filename_ext = os.path.basename(input_path)
    filename = os.path.splitext(filename_ext)[0]
    ext = os.path.splitext(filename_ext)[1]
    suffix = "_radiance" if mode == "放射輝度" else "_reflectance"
    out_path = preproc(input_path, output_dir, mode=mode)
    if out_path == "blue_band_skipped":
        return "blue_band_skipped"
    return out_path if out_path and os.path.exists(out_path) else None
    print(f"[DEBUG] Saving to: {output_dir}")
    print(f"[DEBUG] Output path: {out_path}")


def OutputImg(image_float, resroot, filenameExt):
    outimg = np.clip(image_float, 0., 1.)
    outimg = (outimg * 65535.).astype('uint16')
    cv2.imwrite(os.path.join(resroot, filenameExt), outimg)

def dms_to_decimal_from_string(dms_string):
    # 正規表現で度、分、秒、方向を抽出
    dms_pattern = re.compile(r'(\d+) deg (\d+)\' (\d+\.\d+)" ([NSEW])')
    match = dms_pattern.search(dms_string)
    if match:
        degrees = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        direction = match.group(4)
        decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)
        if direction in ['S', 'W']:  # 南緯や西経はマイナスにする
            decimal_degrees *= -1
        return decimal_degrees
    return None

# タイムスタンプのフォーマットを修正する関数
def convert_timestamp_format(val_time):
    return val_time.replace(":", "-", 2)  # 最初の2つのコロンだけをハイフンに置換
    
def calculate_normal_vector(pitch, roll, yaw):
    pitch = np.deg2rad(pitch)
    roll = np.deg2rad(roll)
    yaw = np.deg2rad(yaw)
    
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(pitch), -np.sin(pitch)],
                    [0, np.sin(pitch), np.cos(pitch)]])
    
    R_y = np.array([[np.cos(roll), 0, np.sin(roll)],
                    [0, 1, 0],
                    [-np.sin(roll), 0, np.cos(roll)]])
    
    R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw), np.cos(yaw), 0],
                    [0, 0, 1]])
    
    n0 = np.array([0, 0, 1])
    n = R_z @ R_y @ R_x @ n0
    return n

def calculate_sun_vector(altitude, azimuth):
    altitude = np.deg2rad(altitude)
    azimuth = np.deg2rad(azimuth)
    
    S_x = np.cos(altitude) * np.sin(azimuth)
    S_y = np.cos(altitude) * np.cos(azimuth)
    S_z = np.sin(altitude)
    
    return np.array([S_x, S_y, S_z])

def calculate_angle_between_vectors(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    cos_theta = dot_product / (norm_v1 * norm_v2)
    angle = np.arccos(np.clip(cos_theta, -1.0, 1.0))  
    return np.rad2deg(angle)

def correct_irradiance(irradiance, angle_horizontal_sun, angle_body_sun):
    corrected_irradiance = irradiance * (np.cos(np.deg2rad(angle_horizontal_sun)) / np.cos(np.deg2rad(angle_body_sun)))
    return corrected_irradiance

def process_irradiance_correction(pitch, roll, yaw, irradiance, altitude, azimuth):
    # 機体の法線ベクトルを計算
    normal_vector = calculate_normal_vector(pitch, roll, yaw)
    horizontal_vector = np.array([0, 0, 1])
        
    # 太陽ベクトルを計算
    sun_vector = calculate_sun_vector(altitude, azimuth)
        
    # 各ベクトル間の角度を計算
    angle_body_sun = calculate_angle_between_vectors(normal_vector, sun_vector)
    angle_horizontal_sun = calculate_angle_between_vectors(horizontal_vector, sun_vector)
    print("\t", "angle_body_sunangle_body_sun: ", angle_body_sun)
    print("\t", "angle_horizontal_sun: ", angle_horizontal_sun)
    
    # Irradianceの水平補正
    corrected_irradiance = correct_irradiance(irradiance, angle_horizontal_sun, angle_body_sun)
    
    return corrected_irradiance

def write_to_csv_and_console(message, filename='result.csv'):
    print(message)  # コンソールに出力
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([message])
    
def preproc(raw_path, res_root, mode="反射率"):
    filename_ext = os.path.basename(raw_path)
    filename = os.path.splitext(filename_ext)[0]
    ext = os.path.splitext(filename_ext)[1]
    suffix = "_radiance" if mode == "放射輝度" else "_reflectance"

    print("\n[00] Reading image: ", filename_ext)
    with open(raw_path, 'rb') as f:
        img_array = np.asarray(bytearray(f.read()), dtype=np.uint8)
        img_float = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
    if img_float is None:
        print("Failed reading image, please check input")
        return
    print("\t", "Pixel value min: ", np.min(img_float), "max: ", np.max(img_float))

    # Remove black level
    print("\n[01] Removing black level")
    img_float = np.clip(img_float.astype(np.float64), black_level, 65535.0)
    img_float -= black_level
    img_float = img_float.astype(np.float64) / (65535.)
    #OutputImg(img_float, res_root, filename + "_01_BlkLvl." + ext)
    print("\t", "Pixel value min: ", np.min(img_float), "max: ", np.max(img_float))

    # vignette
    print("\n[02] Vignetting")
    img_float = vignette_correct(img_float)
    print("\t", "Pixel value min: ", np.min(img_float), "max: ", np.max(img_float))

    # signal value
    print("\n[03] Computing signal value")
    tags = exiftool.get_json(raw_path)[0]

    val_gain = tags['XMP:SensorGain']
    val_etime = tags['XMP:ExposureTime']
    val_irra = tags['XMP:Irradiance']
    val_adj = tags['XMP:SensorGainAdjustment']
    val_time = tags['EXIF:DateTimeOriginal'] 
    val_pitch = float(tags['XMP:FlightPitchDegree'])
    val_roll = float(tags['XMP:FlightRollDegree'])
    val_yaw = float(tags['XMP:FlightYawDegree'])

    val_Lat = tags['XMP:GPSLatitude']
    val_Lon = tags['XMP:GPSLongitude']    
    
    print("\t", "EXIF:DateTimeOriginal: ", val_time)
    print("\t", "XMP:SensorGain: ", val_gain)
    print("\t", "XMP:ExposureTime: ", val_etime)
    #print("\t", "XMP:SensorGainAdjustment: ", val_adj)
    print("\t", "XMP:Irradiance: ", val_irra)
    print("\t", "XMP:FlightPitchDegree: ", val_pitch)
    print("\t", "XMP:FlightRollDegree: ", val_roll)
    print("\t", "XMP:FlightYawDegree: ", val_yaw)
    
    
    val_Lat_Dec = dms_to_decimal_from_string(val_Lat)
    val_Lon_Dec = dms_to_decimal_from_string(val_Lon)
    val_time = convert_timestamp_format(val_time)
    
    dt = datetime.strptime(val_time, "%Y-%m-%d %H:%M:%S")
    timezone = pytz.timezone("Asia/Tokyo")
    dt_with_timezone = timezone.localize(dt)
    
    val_alt = get_altitude(val_Lat_Dec, val_Lon_Dec, dt_with_timezone)
    val_azi = get_azimuth(val_Lat_Dec, val_Lon_Dec, dt_with_timezone)
    print("\t", "altitude: ", val_alt)
    print("\t", "azimuth: ", val_azi)    
    
    # バンド毎のslopeとinterceptの設定（青バンドはスキップ）
    if filename_ext.endswith("1.TIF"):
        print(f"{filename_ext} は青バンドのため処理をスキップします。")
        return "blue_band_skipped"
    elif filename_ext.endswith("2.TIF"):
        slope_cam, intercept_cam = 35.27, 0
        slope_sun, intercept_sun = 4.64e-3, 2.83
        sensitivity = 0.705
    elif filename_ext.endswith("3.TIF"):
        slope_cam, intercept_cam = 33.06, 0
        slope_sun, intercept_sun = 4.74e-3, 1.95
        sensitivity = 0.709
    elif filename_ext.endswith("4.TIF"):
        slope_cam, intercept_cam = 29.05, 0
        slope_sun, intercept_sun = 4.44e-3, 0.99
        sensitivity = 0.589
    elif filename_ext.endswith("5.TIF"):
        slope_cam, intercept_cam = 26.74, 0
        slope_sun, intercept_sun = 5.50e-3, 0.94
        sensitivity = 0.396
    else:
        print(f"Unknown band for file: {filename_ext}")
        return

    
    corrected_irradiance = process_irradiance_correction(val_pitch, val_roll, val_yaw, val_irra, val_alt, val_azi)
    print("\t",f"Corrected Irradiance: {corrected_irradiance}")


    # 画像の露出とゲイン補正
    img_float = (img_float) / (val_gain * (val_etime) / 1e2)
    print(f"\n[04] Exposure and Gain Correction - min:{np.min(img_float)}, max:{np.max(img_float)}")

    img_radiance = (img_float * slope_cam + intercept_cam) / sensitivity
    calibrated_irradiance = corrected_irradiance * slope_sun + intercept_sun
    print(f"\tImage Radiance - min: {np.min(img_radiance)}, max: {np.max(img_radiance)}")
    print("\t",f"calibrated irradiance: {calibrated_irradiance}")

    # カメラと太陽の変換係数の適用
    if mode == "放射輝度":
        img_float = img_radiance
    else:
        img_float = img_radiance / calibrated_irradiance
        
    print(f"\n[05] {'Radiance' if mode == '放射輝度' else 'Reflectance'} - min: {np.min(img_float)}, max: {np.max(img_float)}")

    # 歪み補正
    print("\n[06] Undistortion")
    img_float = undistort_image(img_float)
    out_filename = filename + suffix + ext
    OutputImg(img_float, res_root, out_filename)
    return os.path.join(res_root, out_filename)
    print("\t", "Pixel value min: ", np.min(img_float), "max: ", np.max(img_float))

        
    # _dump
    #np.save(os.path.join(res_root, filename), img_float)

    print("Preprocess done!")

