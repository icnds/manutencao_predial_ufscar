import streamlit as st

st.set_page_config(
    page_title='UFSCar',
    page_icon=':mortar_board:'
)

st.write("# Manutenção Predial UFSCar")

st.markdown(
    """
    A Coordenadoria de Manutenção e Infraestrutura (CMan) é responsável pelo 
    gerenciamento dos recursos de manutenção predial no campus São Carlos da 
    Universidade Federal de São Carlos ([UFSCar](https://www.ufscar.br/)).
"""
)

st.page_link('pages/1_Categorias.py', label='Categorias', icon='1️⃣')
st.page_link('pages/2_Tabelas.py', label='Tabelas', icon='2️⃣')
st.page_link('pages/3_Rankings.py', label='Rankings', icon='3️⃣')
