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
# # Merge datasets
# names = departments.merge(baby_names, how='right', left_on='code', right_on='dpt')
# # Drop the geometry column before groupby
# names_no_geom = names.drop(columns='geometry')

# # Perform the groupby operation
# grouped = names_no_geom.groupby(['dpt', 'preusuel', 'sexe'], as_index=False).sum()
# # Merge the geometry data back in
# grouped = departments.merge(grouped, how='right', left_on='code', right_on='dpt')

# Title of the app
st.title('Interactive Baby Names Visualization in France')

# Sidebar for selecting the visualization
st.sidebar.title('Select Visualization')
visualization = st.sidebar.selectbox('Choose a visualization type', 
                                     ['Baby Names Over Time', 'Regional Effect', 'Names by Sex Over Time'])

# Visualization 1: Baby Names Over Time
if visualization == 'Baby Names Over Time':
    agg_baby_names = baby_names.groupby(['preusuel', 'annais']).agg({'nombre': 'sum'}).reset_index()

    st.header('Name Trends Interactive Visualization')

    # input for searching names
    search_text = st.text_input('Search for names (partial match):')

    if 'selected_names' not in st.session_state:
        st.session_state.selected_names = []

    # filter names based on search text
    filtered_names = sorted(agg_baby_names['preusuel'].unique())
    if search_text:
        filtered_names = [name for name in filtered_names if search_text.lower() in name.lower()]

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

    # No selection -> All lines in original color
    if not st.session_state.selected_names:
        final_chart = alt.Chart(agg_baby_names).mark_line(point=True).encode(
            x=alt.X('annais:O', title='Year'),
            y=alt.Y('nombre:Q', title='Number of Occurrences'),
            color=alt.Color('preusuel:N', legend=alt.Legend(title='Name')),
            tooltip=['preusuel', 'annais', 'nombre']
        ).properties(width=600, height=600, title='Name Trends (All Names)')
    # Selection made -> Only600lected names colored, others grayed out
    else:
        # Split baby_names into selected and unselected
        agg_baby_names['is_selected'] = agg_baby_names['preusuel'].apply(lambda x: x in st.session_state.selected_names)
        selected_baby_names = agg_baby_names[agg_baby_names['is_selected']]
        unselected_baby_names = agg_baby_names[~agg_baby_names['is_selected']]

        # Base chart for unselected (gray lines)
        base_chart = alt.Chart(unselected_baby_names).mark_line(point=False).encode(
            x=alt.X('annais:O', title='Year'),
            y=alt.Y('nombre:Q', title='Number of Occurrences'),
            detail='preusuel:N', 
            color=alt.value('#D3D3D3'),
            opacity=alt.value(0.1),
            tooltip=['preusuel', 'annais', 'nombre']
        )

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
                st.image("https://media.istockphoto.com/id/584205358/fr/vectoriel/france-carte.jpg?s=612x612&w=0&k=20&c=eCCphbNXipSQxCuJ5fw1qjHKJ_NdKRVmccPtHSMYPgc=", caption="Départements", use_container_width=True, width=50)
                if st.button("See by Départements"):
                    st.session_state.view_mode = 'departement'
            with col2:
                st.image("https://static.vecteezy.com/system/resources/previews/014/342/168/non_2x/doodle-freehand-drawing-of-france-map-free-png.png", caption="Régions", use_container_width=True, width=45)
                if st.button("See by Régions"):
                    st.session_state.view_mode = 'region'

            if st.session_state.view_mode == 'departement':
                chart_data = data[data['annais']==year]
                chart_data = departments.merge(chart_data[["dpt", "nombre"]], how='left', left_on='code', right_on='dpt')
                chart_data = chart_data.fillna(0)
                chart_data = chart_data.drop(columns='dpt')
                regional_chart = alt.Chart(chart_data).mark_geoshape(stroke='white').encode(
                    tooltip=['nom','code', 'nombre'],
                    color=alt.Color('nombre:Q', scale=alt.Scale(scheme='viridis'), legend=alt.Legend(title='Nombre')),
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
                    color=alt.Color('nombre:Q', scale=alt.Scale(scheme='viridis')),
                    tooltip=['nom', 'nombre']
                ).properties(width=600, height=600)
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as arquivo:
                    chart.save(arquivo.name)
                    arquivo.flush()
                    HtmlFile = open(arquivo.name, 'r', encoding='utf-8')

                    # Load HTML file in HTML component for display on Streamlit page
                    components.html(HtmlFile.read(), height=620)
                # st.altair_chart(regional_chart)

                st.altair_chart(chart)



