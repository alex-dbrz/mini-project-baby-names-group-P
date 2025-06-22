import tempfile
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd 
import altair as alt
import geopandas as gpd
import folium
from streamlit_folium import folium_static

# Load the datasets
baby_names = pd.read_csv('dpt2020.csv', delimiter=';')
departments = gpd.read_file('departements-version-simplifiee.geojson')
regions = gpd.read_file("regions-version-simplifiee.geojson")
correspondance = pd.read_csv("dpt-to-reg.csv", dtype=str)

# Data preprocessing
baby_names.drop(baby_names[baby_names.preusuel == '_PRENOMS_RARES'].index, inplace=True)
baby_names.drop(baby_names[baby_names.dpt == 'XX'].index, inplace=True)

# Title of the app
st.title('Interactive Baby Names Visualization in France')

# Sidebar for selecting the visualization
st.sidebar.title('Select Visualization')
visualization = st.sidebar.selectbox('Choose a visualization type', 
                                     ['Names by Sex Over Time', 'Baby Names Over Time', 'Regional Effect'])

# Visualization 1: Baby Names Over Time
if visualization == 'Baby Names Over Time':
    agg_baby_names = baby_names.groupby(['preusuel', 'annais']).agg({'nombre': 'sum'}).reset_index()

    st.header('Name Trends Interactive Visualization')

    if 'selected_names' not in st.session_state:
        st.session_state.selected_names = []

    # filter names based on search text
    filtered_names = sorted(agg_baby_names['preusuel'].unique())
    new_selection = st.multiselect('Select names to highlight:', options=filtered_names)

    # update session state with new selections
    for name in new_selection:
        if name not in st.session_state.selected_names:
            st.session_state.selected_names.append(name)

    # show selected names
    st.write('### Selected Names:')
    to_remove = st.multiselect('Remove names:', options=st.session_state.selected_names)
    for name in to_remove:
        st.session_state.selected_names.remove(name)

    # # Compute the mean and standard deviation for each year
    year_stats = baby_names.groupby('annais')['nombre'].agg(['mean','std']).reset_index()
    # # log print mean and std
    # st.write('### Mean and Standard Deviation of Name Occurrences Over Time')
    # st.write(year_stats)
    
    # base chart: mean line and standard deviation area
    mean_line = alt.Chart(year_stats).mark_line(color='gray').encode(
        x=alt.X('annais:O', title='Year'),
        y=alt.Y('mean:Q', title='Mean Number of Occurrences')
    )
    std_area = alt.Chart(year_stats).transform_calculate(
        upper='datum.mean + datum.std',
        lower='datum.mean - datum.std'
    ).mark_area(
        color='lightgray', opacity=0.5
    ).encode(
        x='annais:O',
        y='lower:Q',
        y2='upper:Q'
    )
    # Combine
    base_chart = alt.layer(mean_line, std_area).properties(
        width=600,
        height=600,
        title='Mean and Standard Deviation of Name Occurrences Over Time'
    )

    # No selection -> All lines in original color
    if not st.session_state.selected_names:
        final_chart = base_chart
    else:
        # Split baby_names into selected and unselected
        agg_baby_names['is_selected'] = agg_baby_names['preusuel'].apply(lambda x: x in st.session_state.selected_names)
        selected_baby_names = agg_baby_names[agg_baby_names['is_selected']]
        unselected_baby_names = agg_baby_names[~agg_baby_names['is_selected']]

        # Top chart for selected (colored lines)
        highlight_chart = alt.Chart(selected_baby_names).mark_line(point=True).encode(
            x=alt.X('annais:O'),
            y=alt.Y('nombre:Q'),
            color=alt.Color('preusuel:N', legend=alt.Legend(title='Name')),
            tooltip=['preusuel', 'annais', 'nombre']
        )

        # Combine charts in layers
        final_chart = alt.layer(base_chart, highlight_chart).properties(
            width=600,
            height=600,
            title='Name Trends (Selected Lines on Top)'
        )

    st.altair_chart(final_chart, use_container_width=True)



