import streamlit as st
import json
import pandas as pd
from functools import reduce
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO
import dpi_module as dpi

import hmac

st.set_page_config(layout="wide")
st.title("Дашборд")

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Пароль для входа", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()  # Do not continue if check_password is not True.


file_name = "data_file/data_02.2024.xlsx"

@st.cache_data
def load_data(file, sheet):
    
    data = pd.read_excel(file_name, sheet_name=sheet)
    
    return data

path_to_json = "Structure"
structure_json = "structure.json"
structure = dpi.load_structure_data(path_to_json, structure_json)

box_1, box_2, box_3  = st.columns(3)

with box_1:
    department = st.multiselect("Укажите управление", structure.keys(), structure.keys(),  placeholder = "Управление")

master_list = []

for key in department:
    master_list.append(list(structure[key]["Studio"].keys()))

master_list = sum(master_list, [])

with box_2:
    master = st.multiselect("Укажите мастерскую", master_list, master_list,  placeholder = "Мастерская")

group_list =[]

for key in department:
    for key1 in structure[key]["Studio"]:
        group_list.append(structure[key]["Studio"][key1]["Group"])
group_list = sum(group_list, [])
group_list = list(set(group_list))

with box_3:
    group = st.multiselect("Укажите группу", group_list, group_list, placeholder = "Группа")

id_list = []

for key in department:
    id_list.append(structure[key]["ID"])


selected_date_range = st.slider("Укажите диапазон дат", dt.datetime(2023,1,1), dt.datetime(2023,12,31), (dt.datetime(2023,1,1), dt.datetime(2023,12,31)), format = "DD.MM.YYYY")

start_date = selected_date_range[0]
end_date = selected_date_range[1]

tabel_1, tabel_2, tabel_3, tabel_4 = st.tabs(["Готовность", "Качество", "Выработка", "Инициативы"])

