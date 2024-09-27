import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import json
from io import StringIO

# Lendo o arquivo CSV
with open('CCB_Unificado.csv', 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')

df = pd.read_csv(StringIO(content), sep=';')

# Calcular o percentual de membros
df['Percentual_Membros_2010'] = (df['Membros_CCB_2010'] / df['Populacao_Total_2010']) * 100
df['Percentual_Membros_2000'] = (df['Membros_CCB_2000'] / df['Populacao_Total_2000']) * 100

# Calcular a diferença de membros
df['Diferenca_Membros'] = df['Membros_CCB_2010'] - df['Membros_CCB_2000']

# Dicionário com os caminhos dos arquivos GeoJSON para cada estado
geojson_paths = {
    'AC': 'geojson/geojs-12-mun.json',
    'AM': 'geojson/geojs-13-mun.json',
    'AP': 'geojson/geojs-16-mun.json',
    'PA': 'geojson/geojs-15-mun.json',
    'RO': 'geojson/geojs-11-mun.json',
    'RR': 'geojson/geojs-14-mun.json',
    'TO': 'geojson/geojs-17-mun.json',
    'AL': 'geojson/geojs-27-mun.json',
    'BA': 'geojson/geojs-29-mun.json',
    'CE': 'geojson/geojs-23-mun.json',
    'MA': 'geojson/geojs-21-mun.json',
    'PB': 'geojson/geojs-25-mun.json',
    'PE': 'geojson/geojs-26-mun.json',
    'PI': 'geojson/geojs-22-mun.json',
    'RN': 'geojson/geojs-24-mun.json',
    'SE': 'geojson/geojs-28-mun.json',
    'ES': 'geojson/geojs-32-mun.json',
    'MG': 'geojson/geojs-31-mun.json',
    'RJ': 'geojson/geojs-33-mun.json',
    'SP': 'geojson/geojs-35-mun.json',
    'PR': 'geojson/geojs-41-mun.json',
    'RS': 'geojson/geojs-43-mun.json',
    'SC': 'geojson/geojs-42-mun.json',
    'DF': 'geojson/geojs-53-mun.json',
    'GO': 'geojson/geojs-52-mun.json',
    'MT': 'geojson/geojs-51-mun.json',
    'MS': 'geojson/geojs-50-mun.json',
    'BR': 'geojson/geojs-100-mun.json'
}

# Inicializar o aplicativo Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard de Membros da CCB por Municipio"),
    
    dcc.Dropdown(
        id='estado-dropdown',
        options=[
            {'label': 'Brasil', 'value': 'BR'}
        ] + [{'label': estado, 'value': estado} for estado in df['Estado'].unique()],
        multi=False,
        value='BR'  # Define o valor padrão como Brasil
    ),
    
    dcc.Dropdown(
        id='ano-dropdown',
        options=[
            {'label': '2000', 'value': 2000},
            {'label': '2010', 'value': 2010}
        ],
        multi=False,
        value=2010
    ),

    dcc.Dropdown(
        id='ordenacao-dropdown',
        options=[
            {'label': 'Membros (Maior para Menor)', 'value': 'membros_desc'},
            {'label': 'Membros (Menor para Maior)', 'value': 'membros_asc'},
            {'label': 'Percentual (Maior para Menor)', 'value': 'percentual_desc'},
            {'label': 'Percentual (Menor para Maior)', 'value': 'percentual_asc'},
        ],
        multi=False,
        value='membros_desc'
    ),
    
    dcc.Graph(id='populacao-grafico', style={'height': '50vh'}),
    dcc.Graph(id='membros-grafico', style={'height': '50vh'}),
    dcc.Graph(id='percentual-grafico', style={'height': '50vh'}),
    
    # Ajustando a altura e largura dos gráficos do mapa
    dcc.Graph(id='mapa-grafico', style={'height': '1000px', 'width': '1000px'}),
    dcc.Graph(id='mapa-percentual-grafico', style={'height': '1000px', 'width': '1000px'}),
    
    # Gráficos de ganho e perda de membros
    dcc.Graph(id='ganhos-membros-grafico', style={'height': '50vh'}),
    dcc.Graph(id='perdas-membros-grafico', style={'height': '50vh'}),
    
    html.Div([
        html.H3("Estatisticas a Nivel Brasil"),
        html.P(f"Populacao Total: {df['Populacao_Total_2010'].sum()}"),
        html.P(f"Membros da CCB: {df['Membros_CCB_2010'].sum()}"),
        html.P(f"Percentual de Membros: {(df['Membros_CCB_2010'].sum() / df['Populacao_Total_2010'].sum() * 100):.2f}%")
    ])
])

