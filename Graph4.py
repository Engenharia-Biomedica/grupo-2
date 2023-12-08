##importa bibliotecas que serão úteis para o funcionamento do sistema
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

##muito similar a primeira aba de exibição do dashboard, mas ao invés de apresentar informações sobre a sensibilidade de antibioticos, apresenta a de sensibilidade de microorganismos

##função para calculo da variável "delta" que será utilizada posteriormente nas st.metrics
##o valor de delta dos microorganismos que apresentaram resistencia é dado pela quantidade de casos de resistencia numa mesma ala no período selecionado
##já o valor de delta para os microorganismos que apresentaram sensibilidade com aumento de dose ou dose dependente foram calculados juntos e também se referem a uma mesma ala no periodo selecionado
def calcular_delta_casos_ala_microorganismo(df_periodo_selecionado, df_periodo_anterior, microorganismo, interpretacao):
    casos_periodo_selecionado = df_periodo_selecionado[(df_periodo_selecionado['cd_interpretacao_antibiograma'] == interpretacao) & (df_periodo_selecionado['cd_sigla_microorganismo'] == microorganismo)]
    casos_periodo_anterior = df_periodo_anterior[(df_periodo_anterior['cd_interpretacao_antibiograma'] == interpretacao) & (df_periodo_anterior['cd_sigla_microorganismo'] == microorganismo)]

    alas_periodo_selecionado = casos_periodo_selecionado['ds_ala_coleta'].unique()
    alas_periodo_anterior = casos_periodo_anterior['ds_ala_coleta'].unique()

    alas_com_mais_de_um_caso_selecionado = [ala for ala in alas_periodo_selecionado if casos_periodo_selecionado[casos_periodo_selecionado['ds_ala_coleta'] == ala].shape[0] > 1]
    alas_com_mais_de_um_caso_anterior = [ala for ala in alas_periodo_anterior if casos_periodo_anterior[casos_periodo_anterior['ds_ala_coleta'] == ala].shape[0] > 1]

    delta_casos_ala = len(set(alas_com_mais_de_um_caso_selecionado) - set(alas_com_mais_de_um_caso_anterior))

    return delta_casos_ala, set(alas_com_mais_de_um_caso_selecionado)

