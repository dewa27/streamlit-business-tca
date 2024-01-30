# Data Source: https://public.tableau.com/app/profile/federal.trade.commission/viz/FraudandIDTheftMaps/AllReportsbyState
# US State Boundaries: https://public.opendatasoft.com/explore/dataset/us-state-boundaries/export/

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium,folium_static
import geopandas as gpd
from branca.element import MacroElement
from jinja2 import Template
import numpy as np

class BindColormap(MacroElement):
    """Binds a colormap to a given layer.

    Parameters
    ----------
    colormap : branca.colormap.ColorMap
        The colormap to bind.
    """
    def __init__(self, layer, colormap):
        super(BindColormap, self).__init__()
        self.layer = layer
        self.colormap = colormap
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
            {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
            {{this._parent.get_name()}}.on('layeradd', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                }});
            {{this._parent.get_name()}}.on('layerremove', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                }});
        {% endmacro %}
        """) 
APP_TITLE = 'Timedoor Academy Business Analyzer'
# APP_SUB_TITLE = '== Expansion Team =='
# state_name=""
# def display_time_filters(df):
#     year_list = list(df['Year'].unique())
#     year_list.sort()
#     year = st.sidebar.selectbox('Year', year_list, len(year_list)-1)
#     quarter = st.sidebar.radio('Quarter', [1, 2, 3, 4])
#     st.header(f'{year} Q{quarter}')
#     return year, quarter

# def display_state_filter(df, state_name):
#     state_list = [''] + list(df['State Name'].unique())
#     state_list.sort()
#     state_index = state_list.index(state_name) if state_name and state_name in state_list else 0
#     return st.sidebar.selectbox('State', state_list, state_index)

# def display_report_type_filter():
#     return st.sidebar.radio('Report Type', ['Fraud', 'Other'])


def display_map(df_choropleth,df_district_jkt_geojson):
    map = folium.Map(location=[-6.206867,106.8248906], zoom_start=11, tiles='CartoDB positron')
    cp2= folium.Choropleth(
        geo_data=df_district_jkt_geojson,
        name="choropleth",
        data=df_choropleth,
        columns=["district", "jumlah_siswa"],
        key_on="feature.properties.district",
        fill_color="Greens",
        fill_opacity=0.3,
        line_opacity=0.5,
        legend_name="Jumlah Siswa Aktif",
    )
    fg1 = folium.FeatureGroup(name='Active Students Data By Kecamatan',show=True,overlay=True).add_to(map)
    # cp2_colormap=cp2.color_scale
    cp2=cp2.geojson.add_to(fg1)
    # my_map2
    # map.add_child(cp2_colormap)
    # map.add_child(BindColormap(fg1, cp2_colormap))
    popup = folium.GeoJsonPopup(fields=["district", 'active', 'inactive', 'jumlah_siswa'],aliases=["Kecamatan: ", "Siswa Aktif: ", "Siswa Nonaktif: ", 'jumlah_siswa:   '])
    tooltip=folium.features.GeoJsonTooltip(
                        fields=['district'],
                        aliases=["Kecamatan: "],
                        localize=True,
                        sticky=False,
                        labels=True,
                        style="""
                            background-color: #F0EFEF;
                            border: 2px solid black;
                            border-radius: 3px;
                            box-shadow: 3px;
                        """,
                        max_width=600)
    folium.features.GeoJson(
        zoom_on_click=True,
        data=df_choropleth,
        name='Jumlah Siswa di Jakarta',
        smooth_factor=2,
        style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
        popup=popup,
        tooltip=tooltip,
        highlight_function=lambda x: {'weight':2,'color':'yellow'},
    ).add_to(cp2)
    

    with st.form(key="smth"):
        state_name=''
        kabkot_name=''
        col1,col2=st.columns([3,2])
        with col1:
            st_map = st_folium(map,width=900,height=500)
        with col2:
            tuts_expander = st.expander("How to Use",expanded=True)
            with tuts_expander:
                st.markdown('''
                            - Search the district that you want
                            - Click the area of the district
                            - Once the pop up shown, Click on ***Generate Data***
                            - Hide this menu if you already understand :green_heart::green_heart:''')
            
            submitted = st.form_submit_button("Generate Data")
            if submitted:
                st.write(st_map['last_active_drawing']['properties'])
                state_name=st_map['last_active_drawing']['properties']['district']
                kabkot_name=st_map['last_active_drawing']['properties']['regency']
                return state_name, kabkot_name
    
    return state_name, kabkot_name

def display_fraud_facts(df, year, quarter, report_type, state_name, field, title, string_format='${:,}', is_median=False):
    df = df[(df['Year'] == year) & (df['Quarter'] == quarter)]
    df = df[df['Report Type'] == report_type]
    if state_name:
        df = df[df['State Name'] == state_name]
    df.drop_duplicates(inplace=True)
    if is_median:
        total = df[field].sum() / len(df[field]) if len(df) else 0
    else:
        total = df[field].sum()
    st.metric(title, string_format.format(round(total)))


def display_metrics(df_metrics,district_name,kabkot_name):
    # df_kabkot=df_metrics[df_metrics['regency']==kabkot_name]
    df_kabkot=df_metrics.query('regency == @kabkot_name')
    kabkot_total=df_kabkot['jumlah_siswa'].sum()
    df_kabkot_notfounddistrict=df_kabkot[df_kabkot['standardized_district']=='Not Found']
    # df_district=df_kabkot[df_kabkot['standardized_district']==district_name]
    df_district=df_kabkot.query('standardized_district == @district_name')
    df_district=df_district[['subdistrict','branch_name','active','inactive','jumlah_siswa']].sort_values('active',ascending=False)
    df_district=df_district.reset_index(drop=True)
    col1,col2,col3 = st.columns(3)
    with col1:
        st.metric(label="Active Students", value=df_district['active'].sum())
    with col2:
        st.metric(label="Inactive Students", value=df_district['inactive'].sum())
    with col3:
        st.metric(label="Total Students", value=df_district['jumlah_siswa'].sum())
    st.markdown(f'''
                <h5>{df_district['jumlah_siswa'].sum()} siswa tinggal di {district_name}, dari {kabkot_total} siswa di {kabkot_name} <h5>
                ''',unsafe_allow_html=True)
    with st.expander("Lihat Detail per Branch dan Kelurahan"):
        st.table(df_district)

def main():
    st.set_page_config(APP_TITLE,layout='wide')
    st.title(APP_TITLE)

    #Load Data
    df_jkt_geojson= gpd.read_file(r'data/jakarta_formatted.geojson')
    df_jkt_metrics=pd.read_excel("data/jakarta_metrics_data.xlsx",index_col=0)
    df_jkt_choropleth=pd.read_excel("data/choropleth_jakarta2.xlsx")
    df_jabodetabek= gpd.read_file(r'data/jabodetabek_formatted.geojson')
    df_jabodetabek_metrics=pd.read_excel("data/jabodetabek_metrics_data.xlsx",index_col=0)
    df_jabodetabek_choropleth=pd.read_excel("data/choropleth_jabodetabek.xlsx")
    # df_mix_geojson=gpd.GeoDataFrame(pd.concat([df_jkt_geojson,df_jabar_geojson], ignore_index=True) )
    # df_mix_metrics=pd.concat([df_jkt_metrics, df_jabar_metrics])
    # df_mix_choropleth=pd.concat([df_jkt_choropleth, df_jabar_choropleth])
    # st.dataframe(df_mix_choropleth)
    df_jabodetabek_choropleth= df_jabodetabek.merge(df_jabodetabek_choropleth, left_on=["district","regency"], right_on=["sync_name","regency"], how="outer") 
    df_jabodetabek_choropleth=df_jabodetabek_choropleth[['district','regency','geometry','active','inactive','jumlah_siswa']]
    df_jabodetabek_choropleth=df_jabodetabek_choropleth.replace('nan', np.nan).fillna(0)
    
    df_jkt_choropleth= df_jkt_geojson.merge(df_jkt_choropleth, left_on=["district","regency"], right_on=["sync_name","regency"], how="outer") 
    df_jkt_choropleth=df_jkt_choropleth[['district','regency','geometry','active','inactive','jumlah_siswa']]
    df_jkt_choropleth=df_jkt_choropleth.replace('nan', np.nan).fillna(0)

    option= st.selectbox('Pilih daerah yang ingin dilihat',('Jakarta', 'Jabodetabek', 'Jawa Barat','Surabaya'))
    st.session_state.selected_area=option
    if 'selected_area' not in st.session_state:
        st.session_state.selected_area = 'Jakarta'
        df_selected_metrics=df_jkt_metrics

    if st.session_state.selected_area == 'Jakarta':
        district_name,kabkot_name=display_map(df_jkt_choropleth,df_jkt_geojson)
        df_selected_metrics=df_jkt_metrics
    elif st.session_state.selected_area == 'Jabodetabek':
        district_name,kabkot_name=display_map(df_jabodetabek_choropleth,df_jabodetabek)
        df_selected_metrics=df_jabodetabek_metrics

    # Display Metrics
    if(not district_name=='' and not kabkot_name==''):
        st.subheader(f'{district_name} in {kabkot_name}  Facts')
        display_metrics(df_selected_metrics,district_name,kabkot_name)

    # st.dataframe(df_mix_metrics)

    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     display_fraud_facts(df_fraud, year, quarter, report_type, state_name, 'State Fraud/Other Count', f'# of {report_type} Reports', string_format='{:,}')
    # with col2:
    #     display_fraud_facts(df_median, year, quarter, report_type, state_name, 'Overall Median Losses Qtr', 'Median $ Loss', is_median=True)
    # with col3:
    #     display_fraud_facts(df_loss, year, quarter, report_type, state_name, 'Total Losses', 'Total $ Loss')        
    st.markdown('''Made with Love :green_heart: :green_heart:  __Expansion Team__ :green_heart: :green_heart:''')

if __name__ == "__main__":
    main()