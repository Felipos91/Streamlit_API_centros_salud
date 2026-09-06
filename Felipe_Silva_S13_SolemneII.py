import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# Información que aparece en la pestaña
st.set_page_config(page_title="Análisis Establecimientos de Salud", layout="wide")
#Información que aparece en el header
st.title("Análisis de Establecimientos de Salud en Chile")
st.markdown("Datos obtenidos vía API desde datos.gob.cl (Ministerio de Salud)")

# URL de la API
API_URL = "https://datos.gob.cl/api/3/action/datastore_search?resource_id=2c44d782-3365-44e3-aefb-2c8b8363a1bc&limit=6000"
#Decorador utilizado para almacenar la info en caché
@st.cache_data
def cargar_datos():
    #Manejo de errores en caso de que no haya conexión con la api
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        #Si hay conexión exitosa, obtenemos los datos
        if data.get("success"):
            #Los datos se encuentran en ["result"]["records"]
            df = pd.DataFrame(data["result"]["records"])
            
            columnas_seleccionar = [
                'RegionGlosa', 'ComunaGlosa', 'TipoEstablecimientoGlosa', 
                'DependenciaAdministrativa', 'NivelComplejidadEstabGlosa', 
                'EstadoFuncionamiento', 'TipoSistemaSaludGlosa'
            ]
            columnas_seleccionadas = [c for c in columnas_seleccionar if c in df.columns]
            df = df[columnas_seleccionadas]
            #Filtramos para obtener los datos de los establecimientos que estan funcionando
            if 'EstadoFuncionamiento' in df.columns:
                df = df[df['EstadoFuncionamiento'] == 'Vigente en Operación Habitual']
            #Devolvemos los datos
            return df
        else:
            st.error("La API respondió con un error.")
            return None
    except Exception as e:
        st.error(f"Error al conectar con la API: {e}")
        return None

# Traemos los datos
df = cargar_datos()

# Verificamos que df no sea None antes de continuar
if df is not None and not df.empty:
    
    # SIDEBAR - FILTROS
    #En el sidebar, podemos filtrar:región, comuna,tipo_establecimiento y dependencia
    st.sidebar.header(" Filtros")
    
    #Ordenamos y seleccionamos
    regiones = sorted(df['RegionGlosa'].dropna().unique())
    region_sel = st.sidebar.multiselect("Selecciona Región(es)", options=regiones, default=regiones)
    
    #Ordenamos y seleccionamos
    comunas = sorted(df['ComunaGlosa'].dropna().unique())
    comuna_sel = st.sidebar.multiselect("Selecciona Comuna(s)", options=comunas)
    
    #Ordenamos y seleccionamos
    tipos = sorted(df['TipoEstablecimientoGlosa'].dropna().unique())
    tipo_sel = st.sidebar.multiselect("Tipo de Establecimiento", options=tipos)
    
    #Ordenamos y seleccionamos
    dependencias = sorted(df['DependenciaAdministrativa'].dropna().unique())
    dep_sel = st.sidebar.multiselect("Dependencia Administrativa", options=dependencias)
    
    # Aplicar filtros
    #Creamos una copia del dataframe original para aplicar los filtros dinámicamente
    df_f = df.copy()
    if region_sel: df_f = df_f[df_f['RegionGlosa'].isin(region_sel)]
    if comuna_sel: df_f = df_f[df_f['ComunaGlosa'].isin(comuna_sel)]
    if tipo_sel: df_f = df_f[df_f['TipoEstablecimientoGlosa'].isin(tipo_sel)]
    if dep_sel: df_f = df_f[df_f['DependenciaAdministrativa'].isin(dep_sel)]
    #Ponemos información de cuántos Datos filtrados se obtienen
    st.sidebar.info(f" Establecimientos filtrados: **{len(df_f)}**")
    
    # Verificar si hay datos después de filtrar
    if df_f.empty:
        st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados. Por favor, ajusta los filtros.")
    else:
        #Si tenemos datos, llevamos la info a una tabla y se aplica a los gráficos
        # TABLA
        st.header("📋 Tabla de Datos")
        st.dataframe(df_f.head(100), use_container_width=True, height=400)
        
        # GRÁFICOS
        #Selección dinámica del gráfico que queremos
        st.header("📊 Análisis Visual")
        tipo_grafico = st.radio("Selecciona el tipo de visualización:",
                               ["Cantidad por Región", "Cantidad por Tipo de Establecimiento", 
                                "Nivel de Complejidad"],
                               horizontal=True)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        #Generamos gráficos de barra.
        if tipo_grafico == "Cantidad por Región":
            datos = df_f['RegionGlosa'].value_counts().sort_values(ascending=False)
            if not datos.empty:
                datos.plot(kind='bar', ax=ax, color='teal', edgecolor='black')
                ax.set_title('Cantidad de Establecimientos por Región', fontsize=16, fontweight='bold')
                plt.xticks(rotation=45, ha='right')
            else:
                ax.text(0.5, 0.5, 'No hay datos para mostrar', ha='center', va='center', transform=ax.transAxes)
                
        elif tipo_grafico == "Cantidad por Tipo de Establecimiento":
            datos = df_f['TipoEstablecimientoGlosa'].value_counts().sort_values(ascending=False).head(10)
            if not datos.empty:
                datos.plot(kind='barh', ax=ax, color='coral', edgecolor='black')
                ax.set_title('Top 10 Tipos de Establecimientos', fontsize=16, fontweight='bold')
                ax.set_xlabel('Cantidad')
            else:
                ax.text(0.5, 0.5, 'No hay datos para mostrar', ha='center', va='center', transform=ax.transAxes)
                
        elif tipo_grafico == "Nivel de Complejidad":
            datos = df_f['NivelComplejidadEstabGlosa'].value_counts()
            if not datos.empty:
                datos.plot(kind='bar', ax=ax, color='purple', edgecolor='black')
                ax.set_title('Cantidad por Nivel de Complejidad', fontsize=16, fontweight='bold')
                plt.xticks(rotation=45, ha='right')
            else:
                ax.text(0.5, 0.5, 'No hay datos para mostrar', ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout()
        st.pyplot(fig)
else:
    st.error("❌ No se pudieron cargar los datos. Por favor, recarga la página o verifica tu conexión.")