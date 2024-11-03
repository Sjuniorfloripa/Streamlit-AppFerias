import streamlit as st
import pandas as pd
import json

from crud_bd_usuarios import le_todos_usuarios, cria_usuarios, modifica_usuario, deleta_usuario
from time import sleep
from streamlit_calendar import calendar
from datetime import datetime

st.set_page_config(
    page_title='App Férias',
    layout='wide'
)

def login():
    usuarios = le_todos_usuarios()
    usuarios = {usuario.nome: usuario for usuario in usuarios}
    with st.container(border=True):
        st.markdown('Bem vindo ao AppFérias')
        nome_usuario = st.selectbox('Selecione seu Usuário', usuarios.keys())
        senha = st.text_input('Digite sua senha', type='password')
        if st.button('Login'):
            usuario = usuarios[nome_usuario]
            if usuario.verifica_senha(senha):
                st.success('Logado com sucesso')
                st.session_state['logado'] = True
                st.session_state['usuario'] = usuario
                sleep(1)
                st.rerun()
            else:
                st.error('Senha e/ou usuário incorreto.')

def tab_gestao_page():
    with st.sidebar:
        tab_gestao_usuario()

    usuarios = le_todos_usuarios()
    
    for usuario in usuarios:
        with st.container(border=True):
            cols = st.columns(2)
            dias_para_solicitar = usuario.dias_para_solicitar()
            
            with cols[0]:
                if dias_para_solicitar >= 40:
                    st.warning(f'### {usuario.nome}')
                else:
                    st.markdown(f'### {usuario.nome}')
            with cols[1]:
                if dias_para_solicitar >= 40:
                    st.warning(f'### Dias para solicitar: {dias_para_solicitar}')    
                else:
                    st.markdown(f'### Dias para solicitar: {dias_para_solicitar}')

def tab_gestao_usuario():
    if 'tab_selecionada' not in st.session_state:
        st.session_state['tab_selecionada'] = 'Visualizar'

    tab_vis, tab_cria, tab_mod, tab_del = st.tabs(['Visualizar', 'Criar', 'Modificar', 'Deletar'])
    usuarios = le_todos_usuarios()

    with tab_vis:
        data_usuarios = [{
            'id': usuario.id,
            'nome': usuario.nome,
            'email': usuario.email,
            'acesso_gestor': usuario.acesso_gestor,
            'inicio_na_empresa': usuario.inicio_na_empresa
        } for usuario in usuarios]
        st.dataframe(pd.DataFrame(data_usuarios).set_index('id'))

    with tab_cria:
        nome = st.text_input('Nome do Usuário')
        senha = st.text_input('Senha do Usuário', type='password')
        email = st.text_input('Email do Usuário')
        acesso_gestor = st.checkbox('Tem acesso de gestor?')
        inicio_na_empresa = st.text_input('Data de início na empresa (formato AAAA-MM-DD)')
        if st.button('Criar'):
            cria_usuarios(nome=nome, 
                        senha=senha,
                        email=email, 
                        acesso_gestor=acesso_gestor, 
                        inicio_na_empresa=inicio_na_empresa
                    )
            st.success("Usuário criado com sucesso!")
            st.session_state['tab_selecionada'] = 'Visualizar'
            st.rerun()

    with tab_mod:
        usuarios_dict = {usuario.nome: usuario for usuario in usuarios}
        nome_usuario = st.selectbox('Selecione o usuário para atualizar', usuarios_dict.keys())
        usuario = usuarios_dict[nome_usuario]
        nome = st.text_input('Nome do Usuário', value=usuario.nome)
        senha = st.text_input('Senha do Usuário', value='xxxxxx')
        email = st.text_input('Email do Usuário', value=usuario.email)
        acesso_gestor = st.checkbox('Modificar acesso de gestor?', value=usuario.acesso_gestor)
        inicio_na_empresa = st.text_input('Data de início na empresa (formato AAAA-MM-DD)', value=usuario.inicio_na_empresa)
        if st.button('Atualizar'):
            if senha == 'xxxxxx':
                modifica_usuario(
                    id=usuario.id,
                    nome=nome,
                    email=email,
                    acesso_gestor=acesso_gestor,
                    inicio_na_empresa=inicio_na_empresa
                )
                st.success("Usuário atualizado com sucesso!")
                st.session_state['tab_selecionada'] = 'Visualizar'
                st.rerun()
            else:
                modifica_usuario(
                    id=usuario.id,
                    nome=nome,
                    senha=senha,
                    email=email,
                    acesso_gestor=acesso_gestor,
                    inicio_na_empresa=inicio_na_empresa
                )
            st.success("Usuário atualizado com sucesso!")
            st.session_state['tab_selecionada'] = 'Visualizar'
            st.rerun()

    with tab_del:
        usuarios_dict = {usuario.nome: usuario for usuario in usuarios}
        nome_usuario = st.selectbox('selecione um usuário para deletar', usuarios_dict.keys())
        usuario = usuarios_dict[nome_usuario]
        if st.button('Deletar'):
            deleta_usuario(usuario.id)
            st.success("Usuário atualizado com sucesso!")
            st.session_state['tab_selecionada'] = 'Visualizar'
            st.rerun()

