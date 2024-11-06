import plotly.graph_objects as go
import pandas as pd

# Archivos CSV de entrada
file_names = ['CUERPO_COSTEROS.csv', 'CUERPO_LENTICOS.csv', 'CUERPO_LOTICOS.csv', 'CUERPO_SUBTERRANEO.csv']
dfs = []

# Leer y procesar cada archivo CSV
for file in file_names:
    try:
        df = pd.read_csv(file)

        # Identificar el tipo de cuerpo de agua a partir del nombre del archivo
        if 'COSTEROS' in file.upper():
            tipo = 'Costero'
        elif 'LENTICOS' in file.upper():
            tipo = 'Léntico'
        elif 'LOTICOS' in file.upper():
            tipo = 'Lótico'
        elif 'SUBTERRANEO' in file.upper():
            tipo = 'Subterráneo'
        else:
            tipo = 'Desconocido'

        # Añadir la columna 'TIPO'
        df['TIPO'] = tipo

        # Renombrar la columna 'CALIDAD_*ALGO' a 'CALIDAD'
        calidad_col = [col for col in df.columns if col.startswith("CALIDAD_")]
        if calidad_col:
            df.rename(columns={calidad_col[0]: 'CALIDAD'}, inplace=True)

        # Filtrar datos nulos en 'YEAR', 'LATITUD', 'LONGITUD', 'CALIDAD' para evitar errores
        df = df.dropna(subset=['YEAR', 'LATITUD', 'LONGITUD', 'CALIDAD'])
        dfs.append(df)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{file}'.")

# Combinar todos los dataframes en uno solo si se cargaron archivos válidos
if dfs:
    combined_df = pd.concat(dfs, ignore_index=True)

    #Hacer que Coliformes Fec sea un objeto no numerico y rellenar los valores
    #faltantes con un aviso
    combined_df['COLI_FEC'] = combined_df['COLI_FEC'].astype('object')
    combined_df['COLI_FEC'] = combined_df['COLI_FEC'].fillna('No hubo medición')

    # Mapa de colores basado en la calidad
    color_map_calidad = {
        "Buena Calidad": "green",
        "Aceptable": "goldenrod",
        "Contaminada": "red",
        "Datos insuficientes": "gray"
    }

    # Crear una figura base de Plotly
    fig = go.Figure()

    # Crear un frame para cada año y tipo
    years = sorted(combined_df["YEAR"].unique())
    tipos = combined_df["TIPO"].unique()

    # Crear los trazos iniciales para el primer año en la figura
    initial_year = years[0]
    for tipo in tipos:
        df_filtered = combined_df[(combined_df["YEAR"] == initial_year) & (combined_df["TIPO"] == tipo)]
        fig.add_trace(
            go.Scattermapbox(
                lat=df_filtered['LATITUD'],
                lon=df_filtered['LONGITUD'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=[color_map_calidad[val] for val in df_filtered["CALIDAD"]],
                ),
                name=tipo,
                customdata=df_filtered[['SITIO', 'CALIDAD', 'COLI_FEC']],
                hovertemplate="<br>".join([
                    "Sitio: %{customdata[0]}",
                    "Calidad: %{customdata[1]}",
                    "Coliformes Fec: %{customdata[2]}"
                ])
            )
        )

    # Crear frames para cada año
    frames = []
    for year in years:
        frame_data = []
        for tipo in tipos:
            df_filtered = combined_df[(combined_df["YEAR"] == year) & (combined_df["TIPO"] == tipo)]
            frame_data.append(
                go.Scattermapbox(
                    lat=df_filtered['LATITUD'],
                    lon=df_filtered['LONGITUD'],
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=[color_map_calidad[val] for val in df_filtered["CALIDAD"]],
                    ),
                    name=tipo+" - "+str(year),
                    customdata=df_filtered[['SITIO', 'CALIDAD', 'COLI_FEC']],
                    hovertemplate="<br>".join([
                        "Sitio: %{customdata[0]}",
                        "Calidad: %{customdata[1]}",
                        "Coliformes Fec: %{customdata[2]}"
                    ])
                )
            )
        frames.append(go.Frame(data=frame_data, name=str(year)))
    
    # Añadir el menú desplegable para el tipo de mapa
    buttons_mapa = [
    dict(args=["mapbox.style", "open-street-map"],
         label="Open Street Map",
         method="relayout"),
    dict(args=["mapbox.style", "carto-positron"],
         label="Carto Positron",
         method="relayout")
    ]
    # Configurar layout con el slider y el menú desplegable
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            zoom=6.3,
            center=dict(lat=combined_df['LATITUD'].mean(), lon=combined_df['LONGITUD'].mean())
        ),
        title="Visualización de Datos: Calidad del Agua - QROO",
        title_x=0.01,  # Centrar el título horizontalmente
        title_y=0.991,  # Ajustar la posición verticalmente (cerca de la parte superior)
        title_font=dict(
            family="Roboto, monospace",  # Establecer la fuente
            size=20,  # Tamaño de fuente
            color="RebeccaPurple"  # Color del título
        ),
        font=dict
        (
            family="Roboto, monospace",
            #size=18,
            color="RebeccaPurple"
        ),
        # Anotaciones para los botones
        annotations=[
            dict(
                text="Tipo de mapa:", 
                showarrow=False, 
                x=0.01,
                xanchor="left",
                y=1.068,
                yanchor="top",
                yref="paper",
                align="left"
            ),
            dict(
                text="Tipo de agua:", 
                showarrow=False, 
                x=0.11,
                xanchor="left", 
                y=1.068,
                yanchor="top",
                yref="paper", 
                align="left"
            )
        ],
        # Botones arribita del mapa
        updatemenus=[
            # Botones para cambiar el estilo del mapa
            {
                "buttons": buttons_mapa,
                "direction": "down",
                "showactive": True,
                "x": 0.01,
                "xanchor": "left",
                "y": 1.045,
                "yanchor": "top"
            },
            # Botones para tipo de agua
            {
                "buttons": [
                    {"method": "update", "label": tipo, "args": [{"visible": [trace.name == tipo for trace in fig.data]}]}
                    for tipo in tipos
                ] + [{"method": "update", "label": "Todos", "args": [{"visible": [True] * len(fig.data)}]}],
                "direction": "down",
                "showactive": True,
                "x": 0.11,
                "xanchor": "left",
                "y": 1.045,
                "yanchor": "top"
        }],
        # controlador de YEAR
        sliders=[{
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {"prefix": "Año: ", "font": {"size": 20}, "visible": True, "xanchor": "right"},
            "pad": {"b": 23, "t": 30},
            "len": 0.9,
            "x": 0.05,
            "y": 0,
            "steps": [
                {
                    "args": [
                        [str(year)],
                        {"frame": {"duration": 500, "redraw": True}, "mode": "immediate"}
                    ],
                    "label": str(year),
                    "method": "animate"
                } for year in years
            ]
        }],
        margin={"r": 0, "t": 100, "l": 0, "b": 15}
    )

    # Asignar los frames a la figura
    fig.frames = frames

    fig.show()
else:
    print("No se procesaron archivos CSV válidos. Verifica los nombres de archivo y las columnas.")

fig.write_html("index.html", full_html=True, include_plotlyjs="cdn")