with tabel_1:

    df_load = load_data(file_name, "P_RD")
    
    df_load = df_load[(df_load["Управление"].isin(id_list)) & (df_load["Мастерская"].isin(master)) & (df_load["Группа"].isin(group))]
    
    df_load_plan = df_load[(df_load["Срок выдачи (план)"] >= start_date) & (df_load["Срок выдачи (план)"] <= end_date)]
    
    df_group_plan = df_load_plan.groupby([pd.Grouper(key = "Срок выдачи (план)", freq="M")]).aggregate({"Кол-во комплектов (план)":"sum"}).reset_index()
    
    #df_group_plan = df_group_plan[df_group_plan["Срок выдачи (план)"].dt.strftime('%Y') == "2023"]
    
    df_load_fact = df_load[(df_load["Срок выдачи (факт)"] >= start_date) & (df_load["Срок выдачи (факт)"] <= end_date)]
    
    df_group_fact = df_load_fact.groupby([pd.Grouper(key = "Срок выдачи (факт)", freq="M")]).aggregate({"Кол-во комплектов (факт)":"sum"}).reset_index()

    df_group_fact["Кол-во комплектов (факт) YTD"] = df_group_fact["Кол-во комплектов (факт)"].cumsum()
    df_group_plan["Кол-во комплектов (план) YTD"] = df_group_plan["Кол-во комплектов (план)"].cumsum() 

    df_group_status = df_load.groupby([df_load["Срок выдачи (факт)"].dt.strftime("%Y-%m-1"), "Статус по выдаче"]).aggregate({"Кол-во комплектов (факт)":"sum"}).reset_index()

    figure_line = go.Figure()

    figure_line.add_trace(go.Scatter(x = df_group_plan["Срок выдачи (план)"], 
                                     y = df_group_plan["Кол-во комплектов (план)"], 
                                     text = df_group_plan["Кол-во комплектов (план)"],
                                     textposition = "top center",
                                     textfont_color="grey",
                                     name = "План", 
                                     mode = "lines + markers + text", 
                                     marker_color = "grey"))
    
    figure_line.add_trace(go.Scatter(x = df_group_plan["Срок выдачи (план)"], 
                                     y = df_group_plan["Кол-во комплектов (план) YTD"],
                                     text = df_group_plan["Кол-во комплектов (план) YTD"],
                                     textposition = "top center",
                                     textfont_color="grey", 
                                     name = "План YTD", 
                                     mode = "lines + markers + text", 
                                     marker_color = "grey"))

    figure_line.add_trace(go.Scatter(x = df_group_fact["Срок выдачи (факт)"], 
                                     y = df_group_fact["Кол-во комплектов (факт)"],
                                     text = df_group_fact["Кол-во комплектов (факт)"],
                                     textposition = "bottom center",
                                     textfont_color="#007FFF", 
                                     name = "Факт", 
                                     mode = "lines + markers + text", 
                                     marker_color = "#007FFF"))
    
    figure_line.add_trace(go.Scatter(x = df_group_fact["Срок выдачи (факт)"], 
                                     y = df_group_fact["Кол-во комплектов (факт) YTD"],
                                     text = df_group_fact["Кол-во комплектов (факт) YTD"],
                                     textposition = "bottom center",
                                     textfont_color="#007FFF",  
                                     name = "Факт YTD", 
                                     mode = "lines + markers + text", 
                                     marker_color = "#007FFF"))


    figure_line.update_layout(
                    
                    width=1200,
                    height=500,
                    xaxis_title='Месяц',
                    yaxis_title='Значение', 
                    legend_orientation="h",
                    legend=dict(x=.5, xanchor="center"),
                    margin=dict(l=0, r=0, t=0, b=0))
    
    d = df_load.groupby(["Статус по выдаче"], as_index=False).aggregate({"Кол-во комплектов (факт)":"sum"})
    
    fig_pie = px.pie(d, values='Кол-во комплектов (факт)', 
                     names='Статус по выдаче', hole=0.5, 
                     labels={'Category': 'Категория', 'Values': 'Значения'},
                     width = 500,
                     height = 500
                )
    
    st.markdown("## Статус по выдаче документации")
    
    data = df_load_fact.groupby("Мастерская").aggregate({"Кол-во комплектов (факт)":"sum"}).reset_index()

    col_box_1 = st.columns((7,3), gap = "medium")

    with col_box_1[0]:
        st.plotly_chart(figure_line)

    with col_box_1[1]:
        st.data_editor(data,
                       
    column_config={
        "Кол-во комплектов (факт)": st.column_config.ProgressColumn(
            "Выдано комплектов",
            format="%f",
            max_value = 1500),
        },
        hide_index=True,)

    df_group_fact["Месяц"] = df_group_fact["Срок выдачи (факт)"].dt.strftime('%B')

    fig_heatmap = px.imshow([df_group_fact['Кол-во комплектов (факт)']],
                labels=dict(color='Кол-во комплектов (факт)'),
                x=df_group_fact['Месяц'],
                y=['Кол-во комплектов (факт)'],
                width = 1500,
                height = 500,
                color_continuous_scale=["#d7eefe","#a1d4ff","#6db8ff","#3a99ff", "#0079fa"])
    
    st.plotly_chart(fig_heatmap)

    figure_status = px.bar(df_group_status, 
                           x = "Срок выдачи (факт)", 
                           y = "Кол-во комплектов (факт)", 
                           color="Статус по выдаче"
                           )

    figure_status.update_layout(
                    
                    width=1000,
                    height=500,
                    xaxis_title='Месяц',
                    yaxis_title='Значение', 
                    legend_orientation="h",
                    legend=dict(x=.5, xanchor="center"),
                    margin=dict(l=0, r=0, t=0, b=0))

    st.markdown("## Статус по выдаче комплектов с разрезе сроков")

    col_box = st.columns((6, 3), gap = "medium")

    with col_box[0]:
        st.plotly_chart(figure_status)

    with col_box[1]:
        st.plotly_chart(fig_pie)

    with st.expander("Исходные данные"):
        st.dataframe(df_load)

    st.page_link("https://docs.google.com/spreadsheets/d/1vNIN987Wc9XbFTSusPmLoicqsfgjuu_1Y8Y7t0b0Hyk/edit#gid=1152946667", label="Ссылка на данные", icon="💻")