# Visualization 2: Regional Effect
elif visualization == 'Regional Effect':
    st.header('Regional Effect of Baby Names in France')
    name = st.selectbox('Select a baby name', baby_names['preusuel'].unique())
    
    if name:
        subset_name = baby_names[baby_names['preusuel'] == name]
        data = departments.merge(subset_name, how='left', left_on='code', right_on='dpt')
        data2 = pd.merge(subset_name, correspondance, left_on='dpt', right_on='num_dep', how='left')
        arr = [i for i in data['annais'].unique() if type(i) == str]
        arr.sort()
        year = st.selectbox('Select a year', arr)
        if year :
            if 'view_mode' not in st.session_state:
                st.session_state.view_mode = 'departement'
            col1, col2 = st.columns(2)
            with col1:
                if st.button("See by Départements"):
                    st.session_state.view_mode = 'departement'
            with col2:
                if st.button("See by Régions"):
                    st.session_state.view_mode = 'region'

            if st.session_state.view_mode == 'departement':
                chart_data = data[data['annais']==year]
                chart_data = departments.merge(chart_data[["dpt", "nombre"]], how='left', left_on='code', right_on='dpt')
                chart_data = chart_data.fillna(0)
                chart_data = chart_data.drop(columns='dpt')
                regional_chart = alt.Chart(chart_data).mark_geoshape(stroke='white').encode(
                    tooltip=['nom','code', 'nombre'],
                    color=alt.Color('nombre:Q', scale=alt.Scale(scheme='viridis'), legend=alt.Legend(title='Number')),
                ).properties(width=600, height=600)
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as arquivo:
                    regional_chart.save(arquivo.name)
                    arquivo.flush()
                    HtmlFile = open(arquivo.name, 'r', encoding='utf-8')

                    # Load HTML file in HTML component for display on Streamlit page
                    components.html(HtmlFile.read(), height=620)
                # st.altair_chart(regional_chart)

            elif st.session_state.view_mode == 'region':
                df_region = data2.groupby(['region_name', 'annais'])['nombre'].sum().reset_index()
                map_data = regions.merge(df_region[df_region['annais'] == year], left_on='nom', right_on='region_name', how='left')
                map_data = map_data.fillna({'nombre': 0})
                chart = alt.Chart(map_data).mark_geoshape(stroke='white').encode(
                    color=alt.Color('nombre:Q', scale=alt.Scale(scheme='viridis'), legend=alt.Legend(title='Number')),
                    tooltip=['nom', 'nombre']
                ).properties(width=600, height=600)
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as arquivo:
                    chart.save(arquivo.name)
                    arquivo.flush()
                    HtmlFile = open(arquivo.name, 'r', encoding='utf-8')

                    # Load HTML file in HTML component for display on Streamlit page
                    components.html(HtmlFile.read(), height=620)




# Visualization 3: Gender Perception Trends in Baby Names
elif visualization == 'Names by Sex Over Time':
    st.header('Gender Perception of Names Over Time')

    df = baby_names.copy()
    df = df[df['sexe'].isin([1, 2])]

    grouped = df.groupby(['preusuel', 'annais', 'sexe'])['nombre'].sum().reset_index()
    pivot = grouped.pivot_table(index=['preusuel', 'annais'], columns='sexe', values='nombre', fill_value=0).reset_index()
    pivot.columns = ['preusuel', 'annais', 'garcons', 'filles']
    pivot['total'] = pivot['garcons'] + pivot['filles']
    pivot = pivot[pivot['total'] > 0]
    pivot['pct_fille'] = pivot['filles'] / pivot['total']

    # Classification
    def classify_gender(pct):
        if pct == 0.0:
            return 'Uniquement masculin'
        elif pct < 0.05:
            return 'Majoritairement masculin'
        elif pct < 0.95:
            return 'Neutre'
        elif pct < 1.0:
            return 'Majoritairement féminin'
        else:
            return 'Uniquement féminin'

    pivot['genre_percu'] = pivot['pct_fille'].apply(classify_gender)

    df_genre = df.merge(pivot[['preusuel', 'annais', 'genre_percu']], on=['preusuel', 'annais'], how='left')

    genre_counts_people = df_genre.groupby(['annais', 'genre_percu'])['nombre'].sum().reset_index()
    total_by_year_people = genre_counts_people.groupby('annais')['nombre'].transform('sum')
    genre_counts_people['proportion'] = genre_counts_people['nombre'] / total_by_year_people

    ordered_categories = [
        'Uniquement masculin',
        'Majoritairement masculin',
        'Neutre',
        'Majoritairement féminin',
        'Uniquement féminin'
    ]

    ordre_map = {cat: f"{i}:{cat}" for i, cat in enumerate(ordered_categories)}
    genre_counts_people['order'] = genre_counts_people['genre_percu'].map(ordre_map)

    prenoms_by_group = pivot.groupby(['annais', 'genre_percu'])['preusuel'].apply(
        lambda x: ', '.join(sorted(set(x))[:20]) + ('...' if len(set(x)) > 20 else '')
    ).reset_index(name='prenoms')

    genre_counts_people = genre_counts_people.merge(prenoms_by_group, on=['annais', 'genre_percu'], how='left')

    # graphe Altair
    chart = alt.Chart(genre_counts_people).mark_area(
    ).encode(
        x=alt.X('annais:O', title='Année'),
        y=alt.Y('proportion:Q', stack='normalize', title='Proportion'),
        color=alt.Color('order:N', scale=alt.Scale(scheme='redblue'), 
                        title='Genre perçu'),
        tooltip=[
            alt.Tooltip('annais:O', title='Année'),
            alt.Tooltip('genre_percu:N', title='Genre perçu'),
            alt.Tooltip('nombre:Q', title='Nombre de prénoms'),
            alt.Tooltip('proportion:Q', title='Proportion', format='.2%'),
            alt.Tooltip('prenoms:N', title='Exemples de prénoms')
        ]
    ).properties(
        width=800,
        height=400,
        title='Évolution des genres perçus par année'
    )
    st.markdown("""
    - La catégorisation du "genre perçu" repose sur des seuils arbitraires :
        - 0% → Uniquement masculin
        - <5% → Très masculin
        - <30% → Légèrement masculin
        - 30–70% → Neutre
        - >70% → Légèrement féminin
        - >95% → Très féminin
        - 100% → Uniquement féminin
    """)

    st.altair_chart(chart)