@app.callback(
    Output('populacao-grafico', 'figure'),
    Output('membros-grafico', 'figure'),
    Output('percentual-grafico', 'figure'),
    Output('mapa-grafico', 'figure'),
    Output('mapa-percentual-grafico', 'figure'),
    Output('ganhos-membros-grafico', 'figure'),
    Output('perdas-membros-grafico', 'figure'),
    Input('estado-dropdown', 'value'),
    Input('ano-dropdown', 'value'),
    Input('ordenacao-dropdown', 'value')
)
def update_graphs(estado_selecionado, ano_selecionado, ordenacao_selecionada):
    if estado_selecionado == 'BR':
        filtro_estado = df  # Seleciona todos os dados
    else:
        filtro_estado = df[df['Estado'] == estado_selecionado]

    if filtro_estado.empty:
        return {}, {}, {}, {}, {}, {}, {}

    # Carregar o GeoJSON correspondente ao estado selecionado
    geojson_file = geojson_paths.get(estado_selecionado)
    try:
        with open(geojson_file, 'r', encoding='utf-8') as f:
            geojson_municipios = json.load(f)
    except FileNotFoundError:
        return {}, {}, {}, {}, {}, {}, {}
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON: {geojson_file}")
        return {}, {}, {}, {}, {}, {}, {}

    # Selecionar colunas com base no ano
    if ano_selecionado == 2000:
        populacao_col = 'Populacao_Total_2000'
        membros_col = 'Membros_CCB_2000'
        percentual_col = 'Percentual_Membros_2000'
    else:
        populacao_col = 'Populacao_Total_2010'
        membros_col = 'Membros_CCB_2010'
        percentual_col = 'Percentual_Membros_2010'

    # Determinar a coluna e a ordem de ordenação
    if 'membros' in ordenacao_selecionada:
        ordem_col = membros_col
    else:
        ordem_col = percentual_col

    ascending = 'asc' in ordenacao_selecionada

    # Ordenação
    filtro_estado = filtro_estado.sort_values(by=ordem_col, ascending=ascending)

    # Gráfico de População
    fig_populacao = px.bar(
        filtro_estado,
        x='Municipio',
        y=populacao_col,
        title=f'Populacao Total por Municipio ({ano_selecionado})'
    )
    
    # Gráfico de Membros da CCB
    fig_membros = px.bar(
        filtro_estado,
        x='Municipio',
        y=membros_col,
        title=f'Membros da CCB por Municipio ({ano_selecionado})'
    )
    
    # Gráfico de Percentual de Membros
    fig_percentual = px.bar(
        filtro_estado,
        x='Municipio',
        y=percentual_col,
        title=f'Percentual de Membros da CCB em Relacao a Populacao Total ({ano_selecionado})',
        labels={percentual_col: 'Percentual (%)'}
    )

    # Mapa
    fig_mapa = px.choropleth(
        filtro_estado,
        geojson=geojson_municipios,
        locations='Municipio',
        featureidkey="properties.name",  # Verifique este nome
        color=membros_col,
        color_continuous_scale="Viridis",
        title='Distribuicao de Membros da CCB por Municipio',
        scope="south america"
    )
    
    # Mapa de Percentagem de Membros
    fig_mapa_percentual = px.choropleth(
        filtro_estado,
        geojson=geojson_municipios,
        locations='Municipio',
        featureidkey="properties.name",
        color=percentual_col,
        color_continuous_scale="Viridis",
        title='Distribuicao de Percentual de Membros da CCB por Municipio',
        scope="south america"
    )

    # Gráfico das cidades que mais ganharam membros
    cidades_ganharam = filtro_estado.nlargest(5, 'Diferenca_Membros')
    fig_ganhos = px.bar(
        cidades_ganharam,
        x='Municipio',
        y='Diferenca_Membros',
        title='Cidades que Mais Ganharam Membros (2000-2010)',
        labels={'Diferenca_Membros': 'Ganho de Membros'}
    )

    # Gráfico das cidades que mais perderam membros
    cidades_perderam = filtro_estado.nsmallest(5, 'Diferenca_Membros')
    fig_perdas = px.bar(
        cidades_perderam,
        x='Municipio',
        y='Diferenca_Membros',
        title='Cidades que Mais Perderam Membros (2000-2010)',
        labels={'Diferenca_Membros': 'Perda de Membros'}
    )

    return fig_populacao, fig_membros, fig_percentual, fig_mapa, fig_mapa_percentual, fig_ganhos, fig_perdas

if __name__ == '__main__':
    app.run_server(debug=True)