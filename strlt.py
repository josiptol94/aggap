import streamlit as st
from streamlit_metrics import metric, metric_row
import requests
import time
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from datetime import date , timedelta
import altair as alt
import json
import pydeck as pdk



unixts_end=time.time()
unixts_start=unixts_end-2073600
unixts_start24=unixts_end-86400
unixts_start24=str(int(unixts_start24))
unixts_end=str(int(unixts_end))
unixts_start=str(int(unixts_start))
appid="719ffe1cdb61ea1445bbc8318314d4a4"
call_getpolly="http://api.agromonitoring.com/agro/1.0/polygons?appid="+appid
response_data = requests.get(call_getpolly).json()
df_polly=pd.DataFrame(response_data,columns=['id','geo_json','name','center','area'])
coordinates=df_polly['center']
pollyname=df_polly['name']
pollyid=df_polly['id']
df_rain=pd.DataFrame(columns=['dt','rain','count','name'])
df_satimg=pd.DataFrame(columns=['dt','type','dc','cl','sun','image','tile','stats','data','name'])
df_raincur=pd.DataFrame(columns=['dt','rain','count','name'])
df_soilcur=pd.DataFrame(columns=['dt','t10','moisture','t0','name'])
df_soilhist=pd.DataFrame(columns=['dt','t10','moisture','t0','name'])
df_loc=pd.DataFrame(columns=['lon','lat','name'])
st.title('Pregled Tabli')

#koordinate svih tabli 
lon=[j[0] for j in coordinates]
lat=[j[1] for j in coordinates]


#poziv za podatake o kiši unazad 31 dan
i=0
while i < len(lat):
    call_getrain="https://api.agromonitoring.com/agro/1.0/weather/history/accumulated_precipitation?lat="+str(lat[i])+"&lon="+str(lon[i])+"&start="+unixts_start+"&end="+unixts_end+"&appid="+appid
    response_data = pd.DataFrame(requests.get(call_getrain).json())
    response_data['name']=pollyname[i]
    df_rain=df_rain.append(response_data)
    i +=1

########
#Izbor table 
option=st.selectbox("Izaberite tablu",df_polly['name'])

df_polly[['lon','lat']] = pd.DataFrame(df_polly.center.tolist(), index= df_polly.index)
print(df_polly)
df_polly=df_polly.loc[df_polly['name']==option] #referenciram se na izbornik

st.map(df_polly,zoom=11,use_container_width=True)



#pripreme za graf
df_rain.dt=pd.to_datetime(df_rain['dt'], unit = 's') #prebacio sam se iz unixts u normalan
rain_data=df_rain[['rain','dt','name']] #ono što želim ubaciti u graf
rain_data=rain_data.loc[rain_data['name']==option] #referenciram se na izbornik 

line_chart=alt.Chart(rain_data).mark_line().encode(
    x=alt.X('dt', axis=alt.Axis(title='Datum')),
    y=alt.Y('rain', axis=alt.Axis(title='Kiša u mm')),
    color=alt.Color('name',legend=alt.Legend(title="Tabla")),
    strokeDash='name',
).configure_axis(
    grid=False
).properties(
    title="Količina kiše u zadnjih mjesec dana",
    width=700,
    height=200
)

line_chart.configure_title(
    fontSize=20,
    font='Courier',
    anchor='start',
    color='gray')




#############################
i=0
while i < len(pollyid):
    call_getsoil="http://api.agromonitoring.com/agro/1.0/soil?"+"polyid="+pollyid[i]+"&appid="+appid
    response_data = pd.DataFrame(requests.get(call_getsoil).json(), index=[0])
    response_data['name']=pollyname[i]
    df_soilcur=df_soilcur.append(response_data)
    i +=1

df_soilcur.dt=df_soilcur.dt=pd.to_datetime(df_soilcur['dt'], unit = 's') #prebacio sam se iz unixts u normalan

df_soilcur=df_soilcur.loc[df_soilcur['name']==option]


