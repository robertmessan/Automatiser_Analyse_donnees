import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO
import io
import base64
import time

# Fonction pour charger une base de données à partir d'un fichier
def charger_base_de_donnees(fichier):
    extension = fichier.name.split(".")[-1]
    if extension.lower() in ["xlsx", "xls"]:
        return pd.read_excel(fichier)
    elif extension.lower() == "csv":
        fichier.seek(0)  # Remettre le curseur au début du fichier
        premiere_ligne = fichier.readline().decode().strip()  # Lire et décoder la première ligne
        if premiere_ligne == "":
            raise pd.errors.EmptyDataError("Fichier vide!")
        delimiter = ","
        if ";" in premiere_ligne:
            delimiter = ";"
        fichier.seek(0)  # Remettre le curseur au début du fichier
        return pd.read_csv(fichier, delimiter=delimiter)
    elif extension.lower() == "txt":
        return pd.read_table(fichier, delimiter="\s+")
    else:
        raise ValueError("Format de fichier non pris en charge.")
#fonction pour convertir le type des variables
def convert_column_type(columns, new_types, data):
    try:
        for column, new_type in zip(columns, new_types):
            if new_type == 'flottant':
                data[column] = data[column].astype(float)
            elif new_type == 'entier':
                data[column] = data[column].astype(int)
            elif new_type == 'double':
                data[column] = data[column].astype(float)
            elif new_type == 'chaine_caractère':
                data[column] = data[column].astype(str)
            elif new_type == 'date':
                data[column] = pd.to_datetime(data[column])
            elif new_type == 'booléen':
                data[column] = data[column].astype(bool)
    except ValueError:
        st.error("Impossible de convertir la colonnes. Assurez-vous que toutes les valeurs sont dans des formats compatibles.")
    return data

# Fonction pour effectuer le nettoyage des données (valeurs aberrantes)
def nettoyer_donnees_aberrantes(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR))).any(axis=1)
    data = data[~((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR))).any(axis=1)]
    aberrant_data = data[outliers]
    num_aberrant_values = aberrant_data.sum(axis=0)
    st.write('Nombre de valeurs aberrantes après traitement:')
    st.write(num_aberrant_values)
    return data

# Fonction pour effectuer le nettoyage des données (valeurs manquantes)
def nettoyer_donnees_manquantes(data, method):
    if method == "Supprimer":
        data = data.dropna()
    elif method == "Remplir avec la médiane":
        data = data.fillna(data.median())
    elif method == "Remplir avec la moyenne":
        data = data.fillna(data.mean())
    return data

# Fonction pour afficher les statistiques des données
def afficher_statistiques(data):
    st.write("Nombre de valeurs manquantes :", data.isnull().sum())
    st.write("Moyenne :", data.mean())
    st.write("Médiane :", data.median())
    st.write("Nombre de lignes :", data.shape[0])
    st.write("Nombre de variables :", data.shape[1])
    st.write("nombre de doublons sur les lignes:",data.shape[0]-len(data.drop_duplicates()))
    st.write("nombre de doublons sur les colonnes:",data.shape[1]-len(data.nunique()))
    st.write("Plus de statistiques:",data.describe())
    st.write("Plus d'informations:")
    st.write(data.dtypes)

# Fonction pour afficher les boîtes à moustaches des colonnes
def afficher_boites_a_moustaches(data):
    st.subheader("Boîtes à moustaches")
    selected_columns = st.multiselect("Sélectionner les variables", data.columns, key="boites_a_moustaches")
    
    if len(selected_columns) >= 2:
        fig, ax = plt.subplots()
        try:
            data[selected_columns].boxplot()
            st.pyplot(fig)
        except Exception as e:
            st.error("Au moins une variable doit être numérique")
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
        st.write("veuillez sélectionner au moins une variable numérique")

