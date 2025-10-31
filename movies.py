import streamlit as st
import pandas as pd
import requests

# Intentar leer desde GitHub directamente
try:
    csv_url = "https://raw.githubusercontent.com/henrymunoz/cineapp/main/movies_buscador_IN_ESP.csv"
    df = pd.read_csv(csv_url, sep=';', encoding='latin-1')
    st.success("✅ Datos cargados correctamente desde GitHub")
except Exception as e:
    st.error("❌ No se pudo cargar el archivo CSV desde GitHub.")
    st.write("Detalles del error:", e)
    st.stop()


# ===== CONFIG =====
st.set_page_config(page_title="🎬 CineMatch - Recomendador", layout="wide")

# ===== ESTILOS =====
page_bg = """
<style>
    .stApp {
        background-color: #0d47a1;
        color: white;
    }
    label, .stSelectbox label, .stMultiSelect label, .stTextInput label {
        color: white !important;
        font-weight: bold;
    }
    div.stButton > button {
        color: black !important;
        font-weight: bold;
    }
    .centered-message {
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin-top: 40px;
        color: white;
    }
    /* Tarjeta de película */
    .movie-card {
        position: relative;
        overflow: hidden;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .movie-card img {
        border-radius: 12px;
        transition: transform 0.3s ease;
    }
    .movie-card:hover img {
        transform: scale(1.05);
    }
    /* Overlay */
    .overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.3s ease;
        border-radius: 12px;
    }
    .movie-card:hover .overlay {
        opacity: 1;
    }
    .overlay a {
        background: #ffcc00;
        padding: 10px 18px;
        border-radius: 8px;
        text-decoration: none;
        color: black;
        font-weight: bold;
        font-size: 14px;
    }
    .overlay a:hover {
        background: #ffb300;
    }
    /* Rating */
    .rating-badge {
        position: absolute;
        bottom: 8px;
        right: 8px;
        padding: 6px 10px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 4px;
        color: white;
    }
    .rating-good {
        background: rgba(0, 150, 0, 0.8);
    }
    .rating-medium {
        background: rgba(255, 170, 0, 0.8);
    }
    .rating-bad {
        background: rgba(200, 0, 0, 0.8);
    }
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ===== CARGAR DATA =====
#df = pd.read_excel("movies_buscador_IN_ESP.xlsx")  SE ELIMINA BUSQUEDA EN EXCEL
#df = pd.read_csv("movies_buscador_IN_ESP.csv", sep=';', encoding='utf-8', engine='python')
df = pd.read_csv("movies_buscador_IN_ESP.csv", sep=';', encoding='latin-1', engine='python')
df = df.dropna(axis=1, how='all') # Elimina columnas vacias


st.title("🍿 CineMatch - Tu recomendador de películas")
st.markdown("Busca películas por título (inglés o español) o explora por género 🎥")

# Botón refrescar alineado a la derecha
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("🔄 Refrescar búsqueda"):
        st.rerun()

# Buscador
title_search = st.text_input("🔎 Buscar por título (en inglés o español):")

# Filtro por género
all_genres = pd.unique(df[['genres','genres.1','genres.2','genres.3','genres.4']].values.ravel('K'))
all_genres = [g for g in all_genres if pd.notna(g)]
selected_genres = st.multiselect("🎭 Filtrar por género:", sorted(all_genres))

# ===== FILTROS =====
filtered_df = df.copy()

if title_search:
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(title_search, case=False, na=False) |
        filtered_df['title_es'].str.contains(title_search, case=False, na=False)
    ]

if selected_genres:
    filtered_df = filtered_df[
        filtered_df[['genres','genres.1','genres.2','genres.3','genres.4']]
        .apply(lambda row: any(g in row.values for g in selected_genres), axis=1)
    ]

# ===== MOSTRAR RESULTADOS =====
if not title_search and not selected_genres:
    st.markdown('<p class="centered-message">👉 Empieza buscando una película o selecciona un género.</p>', unsafe_allow_html=True)
else:
    if filtered_df.empty:
        st.warning("No se encontraron películas con esos filtros 😢")
    else:
        cols = st.columns(6)

           # ===== CLASIFICAR Reemplaza  , por un  . en RATING =====
             try:
                 rating = float(str(rating).replace(',', '.'))
             except:
                 rating = None

        for i, (_, row) in enumerate(filtered_df.iterrows()):
            tmdb_link = row["LINK TMDBLD"]
            tmdb_id = tmdb_link.split("/")[-1] if tmdb_link else None
            rating = row.get("rating", None)

         
            # ===== CLASIFICAR RATING =====
            if pd.isna(rating):
                rating_html = '<div class="rating-badge rating-medium">⭐ N/A</div>'
            elif rating >= 4:
                rating_html = f'<div class="rating-badge rating-good">🟢 {rating:.1f}</div>'
            elif rating >= 2.5:
                rating_html = f'<div class="rating-badge rating-medium">🟡 {rating:.1f}</div>'
            else:
                rating_html = f'<div class="rating-badge rating-bad">🔴 {rating:.1f}</div>'

            # ===== POSTER =====
            poster_url = None
            if tmdb_id:
                try:
                    response = requests.get(
                        f"https://api.themoviedb.org/3/movie/{tmdb_id}",
                        params={"api_key": "d2006726b1679b1f1ed8deb5e583fdc1", "language": "es-ES"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        poster_path = data.get("poster_path")
                        if poster_path:
                            poster_url = f"https://image.tmdb.org/t/p/w300{poster_path}"
                except:
                    pass

            with cols[i % 6]:
                if poster_url:
                    st.markdown(
                        f"""
                        <div class="movie-card">
                            <img src="{poster_url}" width="100%">
                            {rating_html}
                            <div class="overlay">
                                <a href="{tmdb_link}" target="_blank">Ver ficha</a>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.write("🎞️ Sin póster disponible")
