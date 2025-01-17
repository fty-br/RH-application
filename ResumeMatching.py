from flask import Flask, request, jsonify
import os
import pandas as pd
import pdfplumber
import mysql.connector
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import json


def extract_information_from_cv(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Chemin vers le répertoire contenant les CV PDF
cv_directory = "C:/xampp/htdocs/eris/applicant/photos"

# Liste pour stocker les informations de tous les CV
all_cv_information = []

# Parcourir tous les fichiers dans le répertoire
for filename in os.listdir(cv_directory):
    if filename.endswith(".pdf"):
        cv_path = os.path.join(cv_directory, filename)
        cv_text = extract_information_from_cv(cv_path)
        # Stocker les informations de chaque CV dans la liste
        all_cv_information.append((filename, cv_text))

# Connexion à la base de données MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    database="erisdb"  # Nom de votre base de données existante
)

cursor = conn.cursor()

# Vérifier si le CV existe déjà dans la base de données
def is_cv_processed(filename):
    cursor.execute("SELECT COUNT(*) FROM tblresume WHERE filename = %s", (filename,))
    count = cursor.fetchone()[0]
    return count > 0

# Parcourir tous les fichiers dans le répertoire
for cv_info in all_cv_information:
    filename, text = cv_info
    # Vérifier si le CV a déjà été traité
    if not is_cv_processed(filename):
        try:
            # Requête SQL pour insérer les informations du CV dans la table
            sql = "INSERT INTO tblresume (filename, text) VALUES (%s, %s)"
            val = (filename, text)
            cursor.execute(sql, val)
            conn.commit()
            print("Les informations du CV", filename, "ont été insérées avec succès dans la base de données.")
        except mysql.connector.Error as err:
            print("Erreur lors de l'insertion des informations du CV", filename, ":", err)


# Data Pre-processing Resume

# Import data 
query = "SELECT * FROM tblresume"
df = pd.read_sql(query, conn)

# Affichez les premières lignes du DataFrame
print(df.head())


# Supprimer les lignes avec des valeurs manquantes
df.dropna(inplace=True)

# Convertir le texte en minuscules
df['text'] = df['text'].str.lower()

# Supprimer les caractères spéciaux et les chiffres
df['text'] = df['text'].str.replace(r'[^a-zA-Z\s]', '', regex=True)

# Tokenization des mots
from nltk.tokenize import word_tokenize
df['text'] = df['text'].apply(word_tokenize)

# Supprimer les mots vides en anglais
from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))
df['text'] = df['text'].apply(lambda x: [word for word in x if word not in stop_words])

# Lemmatisation des mots
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
df['text'] = df['text'].apply(lambda x: [lemmatizer.lemmatize(word) for word in x])

# Reconstruire le texte nettoyé
df['text'] = df['text'].apply(lambda x: ' '.join(x))

# Affichez les premières lignes du DataFrame après le prétraitement
#print(df.head())


# Pre-Processing Job Opportunities

# Import des données depuis la table tbljob
job_query = "SELECT JOBDESCRIPTION, OCCUPATIONTITLE, QUALIFICATION_WORKEXPERIENCE FROM tbljob"
job_df = pd.read_sql(job_query, conn)

que = "SELECT * FROM tbljob"
job_db = pd.read_sql(que, conn)

# Concaténation des colonnes pertinentes pour former un seul texte représentant l'offre d'emploi
job_df['job_text'] = job_df['JOBDESCRIPTION'] + ' ' + job_df['OCCUPATIONTITLE'] + ' ' + job_df['QUALIFICATION_WORKEXPERIENCE']

# Convertir le texte en minuscules
job_df['job_text'] = job_df['job_text'].str.lower()

# Supprimer les caractères spéciaux et les chiffres
job_df['job_text'] = job_df['job_text'].str.replace(r'[^a-zA-Z\s]', '', regex=True)

# Tokenization des mots
job_df['job_text'] = job_df['job_text'].apply(word_tokenize)

# Supprimer les mots vides en anglais
job_df['job_text'] = job_df['job_text'].apply(lambda x: [word for word in x if word not in stop_words])

# Lemmatisation des mots
job_df['job_text'] = job_df['job_text'].apply(lambda x: [lemmatizer.lemmatize(word) for word in x])

# Fusionner les listes de mots en une seule chaîne de texte
job_df['job_text'] = job_df['job_text'].apply(lambda x: ' '.join(x))

print(job_df['job_text'].head())


# Vectorization

# Création du vectoriseur TF-IDF avec les mêmes paramètres pour les CV et les offres d'emploi
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', tokenizer=word_tokenize)

# Vectorisation des données des CV
cv_vectors = vectorizer.fit_transform(df['text'])

# Vectorisation des données des offres d'emploi
job_vectors = vectorizer.transform(job_df['job_text'])

# Calcul de la similarité cosinus
similarities = cosine_similarity(cv_vectors, job_vectors)

print("-----------------------------------")



# Affichage des similarités
for i, cv_filename in enumerate(df['filename']):
    for j, job_id in enumerate(job_db['JOBID']):
        similarity = similarities[i, j]
        print(f"Similarité entre {cv_filename} et l'offre d'emploi {job_id} : {similarity}")
        
   
        
 



app = Flask(__name__)

@app.route('/match')
def match():
    # Calcul de la similarité cosinus
    similarities = cosine_similarity(cv_vectors, job_vectors)

    matching_results = []

    # Construction des résultats de matching avec les valeurs de similarité réelles
    for i, cv_filename in enumerate(df['filename']):
        for j, job_id in enumerate(job_db['JOBID']):
            similarity = similarities[i, j]
            matching_results.append({"cv_job_id": f"{cv_filename}_{job_id}", "similarity": similarity})
    
    # Données pour les noms des CV - Offres d'emploi et leurs similarités correspondantes
    cv_job_ids = [result['cv_job_id'] for result in matching_results]
    similarities = [result['similarity'] for result in matching_results]

        # Générer les données du graphique
    data = {
        "cv_job_ids": cv_job_ids,
        "similarities": similarities
    }

    # Convertir les données en JSON
    graph_data_json = json.dumps(data)

    # Renvoyer les résultats sous forme de JSON
    return jsonify(matching_results)

@app.route('/validate')
def validate():
    username = request.args.get('username')
    password = request.args.get('password')
    
    if username == 'admin' and password == 'password':
        return '<h1>Correct</h1>'
    else:
        return '<h1>faux</h1>'
    
if __name__ == '__main__':
    app.run() 
    