# Fonction pour créer les tableaux de bord
def creer_tableaux_de_bord(data):
    st.subheader("Les graphiques")
    selected_columns = st.multiselect("Sélectionner les variables", data.columns, key="tableaux_de_bord")
    
    if len(selected_columns) > 0:
        for column in selected_columns:
            st.subheader(f"Diagrammes pour la variable {column}")
            chart_types = st.multiselect("Sélectionner les types de diagrammes", ("Circulaire", "Bâtons"), key=f"{column}_chart_types")
            
            if "Circulaire" in chart_types:
                st.markdown('<h1 style="color: green;">Diagramme circulaire</h1>', unsafe_allow_html=True)
                if data[column].dtype == "object":
                    fig, ax = plt.subplots()
                    data[column].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax)
                    ax.set_aspect('equal')
                    ax.set_title(column)
                    st.pyplot(fig)
                else:
                    st.write("La variable sélectionnée ne contient pas de données catégorielles.")
            
            if "Bâtons" in chart_types:
                st.markdown('<h1 style="color: green;">Diagramme en bâtons</h1>', unsafe_allow_html=True)
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
    st.title("Automatisez vos tâches fastidueuses du process data")
    st.markdown('<h2 style="color: blue;">Bienvenue ! Veuillez sélectionner une base de données à analyser.</h2>', unsafe_allow_html=True)

    option = st.radio("Choisir une option", ("Charger une base de données locale", "Utiliser une base de données en ligne"))
    
    if option == "Charger une base de données locale":
        fichier = st.file_uploader("Sélectionner un fichier(tabulaire)", type=["xlsx", "xls", "csv", "txt"])
        
        if fichier is not None:
            try:
                data = charger_base_de_donnees(fichier)
                
                # Affichage de la base de données initiale
                st.subheader("Base de données initiale")
                st.write(data)
                st.markdown('<h2 style="color: blue;">les premières lignes de la base de données:</h2>', unsafe_allow_html=True)
                st.write(data.head())
                st.markdown('<h2 style="color: blue;">les dernières lignes de la base de données:</h2>', unsafe_allow_html=True)
                st.write(data.tail())
            except Exception as e:
                st.error("Veuillez sélectionner des données tabulaires ")
            
            # Supprimer des colonnes
            try:
                st.markdown('<h2 style="color: green;">Les statistiques de la base de données initiale</h2>', unsafe_allow_html=True)
                afficher_statistiques(data)
                # Supprimer des colonnes
                st.subheader("Supprimer des colonnes")
                selected_columns = st.multiselect("Sélectionner les variables à supprimer", data.columns)
                data = data.drop(columns=selected_columns)
    
                # Suppression de lignes sélectionnées
                st.subheader("Éliminer des lignes sélectionnées")
                selected_rows = st.multiselect("Sélectionner les lignes à éliminer", data.index)
                data = data.drop(index=selected_rows)
    
                # Suppression d'un nombre précis de lignes
                st.subheader("Éliminer un nombre précis de lignes")
                delete_option = st.selectbox("Sélectionner l'option de suppression", ["Au début", "À la fin", "Au milieu"])
                num_rows = st.number_input("Nombre de lignes à supprimer", min_value=0, max_value=len(data), step=1)
    
                if delete_option == "Au début":
                    data = data.iloc[num_rows:]
                elif delete_option == "À la fin":
                    data = data.iloc[:-num_rows]
                elif delete_option == "Au milieu":
                    start_index = len(data) // 2 - num_rows // 2
                    end_index = start_index + num_rows
                    data = data.drop(index=data.index[start_index:end_index])
                #convertir les types des colonnes
                st.subheader("Transformer les types des colonnes:")
                st.markdown('<span style="color: red;">Assurez-vous que les valeurs de la colonnes correspondent bien au type choisi</span>', unsafe_allow_html=True)
                selected_columns = st.multiselect("Sélectionner les colonnes à convertir", data.columns, key="select_columns")
        
                # Sélectionner les nouveaux types pour chaque colonne
                new_types = []
                for column in selected_columns:
                    new_type = st.selectbox(f"Sélectionner le nouveau type pour la colonne {column}", ["flottant", "entier", "double", "chaine_caractère", "date", "booléen"], key=f"select_type_{column}")
                    new_types.append(new_type)
        
                # Convertir les colonnes
                data = convert_column_type(selected_columns, new_types, data)                
                # Affichage des statistiques transformées
                st.markdown('<h2 style="color: green;">Les statistiques de la base de données transformée</h2>', unsafe_allow_html=True)
                afficher_statistiques(data)
            
                # Nettoyage des données aberrantes
                if st.button("Supprimer les valeurs aberrantes"):
                    data = nettoyer_donnees_aberrantes(data)
                    
            except Exception as e:
                st.error("Les données n'ont pas été correctement chargées.")
            # Nettoyage des valeurs manquantes
            st.markdown('<h2 style="color: blue;">traitement des valeurs manquantes</h2>', unsafe_allow_html=True)
            try:
                nettoyage_method = st.selectbox("Méthode de traitement", ("Supprimer", "Remplir avec la médiane", "Remplir avec la moyenne"))
                if nettoyage_method != "Supprimer":
                    data = nettoyer_donnees_manquantes(data, nettoyage_method)
                    st.write("Nombre de valeurs manquantes après traitement:", data.isnull().sum())
                else:
                    data = nettoyer_donnees_manquantes(data, nettoyage_method)
                    st.write("Nombre de valeurs manquantes après traitement :", data.isnull().sum())
            except Exception as e:
                st.error("Veuillez vous assurer que la structure de votre bd est la bonne!")
            # Affichage de la base de données résultante

            try:
                st.markdown('<h2 style="color: blue;">Base de données résultante</h2>', unsafe_allow_html=True)
                st.write(data)
                #renommer des colonnes
                st.subheader("Renommer les noms des colonnes")
                st.markdown('<span style="color: red;">Attention!, assurez-vous que cela ne causera pas de problème d\'intégrité!</span>', unsafe_allow_html=True)
                colonnes_a_modifier = st.multiselect("Sélectionnez les colonnes à renommer", data.columns.tolist())
    
                # Affichage de la base de données dans un tableau interactif avec les noms de colonnes modifiables
    
                # Création d'une liste pour stocker les nouveaux noms de colonnes
                noms_colonnes_modifies = data.columns.tolist()
    
                # Création d'un dictionnaire pour stocker les éléments interactifs (input) associés aux colonnes
                input_elements = {}
    
                # Affichage de la base de données dans un tableau interactif avec des noms de colonnes modifiables
                for colonne in data.columns:
                    if colonne in colonnes_a_modifier:
                        input_elements[colonne] = st.empty()
                        input_value = input_elements[colonne].text_input(colonne, value=colonne, key=colonne)
                        
                        # Mise à jour du nouveau nom de colonne dans la liste
                        noms_colonnes_modifies[data.columns.get_loc(colonne)] = input_value
    
                # Renommer les colonnes avec les nouveaux noms
                data.columns = noms_colonnes_modifies
    
                # Bouton pour déclencher la modification
                if st.button("Renommer les colonnes"):
                    st.markdown('<h2 style="color: green;">Base de données avec colonnes renommées</h2>', unsafe_allow_html=True)
                    st.write(data)
                    # Téléchargement de la base de données résultante
                download_format = st.selectbox("Sélectionner le format de téléchargement", ["CSV", "XLSX", "XLS", "TXT"])
                if st.button("Télécharger la base de données"):
                    if download_format == "CSV":
                        csv_data = data_editable.to_csv(index=False)
                        file_extension = "csv"
                    elif download_format == "XLSX":
                        excel_data = io.BytesIO()
                        with pd.ExcelWriter(excel_data, engine="xlsxwriter") as writer:
                            data_editable.to_excel(writer, index=False)
                        excel_data.seek(0)
                        file_extension = "xlsx"
                    elif download_format == "XLS":
                        excel_data = io.BytesIO()
                        with pd.ExcelWriter(excel_data, engine="openpyxl") as writer:
                            data_editable.to_excel(writer, index=False)
                        excel_data.seek(0)
                        file_extension = "xls"
                    elif download_format == "TXT":
                        csv_data = data_editable.to_csv(index=False, sep="\t")
                        file_extension = "txt"
    
                    if download_format in ["CSV", "TXT"]:
                        b64 = base64.b64encode(csv_data.encode()).decode()
                    else:
                        b64 = base64.b64encode(excel_data.read()).decode()
                        excel_data.close()
    
                    href = f'<a href="data:file/{file_extension};base64,{b64}" download="resultat.{file_extension}">Obtenir</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    data=data_editable
                return data
            except Exception as e:
                st.error("Merci de recharger une base de données tabulaire! ")   
    elif option == "Utiliser une base de données en ligne":
        base_donnees_en_ligne = st.radio("Nous vous proposons cette base de données synthétique:", ("Données commerciales",))
        if base_donnees_en_ligne == "Données commerciales":
            # Charger la base de données en ligne (exemple avec base Commerciale)
            url = "https://raw.githubusercontent.com/robertmessan/lunettes_parlantes/main/data_bd.csv"  # Remplacer l'URL par l'URL réelle de la base de données en ligne
            try:
                data = charger_base_de_donnees_en_ligne(url)
                st.subheader("Base de données initiale :")
                st.write(data)
                st.markdown('<h1 style="color: blue;">les premières lignes de la base de données:</h1>', unsafe_allow_html=True)
                st.write(data.head())
                st.markdown('<h1 style="color: blue;">les dernières lignes de la base de données:</h1>', unsafe_allow_html=True)
                st.write(data.tail())
                # Reste du code pour le nettoyage des données et la création des tableaux de bord

            except Exception as e:
                st.error("Erreur lors du chargement de la base de données .")
            
            # Affichage de la base de données initiale
            #st.subheader("Base de données initiale")
            #st.write(data.head())
            
            # Supprimer des colonnes
            st.markdown('<h2 style="color: green;">Les statistiques de la base de données initiale</h2>', unsafe_allow_html=True)
            afficher_statistiques(data)
            # Supprimer des colonnes
            st.subheader("Supprimer des colonnes")
            selected_columns = st.multiselect("Sélectionner les variables à supprimer", data.columns)
            data = data.drop(columns=selected_columns)

            # Suppression de lignes sélectionnées
            st.subheader("Éliminer des lignes sélectionnées")
            selected_rows = st.multiselect("Sélectionner les lignes à éliminer", data.index)
            data = data.drop(index=selected_rows)

            # Suppression d'un nombre précis de lignes
            st.subheader("Éliminer un nombre précis de lignes")
            delete_option = st.selectbox("Sélectionner l'option de suppression", ["Au début", "À la fin", "Au milieu"])
            num_rows = st.number_input("Nombre de lignes à supprimer", min_value=0, max_value=len(data), step=1)

            if delete_option == "Au début":
                data = data.iloc[num_rows:]
            elif delete_option == "À la fin":
                data = data.iloc[:-num_rows]
            elif delete_option == "Au milieu":
                start_index = len(data) // 2 - num_rows // 2
                end_index = start_index + num_rows
                data = data.drop(index=data.index[start_index:end_index])
            
            # Affichage des statistiques initiales
            st.markdown('<h2 style="color: green;">Les statistiques de la base de données transformée</h2>', unsafe_allow_html=True)
            afficher_statistiques(data)
            
            # Nettoyage des données aberrantes
            if st.button("Supprimer les données aberrantes"):
                data = nettoyer_donnees_aberrantes(data)
                st.write("Nombre de données aberrantes après traitement :", data.isnull().sum())
            
            # Nettoyage des valeurs manquantes
            st.markdown('<h2 style="color: blue;">traitement des valeurs manquantes</h2>', unsafe_allow_html=True)
            nettoyage_method = st.selectbox("Méthode de traitement", ("Supprimer", "Remplir avec la médiane", "Remplir avec la moyenne"))
            if nettoyage_method != "Supprimer":
                data = nettoyer_donnees_manquantes(data, nettoyage_method)
                st.write("Nombre de valeurs manquantes :", data.isnull().sum())
            else:
                st.write("Nombre de valeurs manquantes :", data.isnull().sum())
            st.markdown('<h2 style="color: blue;">Base de données résultante</h2>', unsafe_allow_html=True)
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

phrase = "Réalisé avec💖par Robert"
phrase_affichee = st.empty()
for i in range(len(phrase)):
    phrase_affichee.subheader(phrase[:i+1])
    time.sleep(0.01)

st.markdown('<h2 style="color: purple;">Si vous avez des propositions, n\'hésitez surtout pas. Envoyez moi un petit message sympa😊 et je vous réponds!</h2>', unsafe_allow_html=True)
st.markdown("[Mon profil](https://www.linkedin.com/in/kossi-robert-messan-252954223/)")
hide_streamlit_style = """
            <style>
            MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
