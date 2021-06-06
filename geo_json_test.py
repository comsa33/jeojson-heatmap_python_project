import plotly.express as px
import pandas as pd
import numpy as np
from urllib.request import urlopen
import json

state_geo = 'TL_SCCO_SIG.zip.geojson'
state_geo1 = json.load(open(state_geo, encoding='utf-8'))
import numpy as np

print(len(state_geo1['features']))
len_data = len(state_geo1['features'])
codes = []
samples = []
sig_code_table = {}
for i in range(len_data):
    sido = state_geo1['features'][i]['properties']['SIG_CD']
    sig_nm = state_geo1['features'][i]['properties']['SIG_KOR_NM']
    sig_code_table[sig_nm] = sido
    codes.append(sido)
    samples.append(np.random.randint(1,12))



### 이루오 : 모든 csv데이터의 컬럼명을 동일하게 바꾸기
def unify_cn_to_df(df):
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

file_name = "hong_df.csv"

hong_df = pd.read_csv(file_name, encoding="utf-8")
hong_db = hong_df.to_dict()
values = []
for i in hong_db.values():
    v = list(i.values())
    values.append(v)
for i,(k,v) in enumerate(hong_db.items()):
    hong_db[k] = values[i]
print("{}파일을 성공적으로 불러왔습니다.".format(file_name))

def make_countDF(db):
    hong_df = pd.DataFrame(db)
    hong_df = unify_cn_to_df(hong_df)
    hong_addr = list(hong_df.columns)
    hong_lat = list(hong_df.values[0])
    hong_lon = list(hong_df.values[1])
    new_hong_dict = {"addr":hong_addr, "lat":hong_lat, "lon":hong_lon}
    new_hong_df = pd.DataFrame(new_hong_dict)
    city1 = []
    dist = []
    for i in new_hong_df['addr'].values:
        city1.append(i.split(' ')[0])
        dist.append(i.split(' ')[1])
    new_hong_df['city_nm'] = city1
    new_hong_df['dist_nm'] = dist
    new_hong_df['SIG_CD'] = new_hong_df['dist_nm'].copy()
    for key, value in sig_code_table.items():
        new_hong_df['SIG_CD'].where(new_hong_df['dist_nm']!=key[:3], value,inplace=True)
    new_hong_df['count'] = 1
    hong_df_count = new_hong_df[['SIG_CD', 'count']]
    hong_df_count = hong_df_count.groupby(by=['SIG_CD'], as_index=False).sum()
    return hong_df_count

hong_df_count = make_countDF(hong_db)

fig = px.choropleth_mapbox(hong_df_count, geojson=state_geo1, locations='SIG_CD', color='count',
                           featureidkey="properties.SIG_CD",
                           color_continuous_scale="Viridis",
                           range_color=(0, 3),
                           mapbox_style="carto-positron",
                           zoom=6.5, center = {"lat": 35.0902, "lon": 127.7129},
                           opacity=0.7,
                           labels={'count':'지역별 매장 밀집도'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