with tabel_2:
    st.markdown("# Качество документации")

    df_izm = load_data(file_name, "IZM")

    df_izm = df_izm[(df_izm["Управление"].isin(id_list)) & (df_izm["Мастерская"].isin(master)) & (df_izm["Группа"].isin(group))]

    df_izm["Дата изменения (план)"] = pd.to_datetime(df_izm["Дата изменения (план)"])
    df_izm_group = df_izm.groupby([pd.Grouper(key = "Дата изменения (факт)", freq = "M")]).aggregate({"Кол-во листов по разделам":"sum"}).reset_index()
    df_sheet_group = df_load.groupby([pd.Grouper(key = "Срок выдачи (факт)", freq = "M")]).aggregate({"Кол-во листов":"sum"}).reset_index()
    df_izm_group = df_izm_group.rename(columns={"Дата изменения (факт)":"Дата"})
    df_sheet_group = df_sheet_group.rename(columns={"Срок выдачи (факт)":"Дата"})
    
    total_master_izm = df_sheet_group.merge(df_izm_group, how='outer')
    total_master_izm["% изм"] = total_master_izm["Кол-во листов по разделам"] / total_master_izm["Кол-во листов"]
    total_master_izm = total_master_izm.fillna(0)
    total_master_izm = total_master_izm.replace({np.inf:0})

    figure_izm_status = px.bar(total_master_izm, 
                           x = "Дата", 
                           y = ["Кол-во листов", "Кол-во листов по разделам"]
                           )

    figure_izm_status.update_layout(
                    
                    width=1500,
                    height=500,
                    xaxis_title='Месяц',
                    yaxis_title='Значение', 
                    legend_orientation="h",
                    legend=dict(x=.5, xanchor="center"),
                    margin=dict(l=0, r=0, t=0, b=0))
    
    total_master_izm["Месяц"] = total_master_izm["Дата"].dt.strftime('%B')

    figure_izm_heatmape = px.imshow([total_master_izm['% изм']],
                labels=dict(color='% изм'),
                x=total_master_izm['Месяц'],
                y=['% изм'],
                width = 1700,
                height = 300,
                color_continuous_scale=["#d7eefe","#a1d4ff","#6db8ff","#3a99ff", "#0079fa"])


    st.plotly_chart(figure_izm_status)
    st.plotly_chart(figure_izm_heatmape)

    with st.expander("Исходные данные"):
        st.dataframe(total_master_izm)

    st.page_link("https://docs.google.com/spreadsheets/d/1vNIN987Wc9XbFTSusPmLoicqsfgjuu_1Y8Y7t0b0Hyk/edit#gid=1152946667", label="Ссылка на данные", icon="💻")

    
with tabel_3:
    st.markdown("# Выработка")

    df_productivity = load_data(file_name, "Productivity")

    df_productivity_group = df_productivity.groupby([pd.Grouper(key = "Дата", freq="M"), "План/Факт"]).aggregate({"Значение":"sum"}).unstack("План/Факт").reset_index()
    df_productivity_group.columns = df_productivity_group.columns.map(''.join)
    df_productivity_group = df_productivity_group.rename(columns={"ЗначениеПлан":"План", 
                                                                  "ЗначениеФакт":"Факт"})

    figure_productivity_line = go.Figure()
    
    figure_productivity_line.add_trace(go.Scatter(x = df_productivity_group["Дата"], 
                                     y = df_productivity_group["Факт"], 
                                     name = "Факт",
                                     marker_color = "#007FFF"))
    
    
    figure_productivity_line.add_trace(go.Scatter(x = df_productivity_group["Дата"], 
                                     y = df_productivity_group["План"], 
                                     name = "План",  
                                     marker_color = "grey"))
    
    figure_productivity_line.update_layout(
                    width=1500,
                    height=500,
                    xaxis_title='Месяц',
                    yaxis_title='Значение', 
                    legend_orientation="h",
                    legend=dict(x=.5, xanchor="center"),
                    margin=dict(l=0, r=0, t=0, b=0))

    st.plotly_chart(figure_productivity_line)

    
    with st.expander("Исходные данные"):
        st.dataframe(df_productivity)

    st.page_link("https://docs.google.com/spreadsheets/d/1l5Y-4o2l6WW-RMbVOrj5rKfwd4QPVwZYrKeGZlJywzk/edit#gid=1418497325", label="Ссылка на данные", icon="💻")