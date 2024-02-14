import streamlit as st
import dpi_module as dpi
import datetime as dt
from dateutil import relativedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import hmac

st.set_page_config(layout="wide")

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



@st.cache_data
def load_data(file_name, sheet_name):
    
    data = pd.read_excel(file_name, sheet_name)
    
    return data


file_name = "data_file/data_02.2024.xlsx"
df_load = load_data(file_name, "P_RD")
df_izm = load_data(file_name, "IZM")
df_productivity = load_data(file_name, "Productivity")

# Выдача документации
def load_status(data, departament_filter, master_filter, group_filter, start_period, end_period):
    
    data = data[(data["Управление"] == departament_filter) & (data["Мастерская"] == master_filter) & (data["Группа"] == group_filter) &\
                ((data["Срок выдачи (факт)"] >= pd.to_datetime(str(start_period))) & (data["Срок выдачи (факт)"] <= pd.to_datetime(str(end_period))))]
    
    
    num_sheet = data["Кол-во листов"].sum()
    load_df = data.groupby("Статус по выдаче", as_index = False).aggregate({"Кол-во комплектов (факт)":"sum"})
    
    time_load      = load_df[load_df["Статус по выдаче"] == "в срок"]["Кол-во комплектов (факт)"].sum()
    time_less_load = load_df[load_df["Статус по выдаче"] == "с задержкой (<14 дней)"]["Кол-во комплектов (факт)"].sum()
    time_more_load = load_df[load_df["Статус по выдаче"] == "с задержкой (>14 дней)"]["Кол-во комплектов (факт)"].sum()
    
    percent_load = (time_load / (load_df["Кол-во комплектов (факт)"].sum()))
    
    if len(load_df) == 0:
        percent_load = 0
    else:
        if time_more_load != 0 or percent_load < 0.8:
            prize_to_load = 0
        elif percent_load >= 0.8 and percent_load < 1:
            prize_to_load = percent_load
        elif percent_load == 1:
            prize_to_load = 0.35

    return prize_to_load, num_sheet
    
# Качество документации
def izm_status(data, departament_filter, master_filter, group_filter, start_period, end_period, num_sheet):

    data = data[(data["Управление"] == departament_filter) & (data["Мастерская"] == master_filter) & (data["Группа"] == group_filter) &\
                ((data["Дата изменения (факт)"] >= pd.to_datetime(str(start_period))) & (data["Дата изменения (факт)"] <= pd.to_datetime(str(end_period))))]

    num_sheet_izm = data["Кол-во листов по разделам"].sum()
    
    percent = num_sheet_izm/num_sheet
    
    if percent == 0:
        prize_to_izm = 1.2
    elif percent >= 0.000001 and percent <= 0.000299:
        prize_to_izm = 1.0
    else:
        prize_to_izm = 0
    
    return prize_to_izm

# Выработка
def productivity_status(data, departament_filter, master_filter, group_filter, start_period, end_period):
    
    data = data[(data["Управление"] == departament_filter) & (data["Мастерская"] == master_filter) & (data["Группа"] == group_filter) &\
                ((data["Дата"] >= pd.to_datetime(str(start_period))) & (data["Дата"] <= pd.to_datetime(str(end_period))))]
    
    productivity_plan = data[data["План/Факт"] == "План"]["Значение"].sum()
    productivity_fact = data[data["План/Факт"] == "Факт"]["Значение"].sum()
    percent_productivity = (productivity_fact / productivity_plan)

    if len(data) == 0:
        prize_to_productivity = 0
    else:
        if percent_productivity < 0.7:
            prize_to_productivity = 0
        elif percent_productivity >= 0.7 and percent_productivity <= 1.2:
            prize_to_productivity = percent_productivity
        elif percent_productivity > 1.2:
            prize_to_productivity = 1.2

    return prize_to_productivity