def verifica_e_adiciona_ferias(data_inicio, data_fim):
    usuario = st.session_state['usuario']
    dias_para_solicitar = usuario.dias_para_solicitar()
    
    total_dias = (datetime.strptime(data_fim, '%Y-%m-%d') - datetime.strptime(data_inicio, '%Y-%m-%d')).days + 1
    if total_dias < 5:
        st.error('Quantidade de dias inferior a 5')

    elif dias_para_solicitar < total_dias:
        st.error(f'Usuário solicitou {total_dias} mas tem apenas {dias_para_solicitar} para solicitar')
    
    else:
        usuario.adiciona_ferias(data_inicio, data_fim)
        limpar_datas()

def limpar_datas():
    del st.session_state['data_final']
    del st.session_state['data_inicio']

def calendar_page():

    usuarios = le_todos_usuarios() 

    with open("calendar_options.json", "r", encoding="utf-8") as f:
        calendar_options = json.load(f)


    calendar_events = []
    for usuario in usuarios:
        calendar_events.extend(usuario.lista_ferias())
    
    usuario = st.session_state['usuario']

    with st.expander('Dias para solicitar'):
        dias_para_solicitar = usuario.dias_para_solicitar()
        st.markdown(f'O usuário {usuario.nome} possui **{dias_para_solicitar}** dias para solicitar')

    calendar_widget = calendar(events=calendar_events, options=calendar_options)
    if 'callback' in calendar_widget and calendar_widget['callback'] == 'dateClick':
        
        raw_date = calendar_widget['dateClick']['date']
        
        if raw_date != st.session_state['ultimo_clique']:
            st.session_state['ultimo_clique'] = raw_date
            
            date = calendar_widget['dateClick']['date'].split('T')[0]
            if not 'data_inicio' in st.session_state:
                st.session_state['data_inicio'] = date
                st.warning(f'Data de início de férias selecionada {date}')
            else:
                st.session_state['data_final'] = date
                date_inicio = st.session_state['data_inicio']

                cols = st.columns([0.7, 0.3])

                with cols[0]:
                    st.warning(f'Data de início de férias selecionada {date_inicio}.')
                with cols[1]:
                    st.button('Limpar', use_container_width=True, on_click=limpar_datas())

                cols = st.columns([0.7, 0.3])
                
                with cols[0]:
                    st.warning(f'Data final de férias selecionada {date}')
                with cols[1]:
                    st.button('Adicionar Férias', 
                              use_container_width=True,
                              on_click=verifica_e_adiciona_ferias,
                              args=(date_inicio, date)
                            )

def pagina_principal():
    usuario_logado = st.session_state['usuario']
    st.title(f'Bem-vindo ao App Férias {usuario_logado.nome}!')
    st.divider()
    
    
    if usuario_logado.acesso_gestor:
        cols = st.columns(4)
        with cols[0]:
            if st.button('Acessar Gestão de Usuários', use_container_width=True):
                st.session_state['pag_gestao_usuarios'] = True
                st.rerun()
        with cols[1]:
            if st.button('Acessar Calendário', use_container_width=True):
                st.session_state['pag_gestao_usuarios'] = False
                st.rerun()
    
    if st.session_state['pag_gestao_usuarios']:
        tab_gestao_page()
    else:
        calendar_page()

def main():
    if not 'logado' in st.session_state:
        st.session_state['logado'] = False
    if not 'pag_gestao_usuarios' in st.session_state:
        st.session_state['pag_gestao_usuarios'] = False
    if not 'ultimo_clique' in st.session_state:
        st.session_state['ultimo_clique'] =''
    if not st.session_state['logado']:
        login()
    else:
        pagina_principal()

if __name__ == '__main__':
    main()
