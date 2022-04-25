from operator import imod
from flask import Flask, render_template, redirect, request, url_for
# from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
import numpy as np
from io import BytesIO
import base64
import iapws
import pandas as pd
import openpyxl
import matplotlib.dates as mdates
import boto3
import glob

# from data_load_test import s3_data
from data_load import s3_data

app = Flask(__name__)

# データ読み込み
data = s3_data()

# allFiles = glob.glob("data/*/*.csv")   
# data = pd.DataFrame() 

# for file_ in allFiles:
#     df = pd.read_csv(file_,encoding = 'shift-jis') 
#     df.columns = df.loc[0]
#     df.index = df.loc[:,'時刻']
#     df = df.drop(index='時刻')
#     df = df.drop(columns = ['時刻'])
#     data = data.append(df)

data.index = pd.to_datetime(data.index,format='%Y/%m/%d %H:%M:%S')
date = data.index
data =  data.sort_index()

print(data)
# --------------------読み込み-----------------------------------
# 圧力
PT001_sw = data['PT-001 蒸気圧力(坑口)'].astype(float)
PT002_sw = data['PT-002 二相流ライン圧力'].astype(float)
PT003_s = (data['PT-003 蒸気ライン圧力'].astype(float)-101.3)/1000
PT004_w = (data['PT-004 熱水ライン圧力'].astype(float)-101.3)/1000
# psa = PT001_sw + 0.1013

PT_dict = {'PT001':PT001_sw,'PT002':PT002_sw,'PT003':PT003_s,'PT004':PT004_w}

# 温度
TT001_s = data['TT-001 蒸気ライン温度'].astype(float)
TT002_w = data['TT-002 熱水ライン温度'].astype(float)
TT003_cw = data['TT-003 山水ライン温度'].astype(float)
# TT_well = iapws.iapws97._TSat_P(psa)

temp_dict ={'TT001':TT001_s,'TT002':TT002_w,'TT003':TT003_cw}

# 流量
FT001_s = data['FT-001 蒸気ライン流量'].astype(float)*3600
FT002_w = data['FT-002 熱水ライン流量'].astype(float)*3600
FT003_cw = data['FT-003 山水ライン流量'].astype(float)
FT004_onsen = data['FT-004 温泉ライン流量'].astype(float)
FT_dict = {'FT001':FT001_s,'FT002':FT002_w,'FT003':FT003_cw,'FT004':FT004_onsen}

# 弁開度
valve = data['MVG-001 電動バルブ開度'].astype(float)

# レベル

# タンク
LTonsen = data['LT-xxx 造成タンク水位'].astype(float)
TTonsen = data['TT-xxx 造成温泉温度'].astype(float)
temp_s = data['TT-xxx 蒸気温度'].astype(float)

onsen = {'level_tank':LTonsen,'temp_tank':TTonsen,'temp_s':temp_s}


def fig_to_base64_img(fig):
    """画像を base64 に変換する。
    """
    # png 形式で出力する。
    io = BytesIO()
    fig.savefig(io, format="png")
    # base64 形式に変換する。
    io.seek(0)
    base64_img = base64.b64encode(io.read()).decode()

    return base64_img


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/pre_temp')
def pre_temp():
    fig1 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(temp_dict['TT001'],label="TT-001 Steam")
    plt.plot(temp_dict['TT002'],label="TT-002 Water")
    # plt.plot(TT_well,label="Temp well")
    # plt.plot(graph02, label='soccer', marker='D', markersize=10, markerfacecolor='lightblue')
    # plt.scatter(df.index, df.basketball, color='red', label='basketball')
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("Temperature ℃",fontsize=18)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.ylim(110,120)
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)

    fig2 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(PT_dict['PT001'],label="PT-001 geowell")
    plt.plot(PT_dict['PT002'],label="PT-002 separeter")
    plt.plot(PT_dict['PT003'],label="PT-003 Steam")
    plt.plot(PT_dict['PT004'],label="PT-004 water")
    # plt.plot(graph02, label='soccer', marker='D', markersize=10, markerfacecolor='lightblue')
    # plt.scatter(df.index, df.basketball, color='red', label='basketball')
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("Pressure MPaG",fontsize=18)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.ylim(0.06,0.20)
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)

    img1 = fig_to_base64_img(fig1)
    img2 = fig_to_base64_img(fig2)
    return render_template('pre_temp.html',img1=img1,img2=img2)

@app.route('/steam_water')
def steam_water():
    logCV = np.log((valve/6.8997))/0.4827
    Cv = np.exp(logCV)
    q = (Cv/0.366)*(((PT004_w-1.7*(PT004_w)**1.4)/0.94276)**(1/2))
    q = q *946.74/1000
    fig02 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(FT002_w,label="FT-002 water")
    plt.plot(q,label="Flow rate water(CV)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("Flow rate t/h",fontsize=18)
    # plt.ylim(0,0.5)
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)

    xx = 3.5/(18+3.5)
    ss = xx*q/(1-xx) 

    fig03 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(FT001_s,label="FT-001 steam")
    plt.plot(ss,label="Flow rate steam")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("Flow rate t/h",fontsize=18)
    plt.ylim(2,5)
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)
    img02 = fig_to_base64_img(fig02)
    img03 = fig_to_base64_img(fig03)
    
    
    fig04 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(valve,label="valve")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("opening %",fontsize=18)
    # plt.ylim(0,0.5)
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)
    img04 = fig_to_base64_img(fig04)

    return render_template('steam_water.html',img02=img02,img03=img03,img04)

@app.route('/steam_water_well')
def steam_water_well():
    return render_template('steam_water_well.html')

@app.route('/onsen')
def onsengraph():
    OverF = FT001_s+FT002_w+FT003_cw-FT004_onsen
    fig6 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(FT004_onsen,label="Onsen")
    plt.plot(FT003_cw,label="Cooling water")
    plt.plot(OverF,label="OverFlow")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("Flow rate t/h",fontsize=18)
    # plt.ylim()
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)


    fig7 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(TTonsen,label="Onsen")
    plt.plot(temp_s,label="Onsen steam")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("Temperature ℃",fontsize=18)
    # plt.ylim()
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)

    img6 = fig_to_base64_img(fig6)
    img7 = fig_to_base64_img(fig7)

    return render_template('onsen.html',img6=img6,img7=img7)

@app.route('/water')
def water():
    fig8 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(FT003_cw,label="Onsen")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("Flow rate t/h",fontsize=18)
    # plt.ylim()
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)

    fig9 = plt.figure(figsize=(15,6))
    ax = plt.axes()
    plt.plot(TT003_cw,label="Onsen")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xlabel('month-day',fontsize=18)
    plt.ylabel("Temperature ℃",fontsize=18)
    # plt.ylim()
    plt.grid()
    plt.tick_params(labelsize=18)
    plt.tight_layout()
    plt.legend(loc='upper left',fontsize=20)

    img8 = fig_to_base64_img(fig8)
    img9 = fig_to_base64_img(fig9)

    return render_template('water.html',img8=img8,img9=img9)

if __name__ == "__main__":
    app.run(debug=True)
