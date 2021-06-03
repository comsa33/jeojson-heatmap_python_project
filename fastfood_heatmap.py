from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
import plotly.express as px
import datetime
from selenium import webdriver
import time
import requests
import re
import sys
import os
import webbrowser
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
from PyQt5 import uic
from PyQt5 import sip
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets


form_class = uic.loadUiType("heatmap.ui")[0]

class heatmapApp(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(self.browser)
        self.frame_2.setLayout(vlayout)
        self.btn_search.clicked.connect(self.click_search)

    def show_graph(self, ex):
        total = ex['count'].sum()
        self.result_count.setText("총 "+str(total)+"개")
        fig = px.density_mapbox(ex, lat='Latitude', lon='Longitude', z='count', radius=10,
                                hover_name='name', hover_data=['address'],
                                center=dict(lat=35.6, lon=127), zoom=5.5,
                                mapbox_style="carto-positron", color_continuous_scale=px.colors.sequential.Sunset)

        fig.update_layout(margin=dict(b=0, t=0, l=0, r=0))

        self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))

    def click_search(self):
        db, df = self.hong()
        ex = self.create_ex(db)
        return self.show_graph(ex)

    ### 이루오 : 홍루이젠 웹스크래핑
    def create_ex(self, db):
        search_word=""
        addr = []
        lat_lngs = []
        for k, v in db.items():
            if search_word in k:
                lat_lngs.append(v)
                addr.append(k)

        ex_ = []
        for x in zip(*lat_lngs):
            ex_.append(list(x))

        ex2 = {}
        ex2['Latitude'] = ex_[0]
        ex2['Longitude'] = ex_[1]

        ex2 = pd.DataFrame(ex2)
        ex2['address'] = addr
        ex2['name'] = "홍루이젠"
        ex2['count'] = 1
        return ex2

    def hong(self):
        file_name = "hong_df.csv"
        try:
            self.hong_df = pd.read_csv(file_name, encoding="utf-8")
            self.hong_db = self.hong_df.to_dict()
            values = []
            for i in self.hong_db.values():
                v = list(i.values())
                values.append(v)
            for i, (k, v) in enumerate(self.hong_db.items()):
                self.hong_db[k] = values[i]
            print("{}파일을 성공적으로 불러왔습니다.".format(file_name))
        except:
            print("불러올수 있는 {}파일이 없습니다.".format(file_name))
            options = webdriver.ChromeOptions()
            # options.add_argument('headless')
            options.add_argument('window-size=1920x1080')
            options.add_argument("disable-gpu")
            # 혹은 options.add_argument("--disable-gpu")

            wd = webdriver.Chrome('/home/ai106/PycharmProjects/pythonProject/heatmap_fastfood/chromedriver',
                                  options=options)
            stores = []
            for i in range(33):
                hong_url = 'https://www.hongruizhen.com/store/store.php?page=' + str(i + 1)
                wd.get(hong_url)
                time.sleep(0.3)

                html = wd.page_source
                soup_hong = BeautifulSoup(html, 'html.parser')
                store_list = soup_hong.select(
                    '#contents > div > div.store_wr > div.store_cont > div > div > div.store_list')
                for store in store_list:
                    store_info = store.select("div > ul > li > div.store_detail > p:nth-child(4)")
                    for store_addr in store_info:
                        print(store_addr.get_text()[6:])
                        stores.append(store_addr.get_text()[6:])

            trash = ['전북 정읍시 충청로 59',
                     '전북 군산시 월명로 24',
                     '경기 수원시 권선구 서수원로 577']

            for i in trash:
                stores.remove(i)
            latlngs = []
            self.hong_db = {}
            self.hong_get_latlng(stores, latlngs, self.hong_db)
            self.hong_df = pd.DataFrame(self.hong_db)
            self.hong_df.to_csv("hong_df.csv", encoding='utf-8', index=False)

        return self.hong_db, self.hong_df

    def hong_get_latlng(self, stores, latlngs, db):
        for addr in stores:
            print("\n", addr)
            # 카카오 REST API로 좌표 구하기
            address_latlng = self.getLatLng(addr)
            # 좌표로 지도 첨부 HTML 생성
            if str(address_latlng).find("ERROR") < 0:
                map_html = self.getKakaoMapHtml(address_latlng)
                html = BeautifulSoup(map_html, "html.parser")
                script = html.select("script")
                script = script[1].string
                latlng = re.findall("\d+", script)[:4]
                latlng = (latlng[0] + "." + latlng[1], latlng[2] + "." + latlng[3])
                print(latlng)
                latlngs.append(latlng)
                db[addr] = latlng
            else:
                print("[ERROR]getLatLng")

    ### kakao api : 주소입력 >>> 위도경도 html형식으로 가져오는 코드
    def getLatLng(address):
        result = ""
        url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
        rest_api_key = '58871f76e7240525a7f5d85c8b83ef1c'
        header = {'Authorization': 'KakaoAK ' + rest_api_key}
        r = requests.get(url, headers=header)
        if r.status_code == 200:
            result_address = r.json()["documents"][0]["address"]
            result = result_address["y"], result_address["x"]
        else:
            result = "ERROR[" + str(r.status_code) + "]"
        return result

    def getKakaoMapHtml(address_latlng):
        javascript_key = "bf0ed730bee63cd68c5a342ba9bbca54"
        result = ""
        result = result + "<div id='map' style='width:300px;height:200px;display:inline-block;'></div>" + "\n"
        result = result + "<script type='text/javascript' src='//dapi.kakao.com/v2/maps/sdk.js?appkey=" + javascript_key + "'></script>" + "\n"
        result = result + "<script>" + "\n"
        result = result + "    var container = document.getElementById('map'); " + "\n"
        result = result + "    var options = {" + "\n"
        result = result + "           center: new kakao.maps.LatLng(" + address_latlng[0] + ", " + \
                 address_latlng[1] + ")," + "\n"
        result = result + "           level: 3" + "\n"
        result = result + "    }; " + "\n"
        result = result + "    var map = new kakao.maps.Map(container, options); " + "\n"
        # 검색한 좌표의 마커 생성을 위해 추가
        result = result + "    var markerPosition  = new kakao.maps.LatLng(" + address_latlng[0] + ", " + \
                 address_latlng[1] + ");  " + "\n"
        result = result + "    var marker = new kakao.maps.Marker({position: markerPosition}); " + "\n"
        result = result + "    marker.setMap(map); " + "\n"
        result = result + "</script>" + "\n"
        return result


    def initUI(self):
        self.setWindowTitle('전국 패스트푸드 체인 HEATMAP')
        # self.resize(1000, 850)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = heatmapApp()
    form.show()
    sys.exit(app.exec_())