def setting_set(number_of_periods):
    
    total_salary = []
    total_prize_for_period = []
    total_bonus = []
    
    data_salary_total = []


    for i in range(number_of_periods):
        
        st.markdown(f"## {i + 1}-й период")
        data_box = st.columns((3, 6, 6), gap = "medium")
        data_salary = []

        with data_box[0]:
            department = st.selectbox(f"Укажите управление для {i+1}-го периода работы", structure.keys(),  placeholder = "Управление")
            master = st.selectbox(f"Укажите мастерскую для {i+1}-го периода работы", structure[department]["Studio"].keys(), placeholder = "Мастерская")
            group = st.selectbox(f"Укажите группу для {i+1}-го периода работы", structure[department]["Studio"][master]["Group"])
            position = st.selectbox(f"Укажите должность для {i+1}-го периода работы", structure[department]["Position"])
            greid = st.selectbox(f"Укажите грейд для {i+1}-го периода работы", greid_level.keys())
            start_period = st.date_input(f"Укажите дату начала работы на должности для {i+1}-го периода работы", dt.datetime(2023,1,1), format="DD.MM.YYYY")
            end_period = st.date_input(f"Укажите дату начала работы на должности для {i+1}-го периода работы", dt.datetime(2023,12,31), format="DD.MM.YYYY")
            salary= st.number_input(f"Укажите ежемесячный размер заработной платы для {i+1}-го периода работы", value=100000, placeholder="Зарплата в рублях")

        delta = end_period - start_period
        salary_for_period = round((salary / 29.3) * (delta.days + 1))
        salary_to_greid_level = round(greid_level[greid] * salary_for_period)
        
        id_department = structure[department]["ID"]
        
        prize_to_load, num_sheet = load_status(df_load, id_department, master, group, start_period, end_period)
        prize_to_izm = izm_status(df_izm, id_department, master, group, start_period, end_period, num_sheet)
        prize_to_productivity = productivity_status(df_productivity, id_department, master, group, start_period, end_period)

        salary_to_load = round(prize_to_load * salary_to_greid_level * 0.35)
        salary_to_izm = round(prize_to_izm * salary_to_greid_level * 0.35)
        salary_to_productivity = round(prize_to_productivity * salary_to_greid_level * 0.2)
        
        #data_salary.append(salary_for_period)
        
        total = salary_to_load + salary_to_izm + salary_to_productivity
        
        data_salary.append(total)
        data_salary.append(salary_to_load)
        data_salary.append(salary_to_izm)
        data_salary.append(salary_to_productivity)
        data_salary.append(salary_to_greid_level)
        
        #total = round(np.sum(data_salary[1:]))
                
        waterfall_salary = go.Figure()

        waterfall_salary.add_trace(go.Waterfall(
            name = "Премия", 
            orientation = "h",
            measure = ["relative", "relative", "relative", "relative", "total"],
            x = data_salary,
            textposition = "inside",
            y = [ "Итого премия", "Выдача документации", "Качество документации", "Выработка", "Зарплата за период (c учетом грейда)"],
            text = data_salary,
            connector = {"mode":"between","line":{"width":0.5, "color":"rgb(255, 255, 255)", "dash":"solid"}},
            textfont=dict(size=16)))
        
        waterfall_salary.update_layout(
            width=700,
            height=700,
            showlegend = True)
        
        data_salary_pie = data_salary[1:4] 
        labels = ["Выдача документации", "Качество документации", "Выработка"]

        salary_pie = go.Figure(data = [go.Pie(labels = labels, values = data_salary_pie, hole = 0.5, pull = [0.02, 0.02, 0.02])])
        salary_pie.update_layout(
            width=800,
            height=700,
            legend=dict(orientation='h', y=1.2, yanchor='top', x=0.5, xanchor='center'))
        
        with data_box[1]:
            st.markdown("## Состав премии")
            st.plotly_chart(salary_pie)

        with data_box[2]:
            st.markdown("## Расчет премии")       
            st.plotly_chart(waterfall_salary)
            #st.write(data_salary)

st.subheader("Укажите был ли перевод за отчетный период")

path_to_json = "Structure"
structure_json = "structure.json"
greid_level_json = "greid_level.json"

structure = dpi.load_structure_data(path_to_json, structure_json)
greid_level  = dpi.load_structure_data(path_to_json, greid_level_json)

on = st.toggle("Укажите был ли перевод за отчетный период")

if on:
    number_of_periods = st.slider('Укажите колличество переводов', min_value=0, max_value=5, value=0) 
    setting_set(number_of_periods+1)   
else:
    setting_set(1)