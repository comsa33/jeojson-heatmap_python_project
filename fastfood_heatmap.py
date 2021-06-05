from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
from selenium import webdriver
import time
import requests
import re
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5 import QtWidgets, QtWebEngineWidgets


form_class = uic.loadUiType("heatmap.ui")[0]


class heatmapApp(QMainWindow, form_class):
    gugun = pd.read_csv('군구.csv', encoding='utf-8')

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(self.browser)
        self.frame_2.setLayout(vlayout)
        self.search_word = ""
        self.btn_search.clicked.connect(self.click_search)
        self.city1.currentTextChanged.connect(self.combo_box_changed)

    # 윤영완 : 콤보박스 문구들
    def combo_box_changed(self):
        text = self.city1.currentText()
        self.city2.clear()
        self.city2.addItem("전체검색")
        if text != '전체검색':
           for i in self.gugun[text]:
               if str(i).lower() == "nan":
                   break
               self.city2.addItem(str(i))

    def show_graph(self, ex, texts):
        if ex:
            total = 0
            result_text = "검색결과 : "
            for i in range(len(ex)):
                sum_ = ex[i]['count'].sum()
                if i == len(ex)-1:
                    result_text += str(texts[i]) + ":" + str(sum_) + "개"
                else:
                    result_text += str(texts[i]) + ":" + str(sum_) + "개 / "
                total += sum_

            colors = [px.colors.sequential.Aggrnyl, px.colors.sequential.Purp,
                      px.colors.sequential.Cividis, px.colors.sequential.Blues]
            self.result_count.setText("총 " + str(total) + "개")

            fig = go.Figure(go.Densitymapbox(lat=ex[0].Latitude, lon=ex[0].Longitude,
                                             name=texts[0],
                                             hoverinfo="all", hovertext=ex[0].address,
                                             hovertemplate=
                                             "주소: %{hovertext}<br>" +
                                             "경도: %{lon}<br>" +
                                             "위도: %{lat}<br>",
                                             opacity=0.85, showlegend=True, showscale=False,
                                             radius=10, colorscale=px.colors.sequential.amp))

            opacity = 0.8
            for i in range(len(ex)-1):
                fig.add_trace(go.Densitymapbox(lat=ex[i+1].Latitude, lon=ex[i+1].Longitude,
                                               name=texts[i+1],
                                               hoverinfo="all", hovertext=ex[i+1].address,
                                               hovertemplate=
                                               "주소: %{hovertext}<br>" +
                                               "경도: %{lon}<br>" +
                                               "위도: %{lat}<br>",
                                               opacity=opacity, showlegend=True, showscale=False,
                                               radius=10, colorscale=colors[i]))
                opacity -= 0.05

            fig.update_layout(title=dict({"text": result_text, "font_size": 15}),
                              legend_title=dict({"text": "가게이름"}))
            fig.update_layout(mapbox_style="carto-positron", mapbox_center=dict(lat=35.6, lon=127))
            fig.update_layout(margin={"r": 100, "t": 60, "l": 0, "b": 0}, mapbox=dict(zoom=6))
            self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
        else:
            pass

    ### 박세은, 윤영완, 이루오 : 클릭 시 검색 알고리즘
    def click_search(self):
        ex_list = []
        checked_text = []
        if self.city1.currentText() != "전체검색" and self.city2.currentText() != "전체검색":
            self.search_word = self.city1.currentText() + ' ' + self.city2.currentText()
        elif self.city1.currentText() != "전체검색" and self.city2.currentText() == "전체검색":
            self.search_word = self.city1.currentText()

        if self.h_check.isChecked():
            try:
                db_h, df_h = self.hong()
                ex_hong = self.create_ex(db_h, "홍루이젠")
                ex_list.append(ex_hong)
                checked_text.append(self.h_check.text())
            except:
                pass

        if self.l_check.isChecked():
            try:
                db_l, df_l = self.lotteria()
                ex_lotteria = self.create_ex(db_l, "롯데리아")
                ex_list.append(ex_lotteria)
                checked_text.append(self.l_check.text())
            except:
                pass

        if self.bk_check.isChecked():
            try:
                db_b, df_b = self.burgerking()
                ex_burgerking = self.create_ex(db_b, "버거킹")
                ex_list.append(ex_burgerking)
                checked_text.append(self.bk_check.text())
            except:
                pass

        if self.mom_check.isChecked():
            try:
                db_m, df_m = self.momstouch()
                ex_momstouch = self.create_ex(db_m, "맘스터치")
                ex_list.append(ex_momstouch)
                checked_text.append(self.mom_check.text())
            except:
                pass

        if self.mc_check.isChecked():
            try:
                db_mc, df_mc = self.mcdonalds()
                ex_mcdonalds = self.create_ex(db_mc, "맥도날드")
                ex_list.append(ex_mcdonalds)
                checked_text.append(self.mc_check.text())
            except:
                pass

        return self.show_graph(ex_list, checked_text)

    ### 이루오 : 검색어 기반으로 위도경도 df 만들기
    def create_ex(self, db, name):
        search_word = self.search_word
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
        ex2['name'] = name
        ex2['count'] = 1
        return ex2

    ### 이루오 : 모든 csv데이터의 컬럼명을 동일하게 바꾸기
    def unify_cn_to_df(self, df):
        new_columns = list(df.columns)

        full_n = ("서울특별시", "부산광역시", "울산광역시", "인천광역시", "대전광역시", "광주광역시", "대구광역시",
                  "경기도", '강원도', '충청북도', "충청남도", "경상북도", "경상남도", "전라북도", '전라남도', "제주도", "세종특별자치시")
        short_n = ("서울", "부산", "울산", "인천", "대전", "광주", "대구", "경기", "강원", "충북", "충남", "경북", "경남", "전북", "전남", "제주", "세종")
        name_map = list(zip(short_n, full_n))

        new_columns_fn = []
        for col in new_columns:
            count = 0
            for s, f in name_map:
                if s[0] in col.split()[0] and s[1] in col.split()[0]:
                    new_col_split = col.split()
                    new_col_split[0] = f
                    new_col = " ".join(new_col_split)
                    new_columns_fn.append(new_col)
                elif (count + 1 == len(name_map)) and (new_columns.index(col) == len(new_columns_fn)):
                    new_columns_fn.append(col)
                count += 1

        df.columns = new_columns_fn
        return df

    ### 이루오 : 홍루이젠 csv 파일 불러오기
    def hong(self):
        file_name = "hong_df.csv"
        try:
            self.hong_df = pd.read_csv(file_name, encoding="utf-8")
            self.unify_cn_to_df(self.hong_df)
            self.hong_df.columns
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

    ### 윤영완 : 버거킹 csv 파일 불러오기
    def burgerking(self):
        file_name = "burgerking_df.csv"
        try:
            self.burgerking_df = pd.read_csv(file_name, encoding="utf-8")
            self.unify_cn_to_df(self.burgerking_df)
            self.burgerking_db = self.burgerking_df.to_dict()
            values = []
            for i in self.burgerking_db.values():
                v = list(i.values())
                values.append(v)
            for i, (k, v) in enumerate(self.burgerking_db.items()):
                self.burgerking_db[k] = values[i]
            print("{}파일을 성공적으로 불러왔습니다.".format(file_name))
        except:
            print("불러올수 있는 {}파일이 없습니다.".format(file_name))
            pass
        return self.burgerking_db, self.burgerking_df

    ### 최용천 : 맘스터치 csv 파일 불러오기
    def momstouch(self):
        file_name = "momstouch_df.csv"
        try:
            self.momstouch_df = pd.read_csv(file_name, encoding="utf-8")
            self.unify_cn_to_df(self.momstouch_df)
            self.momstouch_db = self.momstouch_df.to_dict()
            values = []
            for i in self.momstouch_db.values():
                v = list(i.values())
                values.append(v)
            for i, (k, v) in enumerate(self.momstouch_db.items()):
                self.momstouch_db[k] = values[i]
            print("{}파일을 성공적으로 불러왔습니다.".format(file_name))
        except:
            print("불러올수 있는 {}파일이 없습니다.".format(file_name))
            pass
        return self.momstouch_db, self.momstouch_df

    ### 이광원 : 롯데리아 csv 파일 불러오기
    def lotteria(self):
        file_name = "lotteria_df.csv"
        try:
            self.lotteria_df = pd.read_csv(file_name, encoding="utf-8")
            self.unify_cn_to_df(self.lotteria_df)
            self.lotteria_db = self.lotteria_df.to_dict()
            values = []
            for i in self.lotteria_db.values():
                v = list(i.values())
                values.append(v)
            for i, (k, v) in enumerate(self.lotteria_db.items()):
                self.lotteria_db[k] = values[i]
            print("{}파일을 성공적으로 불러왔습니다.".format(file_name))
        except:
            print("불러올수 있는 {}파일이 없습니다.".format(file_name))
            pass
        return self.lotteria_db, self.lotteria_df

    ### 박세은 : 맥도날드 csv 파일 불러오기
    def mcdonalds(self):
        file_name = "mcdonalds_df.csv"
        try:
            self.mcdonalds_df = pd.read_csv(file_name, encoding="utf-8")
            self.unify_cn_to_df(self.mcdonalds_df)
            self.mcdonalds_db = self.mcdonalds_df.to_dict()
            values = []
            for i in self.mcdonalds_db.values():
                v = list(i.values())
                values.append(v)
            for i, (k, v) in enumerate(self.mcdonalds_db.items()):
                self.mcdonalds_db[k] = values[i]
            print("{}파일을 성공적으로 불러왔습니다.".format(file_name))
        except:
            print("불러올수 있는 {}파일이 없습니다.".format(file_name))
            pass
        return self.mcdonalds_db, self.mcdonalds_df

    def hong_get_latlng(self, stores, latlngs, hong_db):
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
                hong_db[addr] = latlng
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
        self.resize(1000, 850)
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
