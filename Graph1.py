## importa bibliotecas úteis para o sistema
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

##definição da função para uma das abas da página principal, nesta função optamos por calcular médias de tempo de internação por infecções causadas por microorganismos
##as médias são dadas pelas datas de admissão e datas de alta, desconsiderando internações que não possuem datas de alta, mas optamos por manter na visualização internações
##menores do que 1 dia, que são visualizadas como 0 nos gráficos e dataframe.
def graph1():
    st.header("Tempo Médio de Internação por Microorganismo")

    ##separação das colunas para melhor visualização da página
    col1, col2, col3 = st.columns([1, 1, 2])
    
    ##carrega os dados do CSV
    url = "https://raw.githubusercontent.com/AndersonEduardo/pbl-2023/main/sample_data_clean.csv"
    df = pd.read_csv(url)

    ##converte os valores de data e hora do dataset para valores de interpretação facilitada
    df['dh_admissao_paciente'] = pd.to_datetime(df['dh_admissao_paciente'])
    df['dh_alta_paciente'] = pd.to_datetime(df['dh_alta_paciente'])
    
    ##botões para seleção de período
    periodo_opcao = col1.radio("4- Selecione o período:", ["30 dias", "90 dias", "6 meses", "1 ano", "Período completo"])
    
    ##calcula o período correspondente aos botões citados
    if periodo_opcao == "30 dias":
        data_maxima = df['dh_admissao_paciente'].max().date()
        data_inicial = data_maxima - pd.DateOffset(days=30)
    elif periodo_opcao == "90 dias":
        data_maxima = df['dh_admissao_paciente'].max().date()
        data_inicial = data_maxima - pd.DateOffset(days=90)
    elif periodo_opcao == "6 meses":
        data_maxima = df['dh_admissao_paciente'].max().date()
        data_inicial = data_maxima - pd.DateOffset(months=6)
    elif periodo_opcao == "1 ano":
        data_maxima = df['dh_admissao_paciente'].max().date()
        data_inicial = data_maxima - pd.DateOffset(years=1)
    else:  # Período completo
        data_inicial = df['dh_admissao_paciente'].min().date()
        data_maxima = df['dh_admissao_paciente'].max().date()
    
    ##adiciona filtro de período personalizado
    filtro_periodo = col1.date_input('4- Selecione o período:', [data_inicial, data_maxima])
    
    ##converte os filtros de período para numpy.datetime64, para posterior ajuste de valores de média em gráficos
    filtro_periodo = [np.datetime64(date) for date in filtro_periodo]

    ##caixa de multiseleção para selecionar os organismos a serem analisados
    microorganismos_selecionados = col2.multiselect('4- Selecione os microorganismos:', df['cd_sigla_microorganismo'].unique())
    
    ##calcula o tempo de internação em dias
    df['tempo_internacao_dias'] = (df['dh_alta_paciente'] - df['dh_admissao_paciente']).dt.days
    
    ##aplica os filtros desejados pelo usuário
    df_filtrado = df[(df['dh_admissao_paciente'] >= filtro_periodo[0]) & (df['dh_admissao_paciente'] <= filtro_periodo[1])]
    if microorganismos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['cd_sigla_microorganismo'].isin(microorganismos_selecionados)]
    
    ##verifica se há dados para o período selecionado
    if not df_filtrado.empty:
        
        #cria um gráfico para o período selecionado usando a biblioteca Altair
        chart = alt.Chart(df_filtrado).mark_line().encode(
            x=alt.X('dh_admissao_paciente:T', title='Data de Admissão'),
            y=alt.Y('tempo_internacao_dias:Q', title='Média Tempo de Internação'),
            color=alt.Color('cd_sigla_microorganismo:N', title='Microorganismo')
        ).properties(
            width=400,
            height=200
        )
    
        col3.altair_chart(chart, use_container_width=True)
    
        ##exibe um pequeno dataframe que sintetiza as informações obtidas pelo gráfico
        resumo_microorganismo = df_filtrado.groupby('cd_sigla_microorganismo').agg(
            media_tempo_internacao=pd.NamedAgg(column='tempo_internacao_dias', aggfunc='mean'),
            total_admissoes=pd.NamedAgg(column='tempo_internacao_dias', aggfunc='count')
        ).reset_index()

        ##muda o nome das colunas no dataframe para melhor visualização
        resumo_microorganismo = resumo_microorganismo.rename(columns={
            'cd_sigla_microorganismo': 'Microorganismo',
            'media_tempo_internacao': 'Média Tempo Internação',
            'total_admissoes': 'Admissões'
        })
    
        col3.dataframe(resumo_microorganismo, use_container_width=True, hide_index=True)
    
        ##informações sobre os filtros selecionados
        st.write(f"Microorganismos: {', '.join(microorganismos_selecionados) if microorganismos_selecionados else 'Todos'}")
        st.write(f"Período: {filtro_periodo[0]} a {filtro_periodo[1]}")
