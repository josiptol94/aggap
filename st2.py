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
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .reportview-container {
        background: url("https://cdn.agrilifetoday.tamu.edu/wp-content/uploads/2020/06/DSC_3297.jpg")
    }
    </style>
    """,
    unsafe_allow_html=True
)

unixts_end=time.time()
unixts_start=unixts_end-2073600
unixts_start24=unixts_end-86400


end=str(date.fromtimestamp(unixts_end)+ timedelta(days=1))
start=str(date.fromtimestamp(unixts_start)- timedelta(days=0))

unixts_start24=str(int(unixts_start24))
unixts_end=str(int(unixts_end))
unixts_start=str(int(unixts_start))

### NASLOV
st.title('Pregled poljoprivrednog zemljišta')

col1, col2,col3,col4=st.beta_columns([1, 1,1,1])

with col1:
    start_date_standard=st.date_input('Početak pregleda',datetime.date.today()- timedelta(days=30))
with col2:
    end_date_standard=st.date_input('Kraj pregleda',datetime.date.today())
start_date_unix=str(time.mktime(start_date_standard.timetuple()))
end_date_unix=str(time.mktime(end_date_standard.timetuple()))


############################DATAFRAMEOVI############################


df_rain=pd.DataFrame(columns=['dt','rain','count','name'])
df_satimg=pd.DataFrame(columns=['dt','type','dc','cl','sun','image','tile','stats','data','name'])
df_raincur=pd.DataFrame(columns=['dt','rain','count','name'])
df_soilcur=pd.DataFrame(columns=['dt','t10','moisture','t0','name'])
df_soilhist=pd.DataFrame(columns=['dt','t10','moisture','t0','name'])
df_loc=pd.DataFrame(columns=['lon','lat','name'])
df_ndvi=pd.DataFrame(columns=['dt','data.min','data.max','data.median','name'])




####################################################################





#### prikupim sve table pojedinog korisnika/trenutno hardkodirani appid, kasnije povući iz baze 
appid="719ffe1cdb61ea1445bbc8318314d4a4"
call_getpolly="http://api.agromonitoring.com/agro/1.0/polygons?appid="+appid
response_data = requests.get(call_getpolly).json()
df_polly=pd.DataFrame(response_data,columns=['id','geo_json','name','center','area'])


#### izvadio sam si sve geo dužine i širine 
lon=[j[0] for j in df_polly.center]
lat=[j[1] for j in df_polly.center]




###########################################################################DOHVATI PODATAKA##############################################################################################################

#### NDVI INDEKS

i=0
while i < len(df_polly):
    call_getndvi="https://api.agromonitoring.com/agro/1.0/ndvi/history?polyid="+df_polly.id.iloc[i]+"&start="+start_date_unix+"&end="+end_date_unix+"&appid="+appid
    response_data =  pd.json_normalize(requests.get(call_getndvi).json())
    response_data['name']=df_polly.name.iloc[i]
    df_ndvi=df_ndvi.append(response_data)
    i +=1

df_ndvi.rename(columns={'data.median': 'medianndvi', 'data.max': 'maxndvi', 'data.min': 'minndvi'}, inplace=True) ###preimenovao sam kolone u dataframe-u 
df_ndvi.medianndvi = df_ndvi.medianndvi.astype(float) ###prebacio se iz stringa u float 
df_ndvi.medianndvi=df_ndvi.medianndvi.round(decimals=2) ###zaokružio na 2 decimale

#### KUMULATIVNA KIŠA /pozivam podatke o kiši za sve table/ ovo ćemo prepraviti !!!!!

i=0
while i < len(df_polly):
    call_getrain="https://api.agromonitoring.com/agro/1.0/weather/history/accumulated_precipitation?lat="+str(lat[i])+"&lon="+str(lon[i])+"&start="+start_date_unix+"&end="+end_date_unix+"&appid="+appid
    response_data =  pd.json_normalize(requests.get(call_getrain).json())
    response_data['name']=df_polly.name.iloc[i]
    df_rain=df_rain.append(response_data)
    i +=1

#### TRENUTNA KIŠA količina padalina u 24h 
i=0
while i < len(df_polly):
    call_getrain="https://api.agromonitoring.com/agro/1.0/weather/history/accumulated_precipitation?lat="+str(lat[i])+"&lon="+str(lon[i])+"&start="+unixts_start24+"&end="+end_date_unix+"&appid="+appid
    response_data = pd.DataFrame(requests.get(call_getrain).json(),index=[0])
    response_data['name']=df_polly.name.iloc[i]
    df_raincur=df_raincur.append(response_data)
    i +=1


    

#### TRENUTNO STANJE TLA / ovo ćemo prepraviti !!!!!
i=0
while i < len(df_polly):
    call_getsoil="http://api.agromonitoring.com/agro/1.0/soil?"+"polyid="+df_polly.id.iloc[i]+"&appid="+appid
    response_data =  pd.json_normalize(requests.get(call_getsoil).json())
    response_data['name']=df_polly.name.iloc[i]
    df_soilcur=df_soilcur.append(response_data)
    i +=1

#### STANJE TLA POVIJESNO / ovo ćemo prepraviti !!!!!
i=0
while i < len(df_polly):
    call_getsoilh="http://api.agromonitoring.com/agro/1.0/soil/history?start="+start_date_unix+"&end="+end_date_unix+"&polyid="+df_polly.id.iloc[i]+"&appid="+appid
    response_data =  pd.json_normalize(requests.get(call_getsoilh).json())
    response_data['name']=df_polly.name.iloc[i]
    df_soilhist=df_soilhist.append(response_data)
    i +=1

df_soilhist.t10 = df_soilhist.t10.astype(float) ###prebacio se iz stringa u float 
df_soilhist.t10=df_soilhist.t10.round(decimals=2) ###zaokružio na 2 decimale

#######################################################################################################################################################################################################



#####################################################################POČINJEM SLAGATI WEB##############################################################################################################


col8, col9=st.beta_columns([1, 1])

with col8:
### IZBORNIK TABLE 
    option=st.selectbox("Izaberite tablu",df_polly['name'])


st.write(' ')

st.write('Trenutno stanje tla:')
st.write(' ')

####PRIKAZ TRENUTNOG STANJA TLA
df_raincur=df_raincur.loc[df_raincur['name']==option] ### referenciram se na odabranu tablu
df_soilcur=df_soilcur.loc[df_soilcur['name']==option] ### referenciram se na odabranu tablu
a=df_polly.loc[df_polly['name']==option,'area'] ### referenciram se na odabranu tablu

a=a.iloc[0]
print(a)



df_soilcur.dt=df_soilcur.dt=pd.to_datetime(df_soilcur['dt'], unit = 's') #prebacio sam se iz unixts u normalan



metric_row(
    {
        "°C na 10cm": str(round(df_soilcur['t10'][0]-273.15,1)),
        "mm3 kiše u protekla 24h":df_raincur['rain'][0],
        "Vlažnost tla": str(round(df_soilcur['moisture'][0],2)),
        "Površina čestice":str(round(a,2)),
        
    }
)

######MAPA###########
df_polly[['lon','lat']] = pd.DataFrame(df_polly.center.tolist(), index= df_polly.index)
df_polly=df_polly.loc[df_polly['name']==option] #referenciram se na izbornik
st.map(df_polly,zoom=11,use_container_width=True)
######MAPA###########

################################################################GRAFOVI################################################################
########GRAF TEMPERATURE TLA########

#pripreme za graf 
df_soilhist.dt=pd.to_datetime(df_soilhist['dt'], unit = 's') #prebacio sam se iz unixts u normalan
df_soilhist.t10=df_soilhist.t10-273.15 #prebacujem iz kelvina
df_soilhist.t0=df_soilhist.t0-273.15 #prebacujem iz kelvina
df_soilhist=df_soilhist.loc[df_soilhist.name==option] #referenciram se na izbornik
#print(df_soilhist)




line_chart1=alt.Chart(df_soilhist).mark_line().encode(
    x=alt.X('dt:T', axis=alt.Axis(title='Datum', format = ("%a %d"),tickMinStep=1.0,labelOverlap=True),scale=alt.Scale(domain=[str(df_soilhist.dt.min()), str(df_soilhist.dt.max())])),
    y=alt.Y('t10', scale=alt.Scale(domain=[df_soilhist.t10.min(), df_soilhist.t10.max()]),axis=alt.Axis(title='Temperatura tla')),
    color=alt.Color('name',legend=None),

)

line_chart1.configure_title(
    fontSize=20,
    font='Courier',
    anchor='start',
    color='gray')

nearest = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['dt'], empty='none')

selectors = alt.Chart(df_soilhist).mark_point().encode(
    x='dt:T',
    opacity=alt.value(0),
).add_selection(
    nearest
)


points = line_chart1.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)


text = line_chart1.mark_text(align='left', dx=5, dy=-5).encode(
    text=alt.condition(nearest, 't10:Q', alt.value(' '))
)


rules = alt.Chart(df_soilhist).mark_rule(color='gray').encode(
    x='dt:T',
).transform_filter(
    nearest
)

#####SVI LAYERI U 1 GRAF
chart = alt.layer(
    line_chart1, selectors, points, rules, text
).configure(background='rgb(255,255,255,0.7)').configure_axis(
    grid=False
).properties(
    width=1755,
    height=400
).configure_view(
    strokeOpacity=0)

########GRAF VLAŽNOSTI  TLA########

line_chart2=alt.Chart(df_soilhist).mark_line().encode(
    x=alt.X('dt:T', axis=alt.Axis(title='Datum', format = ("%a %d"),tickMinStep=1.0,labelOverlap=True),scale=alt.Scale(domain=[str(df_soilhist.dt.min()), str(df_soilhist.dt.max())])),
    y=alt.Y('moisture', scale=alt.Scale(domain=[df_soilhist.moisture.min(), df_soilhist.moisture.max()]),axis=alt.Axis(title='Vlažnost tla')),
    color=alt.Color('name',legend=None),

)

line_chart2.configure_title(
    fontSize=20,
    font='Courier',
    anchor='start',
    color='gray')

nearest = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['dt'], empty='none')

selectors = alt.Chart(df_soilhist).mark_point().encode(
    x='dt:T',
    opacity=alt.value(0),
).add_selection(
    nearest
)


points = line_chart2.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)


text = line_chart2.mark_text(align='left', dx=5, dy=-5).encode(
    text=alt.condition(nearest, 'moisture:Q', alt.value(' '))
)


rules = alt.Chart(df_soilhist).mark_rule(color='gray').encode(
    x='dt:T',
).transform_filter(
    nearest
)

#####SVI LAYERI U 1 GRAF
chart2 = alt.layer(
    line_chart2, selectors, points, rules, text
).configure(background='rgb(255,255,255,0.7)').configure_axis(
    grid=False
).properties(
    width=1755,
    height=400
).configure_view(
    strokeOpacity=0)


########GRAF NDVI INDEKS ########

df_ndvi.dt=pd.to_datetime(df_ndvi['dt'], unit = 's') #prebacio sam se iz unixts u normalan
df_ndvi=df_ndvi.loc[df_ndvi.name==option] #referenciram se na izbornik





#print(df_ndvi.dt)
line_chart3=alt.Chart(df_ndvi).mark_line().encode(
    x=alt.X('dt:T', axis=alt.Axis(title='Datum', format = ("%a %d"),tickMinStep=1.0,labelOverlap=True),scale=alt.Scale(domain=[str(df_ndvi.dt.min()), str(df_ndvi.dt.max())])),
    y=alt.Y('medianndvi',scale=alt.Scale(domain=[df_ndvi.medianndvi.min()-1, df_ndvi.medianndvi.max()+1]),axis=alt.Axis(title='NDVI')),
    color=alt.Color('name',legend=None),

)

line_chart3.configure_title(
    fontSize=20,
    font='Courier',
    anchor='start')

nearest = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['dt'], empty='none')

selectors = alt.Chart(df_ndvi).mark_point().encode(
    x='dt:T',
    opacity=alt.value(0),
).add_selection(
    nearest
)


points = line_chart3.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)


text = line_chart3.mark_text(align='left', dx=5, dy=-5).encode(
    text=alt.condition(nearest, 'medianndvi:Q', alt.value(' '))
)


rules = alt.Chart(df_ndvi).mark_rule(color='gray').encode(
    x='dt:T',
).transform_filter(
    nearest
)

#####SVI LAYERI U 1 GRAF
chart3 = alt.layer(
    line_chart3, selectors, points, rules, text
).configure(background='rgb(255,255,255,0.7)').configure_axis(
    grid=False
).configure_view(
    strokeOpacity=0).properties(
    width=1755,
    height=400
).configure_area(blend='screen')


col6, col7=st.beta_columns([1,2])

st.write('NDVI indeks')
st.altair_chart(chart3)
st.write('Temperatura tla na 0.1m')
st.altair_chart(chart)
st.write('Vlažnost tla na 0.1m')
st.altair_chart(chart2)


