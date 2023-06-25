import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO

# Fonction pour charger une base de données à partir d'un fichier
def charger_base_de_donnees(fichier):
    extension = fichier.name.split(".")[-1]
    if extension.lower() in ["xlsx", "xls"]:
        return pd.read_excel(fichier)
    elif extension.lower() == "csv":
        return pd.read_csv(fichier)
    elif extension.lower() == "txt":
        return pd.read_csv(fichier, delimiter="\t")
    else:
        raise ValueError("Format de fichier non pris en charge.")

# Fonction pour effectuer le nettoyage des données (valeurs aberrantes)
def nettoyer_donnees_aberrantes(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    data = data[~((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR))).any(axis=1)]
    return data

# Fonction pour effectuer le nettoyage des données (valeurs manquantes)
def nettoyer_donnees_manquantes(data, method):
    if method == "Supprimer":
        data = data.dropna()
    elif method == "Médiane":
        data = data.fillna(data.median())
    elif method == "Moyenne":
        data = data.fillna(data.mean())
    return data

# Fonction pour afficher les statistiques des données
def afficher_statistiques(data):
    st.subheader("Statistiques des données")
    st.write("Nombre de valeurs manquantes :", data.isnull().sum().sum())
    st.write("Moyenne :", data.mean())
    st.write("Médiane :", data.median())
    st.write("Nombre de lignes :", data.shape[0])
    st.write("Nombre de variables :", data.shape[1])
    st.write("Plus de statistiques:",data.describe())
    st.write("Plus d'informations:")
    st.write(data.types())

# Fonction pour afficher les boîtes à moustaches des colonnes
def afficher_boites_a_moustaches(data):
    st.subheader("Boîtes à moustaches")
    selected_columns = st.multiselect("Sélectionner les variables", data.columns, key="boites_a_moustaches")
    
    if len(selected_columns) >= 2:
        fig, ax = plt.subplots()
        data[selected_columns].boxplot()
        st.pyplot(fig)
    elif len(selected_columns) == 1:
        column = selected_columns[0]
        if data[column].dtype != "object":
            fig, ax = plt.subplots()
            ax.boxplot(data[column].dropna())
            ax.set_title(column)
            st.pyplot(fig)
        else:
            st.write("La variable sélectionnée ne contient pas de données numériques.")
    else:
        st.write("veuillez sélectionner au moins une variable")

# Fonction pour créer les tableaux de bord
def creer_tableaux_de_bord(data):
    st.subheader("Les graphiques")
    selected_columns = st.multiselect("Sélectionner les variables", data.columns, key="tableaux_de_bord")
    
    if len(selected_columns) > 0:
        for column in selected_columns:
            st.subheader(f"Diagrammes pour la variable {column}")
            chart_types = st.multiselect("Sélectionner les types de diagrammes", ("Circulaire", "Bâtons"), key=f"{column}_chart_types")
            
            if "Circulaire" in chart_types:
                st.subheader("Diagramme circulaire")
                if data[column].dtype == "object":
                    fig, ax = plt.subplots()
                    data[column].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax)
                    ax.set_aspect('equal')
                    ax.set_title(column)
                    st.pyplot(fig)
                else:
                    st.write("La variable sélectionnée ne contient pas de données catégorielles.")
            
            if "Bâtons" in chart_types:
                st.subheader("Diagramme en bâtons")
                if data[column].dtype == "object":
                    fig, ax = plt.subplots()
                    data[column].value_counts().plot(kind='bar', ax=ax)
                    ax.set_title(column)
                    st.pyplot(fig)
                else:
                    st.write("La variable sélectionnée ne contient pas de données catégorielles.")

def charger_base_de_donnees_en_ligne(url):
    response = requests.get(url)
    content = response.content.decode('utf-8')
    return pd.read_csv(StringIO(content), delimiter=';', decimal=',', error_bad_lines=False)