#poziv za podatake o kiši unazad 24h
i=0
while i < len(lat):
    call_getrain="https://api.agromonitoring.com/agro/1.0/weather/history/accumulated_precipitation?lat="+str(lat[i])+"&lon="+str(lon[i])+"&start="+unixts_start24+"&end="+unixts_end+"&appid="+appid
    response_data = pd.DataFrame(requests.get(call_getrain).json())
    response_data['name']=pollyname[i]
    df_raincur=df_raincur.append(response_data)
    i +=1

df_raincur=df_raincur.loc[df_raincur['name']==option]




metric_row(
    {
        "Temperatura na 10cm": str(round(df_soilcur['t10'][0]-273.15,1)),
        "mm3 kiše u protekla 24h":df_raincur['rain'][0],
        "Vlažnost tla": str(round(df_soilcur['moisture'][0],3)),
        
    }
)


#poziv za podatake o tlu unazad 31 dan
i=0
while i < len(pollyid):
    call_getsoilh="http://api.agromonitoring.com/agro/1.0/soil/history?start="+unixts_start+"&end="+unixts_end+"&polyid="+pollyid[i]+"&appid="+appid
    response_data = pd.DataFrame(requests.get(call_getsoilh).json())
    response_data['name']=pollyname[i]
    df_soilhist=df_soilhist.append(response_data)
    i +=1


#pripreme za graf
df_soilhist.dt=pd.to_datetime(df_soilhist['dt'], unit = 's') #prebacio sam se iz unixts u normalan
df_soilhist.t10=df_soilhist.t10-273.15 #prebacujem iz kelvina
soil_data=df_soilhist[['t10','dt','name']] #ono što želim ubaciti u graf
soil_data=soil_data.loc[soil_data['name']==option] #referenciram se na izbornik

soil_data_moisture=df_soilhist[['moisture','dt','name']] #ono što želim ubaciti u graf
soil_data_moisture=soil_data_moisture.loc[soil_data_moisture['name']==option] #referenciram se na izbornik




###df_soilhist=pd.DataFrame(columns=['dt','t10','moisture','t0','name'])


line_chart1=alt.Chart(soil_data).mark_line().encode(
    x=alt.X('dt', axis=alt.Axis(title='Datum')),
    y=alt.Y('t10', axis=alt.Axis(title='Temperatura tla')),
    color=alt.Color('name',legend=alt.Legend(title="Tabla")),
    strokeDash='name',
).configure_axis(
    grid=False
).properties(
    title="Temperatura tla na 10cm kroz mjesec dana",
    width=700,
    height=200
)

line_chart1.configure_title(
    fontSize=20,
    font='Courier',
    anchor='start',
    color='gray')

#########

line_chart2=alt.Chart(soil_data_moisture).mark_line().encode(
    x=alt.X('dt', axis=alt.Axis(title='Datum')),
    y=alt.Y('moisture', axis=alt.Axis(title='Vlažnost tla')),
    color=alt.Color('name',legend=alt.Legend(title="Tabla")),
    strokeDash='name',
).configure_axis(
    grid=False
).properties(
    title="Vlažnost tla na 10cm kroz mjesec dana",
    width=700,
    height=200
)

line_chart2.configure_title(
    fontSize=20,
    font='Courier',
    anchor='start',
    color='gray')

#st.altair_chart(line_chart2)

x=round(df_polly['lat'],2)
y=round(df_polly['lon'],2)

st.altair_chart(line_chart)
st.altair_chart(line_chart1)
st.altair_chart(line_chart2)


st.deck_gl_chart(
            viewport={
                'latitude': df_polly['lat'],
                'longitude':  df_polly['lon'],
                'zoom': 11
            },
            layers=[{
                'type': 'ScatterplotLayer',
                'data': df_polly,
                'radiusScale': 250,
   'radiusMinPixels': 5,
                'getFillColor': [248, 24, 148],
            }]
        )
