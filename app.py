

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime
from pathlib import Path
import base64

st.set_page_config(
    page_title='Risk and PnL explorer',
    #page_icon='',
    #layout='wide',
    initial_sidebar_state='expanded'
)

# Turning off the SettingWithCopyWarning
pd.set_option('mode.chained_assignment', None)

# Overall heading for streamlit app
def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def header():

    header_html = "<img src='data:image/png;base64,{}' class='img-fluid max-width:100%'>".format(
        img_to_bytes("header1.png")
    )
    st.markdown(
        header_html, unsafe_allow_html=True,
    )
    st.text('')
    st.markdown('---')
    st.sidebar.title('Desk and limit selection')


@st.cache
def get_desk_data():
    desks = pd.read_csv("./data/desks.csv")
    return desks

@st.cache
def get_pnl_data():
    pnl_data = pd.read_csv("./data/pnl.csv")
    pnl_data['date'] = pd.to_datetime(pnl_data['date'], dayfirst=True)
    return pnl_data

@st.cache
def get_risk_data():
    risk_data = pd.read_csv("./data/risk.csv")
    risk_data['date'] = pd.to_datetime(risk_data['date'], dayfirst=True)
    return risk_data


def main():
    header()
    desk_data = get_desk_data()
    pnl_data = get_pnl_data()
    risk_data = get_risk_data()

    ac_list = desk_data['asset_class'].unique().tolist()

    ac_list.insert(0, 'All asset classes')
    
    dt = st.sidebar.date_input("Date range",
                                value=[datetime.date(2020, 1, 1), datetime.date(2020, 2, 1)],
                                min_value=datetime.date(2020,1,1),
                                max_value=datetime.date(2020,2,1)
                                )
    
    dtl = [dt[0]]
    if len(dt)==1:
        dtl.append(dt[0])
    elif len(dt)==2:
        dtl.append(dt[1])
    
    biz_selectbox = st.sidebar.selectbox("Asset class", ac_list)

    if biz_selectbox == 'All asset classes':
        office_select_list = desk_data['office'].unique().tolist()
    else:
        office_select_list = desk_data[(desk_data['asset_class']==biz_selectbox)]['office'].unique().tolist()
    
    office_select_list.sort()
    office_select_list.insert(0, 'All offices')
    office_selectbox = st.sidebar.selectbox("Office", office_select_list)

    if biz_selectbox == 'All asset classes':
        if office_selectbox  == 'All offices':
            desk_select_list = desk_data['desk_name'].unique().tolist()
        else:
            desk_select_list = desk_data[(desk_data['office']==office_selectbox)]['desk_name'].unique().tolist()
    else:
        if office_selectbox  == 'All offices':
            desk_select_list = desk_data[desk_data['asset_class']==biz_selectbox]['desk_name'].unique().tolist()
        else:
            desk_select_list = desk_data[(desk_data['asset_class']==biz_selectbox) & (desk_data['office']==office_selectbox)]['desk_name'].unique().tolist()

    desk_selectbox = st.sidebar.selectbox("Desk", desk_select_list)

    desk_head = desk_data[(desk_data['desk_name']==desk_selectbox)]['desk_head'].iloc[0]
    desk_no = desk_data[(desk_data['desk_name']==desk_selectbox)]['desk_no'].iloc[0]
    desk_office = desk_data[(desk_data['desk_name']==desk_selectbox)]['office'].iloc[0]
    desk_instruments = desk_data[(desk_data['desk_name']==desk_selectbox)]['instruments'].iloc[0]

    st.text('Desk: ' + desk_selectbox + ' | Desk head: ' + desk_head)
    st.text('Office: ' + desk_office + ' | Instruments: ' + desk_instruments)
    


    # Risk sub-chart


    risk_list = risk_data[ (risk_data['desk_no']==desk_no) & (risk_data['date']>=pd.to_datetime(dtl[0])) & (risk_data['date']<=pd.to_datetime(dtl[1]))]['risk_name'].unique().tolist()

    if len(risk_list) == 0:
        st.warning("No data for this desk and date range")
        return None
    else:
        risk_selectbox = st.sidebar.selectbox("Risk factor to display", risk_list)


    risk_df = risk_data[ (risk_data['desk_no']==desk_no) & (risk_data['risk_name']==risk_selectbox) & (risk_data['date']>=pd.to_datetime(dtl[0])) & (risk_data['date']<=pd.to_datetime(dtl[1])) ]

    
    st.subheader('Risk')

    risk_exposure = alt.Chart(risk_df, title=risk_selectbox).mark_bar().encode(
        x=alt.X('date', axis=alt.Axis(format='%Y-%m-%d', title='Date', labelAngle=-90)),
        y=alt.Y('exposure', axis=alt.Axis(title='Exposure (USD)')),
        tooltip = [alt.Tooltip(field = 'date', type = 'temporal', format='%Y-%m-%d'),
                   alt.Tooltip(field = 'exposure', title = str(risk_selectbox) + ' utilisation (USD)', type = 'quantitative', format=',')]
    ).interactive()

    risk_limit = alt.Chart(risk_df).mark_line(color='red').encode(x='date', y=alt.Y('limit')).interactive()

    st.altair_chart(risk_exposure + risk_limit, use_container_width=True)
    

    # PnL sub-charts

    st.subheader('PnL charts')

    pnl_df = pnl_data[(pnl_data['desk_no']==desk_no) & (pnl_data['date']>=pd.to_datetime(dtl[0])) & (pnl_data['date']<=pd.to_datetime(dtl[1])) ]

    list_to_drop_0 = ['desk_no', 'date', 'pnl_total', 'pnl_existing_pos', 'pnl_new_pos', 'pnl_resid',
                      'pnl_risk_factor_changes', 'pnl_cf', 'pnl_carry', 'pnl_val_adj', 'pnl_cna',
                      'pnl_rf_basis', 'pnl_rf_commodity', 'pnl_rf_correlation', 'pnl_rf_credit', 'pnl_rf_equity', 'pnl_rf_fx', 'pnl_rf_ir', 'pnl_rf_model', 'pnl_rf_other']


    # Total PnL Chart

    list_to_drop_total = ['desk_no', 'pnl_existing_pos', 'pnl_new_pos', 'pnl_resid',
                      'pnl_risk_factor_changes', 'pnl_cf', 'pnl_carry', 'pnl_val_adj', 'pnl_cna',
                      'pnl_rf_basis', 'pnl_rf_commodity', 'pnl_rf_correlation', 'pnl_rf_credit', 'pnl_rf_equity', 'pnl_rf_fx', 'pnl_rf_ir', 'pnl_rf_model', 'pnl_rf_other']

    pnl_df_total = pnl_df.drop(list_to_drop_total, axis=1)
    pnl_df_total.sort_values(by=['date'], inplace=True)

    pnl_total_chart = alt.Chart(pnl_df_total).mark_point(color='black', opacity=0.8, size=50, shape='stroke').encode(
        x=alt.X('date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('pnl_total'),
        color=alt.value('black'),
        opacity=alt.value(0.5)
    ).interactive()

    list_to_drop_enr = ['desk_no', 'pnl_total', 
                      'pnl_risk_factor_changes', 'pnl_cf', 'pnl_carry', 'pnl_val_adj', 'pnl_cna',
                      'pnl_rf_basis', 'pnl_rf_commodity', 'pnl_rf_correlation', 'pnl_rf_credit', 'pnl_rf_equity', 'pnl_rf_fx', 'pnl_rf_ir', 'pnl_rf_model', 'pnl_rf_other']

    pnl_df_enr = pnl_df.drop(list_to_drop_enr, axis=1)
    pnl_df_total.sort_values(by=['date'], inplace=True)

    pnl_enr_chart = alt.Chart(pnl_df_enr.melt('date', var_name='PnL type', value_name='PnL'), title = 'Total PnL (daily)').mark_bar().encode(
        x=alt.X('date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('PnL', axis=alt.Axis(title='PnL (USD)')),
        color=alt.Color('PnL type', legend=alt.Legend(orient="bottom"), scale=alt.Scale(scheme='dark2')),
    ).interactive()

    st.altair_chart(pnl_enr_chart + pnl_total_chart, use_container_width=True)


    # Existing position  PnL Chart

    list_to_drop_ep = ['desk_no', 'pnl_total', 'pnl_new_pos', 'pnl_resid',
                      'pnl_risk_factor_changes', 'pnl_cf', 'pnl_carry', 'pnl_val_adj', 'pnl_cna',
                      'pnl_rf_basis', 'pnl_rf_commodity', 'pnl_rf_correlation', 'pnl_rf_credit', 'pnl_rf_equity', 'pnl_rf_fx', 'pnl_rf_ir', 'pnl_rf_model', 'pnl_rf_other']

    pnl_df_ep = pnl_df.drop(list_to_drop_ep, axis=1)
    pnl_df_ep.sort_values(by=['date'], inplace=True)

    pnl_ep_chart = alt.Chart(pnl_df_ep).mark_point(color='black', opacity=0.8, size=50, shape='stroke').encode(
        x=alt.X('date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('pnl_existing_pos', axis=alt.Axis(title='PnL (USD)')),
        color=alt.value('black'),
        opacity=alt.value(0.5)
    ).interactive()

    list_to_drop_rccvc = ['desk_no', 'pnl_total', 'pnl_existing_pos', 'pnl_new_pos', 'pnl_resid',
                      'pnl_rf_basis', 'pnl_rf_commodity', 'pnl_rf_correlation', 'pnl_rf_credit', 'pnl_rf_equity', 'pnl_rf_fx', 'pnl_rf_ir', 'pnl_rf_model', 'pnl_rf_other']

    pnl_df_rccvc = pnl_df.drop(list_to_drop_rccvc, axis=1)
    pnl_df_rccvc.sort_values(by=['date'], inplace=True)

    pnl_rccvc_chart = alt.Chart(pnl_df_rccvc.melt('date', var_name='PnL type', value_name='PnL'), title = 'Existing positions PnL').mark_bar().encode(
        x=alt.X('date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('PnL', axis=alt.Axis(title='PnL (USD)')),
        color=alt.Color('PnL type', legend=alt.Legend(orient="bottom"), scale=alt.Scale(scheme='dark2')),
        tooltip = [alt.Tooltip(field = 'date', type = 'temporal', format='%Y-%m-%d'),
                   alt.Tooltip(field = 'PnL', title = 'PnL (USD)', type='quantitative', format=',d'),
                   alt.Tooltip(field = 'PnL type', type = 'nominal') ]
    ).interactive()

    st.altair_chart(pnl_ep_chart + pnl_rccvc_chart, use_container_width=True)


    # Risk factor PnL chart

    list_to_drop_rf = ['desk_no', 'pnl_total', 'pnl_existing_pos', 'pnl_new_pos', 'pnl_resid',
                      'pnl_risk_factor_changes', 'pnl_cf', 'pnl_carry', 'pnl_val_adj', 'pnl_cna',
                      ]

#  'pnl_rf_basis', 'pnl_rf_commodity', 'pnl_rf_correlation', 'pnl_rf_credit', 'pnl_rf_equity', 'pnl_rf_fx', 'pnl_rf_ir', 'pnl_rf_model', 'pnl_rf_other'

    pnl_df_rf = pnl_df.drop(list_to_drop_rf, axis=1)
    pnl_df_rf.sort_values(by=['date'], inplace=True)

    pnl_rf_chart = alt.Chart(pnl_df_rf.melt('date', var_name='PnL type', value_name='PnL'), title = 'Risk factor PnL').mark_bar().encode(
        x=alt.X('date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('PnL', axis=alt.Axis(title='PnL (USD)')),
        color=alt.Color('PnL type', legend=alt.Legend(orient="bottom"), scale=alt.Scale(scheme='dark2')),
        tooltip = [alt.Tooltip(field = 'date', type = 'temporal', format='%Y-%m-%d'),
                   alt.Tooltip(field = 'PnL', title = 'PnL (USD)', type='quantitative', format=',d'),
                   alt.Tooltip(field = 'PnL type', type = 'nominal') ]
    ).interactive()

    st.altair_chart(pnl_rf_chart, use_container_width=True)

    st.text('Desk data')
    st.write(desk_data)

    return None





if __name__ == "__main__":
    main()