##função que será chamada na página principal
def graph4():
    st.header("Sensibilidade por Microorganismos")

    ##divisão em colunas para melhor visualização
    col1, col2, col3 = st.columns([1, 1, 2])

    ##carregar os dados do CSV
    url = "https://raw.githubusercontent.com/AndersonEduardo/pbl-2023/main/sample_data_clean.csv"
    df = pd.read_csv(url)

    ##converte a coluna de datas
    df['dh_liberacao_exame'] = pd.to_datetime(df['dh_liberacao_exame'])

    ##botões para seleção de período
    periodo_opcao = col1.radio("2- Selecione o período:", ["30 dias", "90 dias", "6 meses", "1 ano", "Período completo"])

    ##calcula o período correspondente aos botões criados
    if periodo_opcao == "30 dias":
        data_maxima = df['dh_liberacao_exame'].max().date()
        data_inicial = data_maxima - pd.DateOffset(days=30)
    elif periodo_opcao == "90 dias":
        data_maxima = df['dh_liberacao_exame'].max().date()
        data_inicial = data_maxima - pd.DateOffset(days=90)
    elif periodo_opcao == "6 meses":
        data_maxima = df['dh_liberacao_exame'].max().date()
        data_inicial = data_maxima - pd.DateOffset(months=6)
    elif periodo_opcao == "1 ano":
        data_maxima = df['dh_liberacao_exame'].max().date()
        data_inicial = data_maxima - pd.DateOffset(years=1)
    else:  # Período completo
        data_inicial = df['dh_liberacao_exame'].min().date()
        data_maxima = df['dh_liberacao_exame'].max().date()

    ##adiciona filtro de período
    filtro_periodo = col1.date_input('2- Selecione o período:', [data_inicial, data_maxima])

    ##converte os filtros de período para numpy.datetime64, para posterior ajuste de valores de média em gráficos
    filtro_periodo = [np.datetime64(date) for date in filtro_periodo]

    ##aplica filtro de período
    df_filtrado = df[(df['dh_liberacao_exame'] >= filtro_periodo[0]) & (df['dh_liberacao_exame'] <= filtro_periodo[1])]

    ##pipeline de dados para excluir valores nulos do gráfico, mas mostrá-los no dataframe
    df_chart = df_filtrado.dropna(subset=['cd_sigla_microorganismo', 'cd_interpretacao_antibiograma', 'ds_ala_coleta'])
    df_chart = df_chart.replace(np.nan, 'Sem informações', regex=True)

    ##caixa de seleção que adiciona filtros de microorganismos
    microorganismos_selecionados_resistencia = col2.multiselect(
        'Selecione os microorganismos:',
        df_filtrado['cd_sigla_microorganismo'].unique(),
        default=df_filtrado['cd_sigla_microorganismo'].unique(),  # Selecionar todos por padrão
        key='microorganismos_resistencia_multiselect'
    )

    ##erifica se há dados existentes no dataset para os microorganismos selecionados
    if not df_chart[df_chart['cd_sigla_microorganismo'].isin(microorganismos_selecionados_resistencia)].empty:
        
        ##cria um gráfico para a sensibilidade dos microorganismos usando a biblioteca Altair
        chart = alt.Chart(df_chart).mark_bar().encode(
            x=alt.X('cd_sigla_microorganismo:N', title='Microorganismo'),
            y=alt.Y('count():Q', title='Contagem'),
            color=alt.Color('cd_interpretacao_antibiograma:N', title='Interpretação')
        ).properties(
            width=400,
            height=250
        )

        col3.altair_chart(chart, use_container_width=True)

    ##nova coluna para melhor visualização dos dados
    st.header("", divider='green')
    col4, col5, col6 = st.columns([1, 1, 2])

    ##filtro de dados para o período selecionado e posterior aplicação a um dataframe
    df_periodo_selecionado = df_chart[(df_chart['dh_liberacao_exame'] >= filtro_periodo[0]) & (df_chart['dh_liberacao_exame'] <= filtro_periodo[1])]

    ##filtra dados para o período anterior aos 30 dias
    data_final_anterior = filtro_periodo[0] - pd.DateOffset(days=1)
    data_inicial_anterior = data_final_anterior - pd.DateOffset(days=30)
    df_periodo_anterior = df_chart[(df_chart['dh_liberacao_exame'] >= data_inicial_anterior) & (df_chart['dh_liberacao_exame'] <= data_final_anterior)]

    ##calcula resistência por microorganismo para o período selecionado e anterior aos 30 dias
    resistencia_periodo_selecionado = df_periodo_selecionado[df_periodo_selecionado['cd_interpretacao_antibiograma'] == 'Resistente']
    resistencia_periodo_anterior = df_periodo_anterior[df_periodo_anterior['cd_interpretacao_antibiograma'] == 'Resistente']

    ##contagem de interpretações "Sensível Aumentando Exposição" e "Sensível Dose-Dependente" para o período selecionado e anterior aos 30 dias
    sensivel_periodo_selecionado = df_periodo_selecionado[df_periodo_selecionado['cd_interpretacao_antibiograma'].isin(['Sensível Aumentando Exposição', 'Sensível Dose-Dependente'])]
    sensivel_periodo_anterior = df_periodo_anterior[df_periodo_anterior['cd_interpretacao_antibiograma'].isin(['Sensível Aumentando Exposição', 'Sensível Dose-Dependente'])]

    ##seleciona os três microorganismos com mais resistência
    microorganismos_maior_resistencia = resistencia_periodo_selecionado['cd_sigla_microorganismo'].value_counts().head(3).index.tolist()

    ##seleciona os três microorganismos com mais interpretações "Sensível Aumentando Exposição" e "Sensível Dose-Dependente"
    microorganismos_maior_sensivel = sensivel_periodo_selecionado.groupby('cd_sigla_microorganismo').size().sort_values(ascending=False).head(3).index.tolist()

    ##nova organização em colunas
    col4, col5, col6 = st.columns([1, 1, 2])

    ##definição da coluna 4, nesta coluna foram implementados widgets do tipo st.metric que irão rankear os 3 microoganismos que mais apresentaram resistencia,
    ##a quantidade de casos de resistencia e também em quantas alas ocorreram mais de uma ocorrência de resistência, podendo auxiliar na identificação de alas
    ##infectadas por bactérias resistentes
    col4.subheader("Resistente", divider="green")
    for i, microorganismo in enumerate(microorganismos_maior_resistencia):
        delta_casos_ala, alas_selecionadas = calcular_delta_casos_ala_microorganismo(df_periodo_selecionado, df_periodo_anterior, microorganismo, 'Resistente')

        col4.metric(f"{microorganismo}",
                    f"{resistencia_periodo_selecionado[resistencia_periodo_selecionado['cd_sigla_microorganismo'] == microorganismo].shape[0]} casos",
                    delta=f"Casos na mesma ala: {delta_casos_ala}"
                    )
        st.markdown(f"Ala(s): {', '.join(alas_selecionadas)} - Microorganismo: {microorganismo}")

    ##definição da coluna 5, nesta coluna foram implementados widgets do tipo st.metric que irão rankear os 3 microorganismo que mais apresentaram sensibilidade reduzida,
    ##e que foi necessário o aumento de dose ou se tornaram dose-dependentes, a classificação foi dada também quanto ao número de alas que apresentaram mais de um
    ##caso de sensibilidade reduzida, e que um alto número desses casos numa mesma ala pode indicar o crescimento de uma bactéria resistente
    col5.subheader("Sensível AD/DD", divider="green")

    for i, microorganismo in enumerate(microorganismos_maior_sensivel):
        resultado_sensivel_AE = calcular_delta_casos_ala_microorganismo(df_periodo_selecionado, df_periodo_anterior, microorganismo, 'Sensível Aumentando Exposição')
        resultado_sensivel_DD = calcular_delta_casos_ala_microorganismo(df_periodo_selecionado, df_periodo_anterior, microorganismo, 'Sensível Dose-Dependente')

        delta_casos_ala = resultado_sensivel_AE[0] + resultado_sensivel_DD[0]
        alas_selecionadas = resultado_sensivel_AE[1].union(resultado_sensivel_DD[1])

        col5.metric(f"{microorganismo}",
                    f"{sensivel_periodo_selecionado[sensivel_periodo_selecionado['cd_sigla_microorganismo'] == microorganismo].shape[0]} casos",
                    delta=f"Casos na mesma ala: {delta_casos_ala}"
                    )
        st.markdown(f"Ala(s): {', '.join(alas_selecionadas)} - Microorganismo: {microorganismo}")

    ##dados para exibir um dataframe que sintetize as informações obtidas no gráfico
    resumo_microorganismos = df_chart.groupby(['cd_sigla_microorganismo', 'cd_interpretacao_antibiograma']).size().unstack(fill_value=0)
    resumo_microorganismos = resumo_microorganismos.reset_index()

    ##renomeia a coluna 'cd_sigla_microorganismo' para 'Microorganismo'
    resumo_microorganismos = resumo_microorganismos.rename(columns={'cd_sigla_microorganismo': 'Microorganismo'})

    ##gera um dataframe com as informações mencionadas anteriormente
    col6.dataframe(resumo_microorganismos, use_container_width=True, hide_index=True)

    ##informações sobre os filtros selecionados
    st.write(f"Microorganismos selecionados: {', '.join(microorganismos_selecionados_resistencia) if microorganismos_selecionados_resistencia else 'Todos'}")
    st.write(f"Período selecionado: {filtro_periodo[0]} a {filtro_periodo[1]}")