# Page d'accueil
def page_accueil():
    st.title("Automatisez vos tâches fastidueuses")
    st.write("Bienvenue ! Veuillez sélectionner une base de données à analyser.")

    option = st.radio("Choisir une option", ("Charger une base de données locale", "Utiliser une base de données en ligne"))
    
    if option == "Charger une base de données locale":
        fichier = st.file_uploader("Sélectionner un fichier", type=["xlsx", "xls", "csv", "txt"])
        
        if fichier is not None:
            try:
                data = charger_base_de_donnees(fichier)
                
                # Affichage de la base de données initiale
                st.subheader("Base de données initiale")
                st.write(data)
                st.subheader("les premières lignes de la base de données:")
                st.write(data.head())
                st.subheader("les dernières lignes de la base de données:")
                st.write(data.tail())
            except Exception as e:
                st.error("Veuillez sélectionner des données tabulaires : {}".format(str(e)))
            
            # Supprimer des colonnes
            st.subheader("Eliminer des variables")
            selected_columns = st.multiselect("Sélectionner les variables à éliminer", data.columns)
            data = data.drop(columns=selected_columns)
            
            # Affichage des statistiques initiales
            afficher_statistiques(data)
            
            # Nettoyage des données aberrantes
            if st.button("Les valeurs aberrantes"):
                data = nettoyer_donnees_aberrantes(data)
                st.write("Nombre de données aberrantes :", data.isnull().sum())
            
            # Nettoyage des valeurs manquantes
            st.subheader("traitement des valeurs manquantes")
            nettoyage_method = st.selectbox("Méthode de traitement", ("Supprimer", "Remplir avec la médiane", "Remplir avec la moyenne"))
            if nettoyage_method != "Supprimer":
                data = nettoyer_donnees_manquantes(data, nettoyage_method)
                st.write("Nombre de valeurs manquantes après traitement:", data.isnull().sum())
            else:
                st.write("Nombre de valeurs manquantes après traitement :", data.isnull().sum())
            
            # Affichage de la base de données résultante
            st.subheader("Base de données résultante")
            st.write(data)
            
            return data
    
    elif option == "Utiliser une base de données en ligne":
        base_donnees_en_ligne = st.radio("Nous vous proposons cette base de données synthétique:", ("Données commerciales",))
        if base_donnees_en_ligne == "Données commerciales":
            # Charger la base de données en ligne (exemple avec base Commerciale)
            url = "https://raw.githubusercontent.com/robertmessan/lunettes_parlantes/main/data_bd.csv"  # Remplacer l'URL par l'URL réelle de la base de données en ligne
            try:
                data = charger_base_de_donnees_en_ligne(url)
                st.subheader("Base de données initiale :")
                st.write(data)
                st.subheader("les premières lignes de la base de données:")
                st.write(data.head())
                st.subheader("les dernières lignes de la base de données:")
                st.write(data.tail())
                # Reste du code pour le nettoyage des données et la création des tableaux de bord

            except Exception as e:
                st.error("Erreur lors du chargement de la base de données : {}".format(str(e)))
            
            # Affichage de la base de données initiale
            #st.subheader("Base de données initiale")
            #st.write(data.head())
            
            # Supprimer des colonnes
            st.subheader("Eliminer des colonnes")
            selected_columns = st.multiselect("Sélectionner les variables à éliminer", data.columns)
            data = data.drop(columns=selected_columns)
            
            # Affichage des statistiques initiales
            afficher_statistiques(data)
            
            # Nettoyage des données aberrantes
            if st.button("Supprimer les données aberrantes"):
                data = nettoyer_donnees_aberrantes(data)
                st.write("Nombre de données aberrantes :", data.isnull().sum().sum())
            
            # Nettoyage des valeurs manquantes
            st.subheader("Nettoyage des valeurs manquantes")
            nettoyage_method = st.selectbox("Méthode de nettoyage", ("Supprimer", "Remplir avec la médiane", "Remplir avec la moyenne"))
            if nettoyage_method != "Supprimer":
                data = nettoyer_donnees_manquantes(data, nettoyage_method)
                st.write("Nombre de valeurs manquantes :", data.isnull().sum().sum())
            else:
                st.write("Nombre de valeurs manquantes :", data.isnull().sum().sum())
            # Affichage de la base de données résultante
            st.subheader("Base de données résultante")
            st.write(data)
            
            return data

# Main
def main():
    # Configuration de la mise en page de Streamlit
    st.set_page_config(page_title="Automatisez vos tâches fastidueuses", layout="wide")
    
    # Page d'accueil
    data = page_accueil()
    
    if data is not None:
        # Affichage des boîtes à moustaches
        afficher_boites_a_moustaches(data)
        
        # Création des tableaux de bord
        creer_tableaux_de_bord(data)

if __name__ == "__main__":
    main()

st.markdown("Réalisé avec💖par Robert ")  
    
#hide_streamlit_style = """
            #<style>
            #MainMenu {visibility: hidden;}
            #footer {visibility: hidden;}
            #</style>
            #"""
#st.markdown(hide_streamlit_style, unsafe_allow_html=True)'''