# Visualization 3: Gender Perception Trends in Baby Names


elif visualization == 'Names by Sex Over Time':
    st.header('Gender Perception of Names Over Time')

    df = baby_names.copy()
    df = df[df['sexe'].isin([1, 2])]
    
    # Regroupement par prénom, année et sexe
    grouped = df.groupby(['preusuel', 'annais', 'sexe'])['nombre'].sum().reset_index()
    pivot = grouped.pivot_table(index=['preusuel', 'annais'], columns='sexe', values='nombre', fill_value=0).reset_index()
    pivot.columns = ['preusuel', 'annais', 'garcons', 'filles']
    
    pivot['total'] = pivot['garcons'] + pivot['filles']
    pivot = pivot[pivot['total'] > 0]
    pivot['pct_fille'] = pivot['filles'] / pivot['total']

    # Classification plus fine
    def classify_gender(pct):
        if pct == 0.0:
            return 'Uniquement masculin'
        elif pct < 0.05:
            return 'Très masculin'
        elif pct < 0.30:
            return 'Légèrement masculin'
        elif pct <= 0.70:
            return 'Neutre'
        elif pct <= 0.95:
            return 'Légèrement féminin'
        elif pct < 1.0:
            return 'Très féminin'
        else:
            return 'Uniquement féminin'

    pivot['genre_percu'] = pivot['pct_fille'].apply(classify_gender)

    # Compter le nombre de prénoms par catégorie par année
    genre_counts = pivot.groupby(['annais', 'genre_percu']).size().reset_index(name='count')
    total_by_year = genre_counts.groupby('annais')['count'].transform('sum')
    genre_counts['proportion'] = genre_counts['count'] / total_by_year

    ordered_categories = [
        'Uniquement masculin',
        'Très masculin',
        'Légèrement masculin',
        'Neutre',
        'Légèrement féminin',
        'Très féminin',
        'Uniquement féminin'
    ]

    ordre_map = {cat: f"{i}:{cat}" for i, cat in enumerate(ordered_categories)}
    genre_counts['order'] = genre_counts['genre_percu'].map(ordre_map)

    prenoms_by_group = pivot.groupby(['annais', 'genre_percu'])['preusuel'].apply(
        lambda x: ', '.join(sorted(set(x))[:15]) + ('...' if len(set(x)) > 15 else '')
    ).reset_index(name='prenoms')

    genre_counts = genre_counts.merge(prenoms_by_group, on=['annais', 'genre_percu'], how='left')

    print(genre_counts)

    # Créer le graphe Altair
    chart = alt.Chart(genre_counts).mark_area(
    ).encode(
        x=alt.X('annais:O', title='Année'),
        y=alt.Y('proportion:Q', stack='normalize', title='Proportion'),
        color=alt.Color('order:N', scale=alt.Scale(scheme='redblue'), 
                        title='Genre perçu'),
        tooltip=[
            alt.Tooltip('annais:O', title='Année'),
            alt.Tooltip('genre_percu:N', title='Genre perçu'),
            alt.Tooltip('count:Q', title='Nombre de prénoms'),
            alt.Tooltip('proportion:Q', title='Proportion', format='.2%'),
            alt.Tooltip('prenoms:N', title='Exemples de prénoms')
        ]
    ).properties(
        width=800,
        height=400,
        title='Évolution des genres perçus par année'
    )


    st.altair_chart(chart)
