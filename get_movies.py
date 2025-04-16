import requests
import random
from pymongo import MongoClient
from datetime import datetime
import time
from dotenv import load_dotenv
import os

load_dotenv()   

# Conexão MongoDB
client = MongoClient(os.getenv("STRING_CONECT_MONGO"))
db = client[os.getenv("DB_NAME")]
collection = db["filmes"]

print(client.list_database_names())

# Configurações da API
api_key = os.getenv("API_KEY")
base_url = "https://api.themoviedb.org/3"
headers = {
    "accept": "application/json",
    "Authorization": api_key
}

# Funções auxiliares
def get_popular_movies(page):
    url = f"{base_url}/movie/popular?page={page}"
    return requests.get(url, headers=headers).json().get("results", [])

def get_movie_details(movie_id):
    url = f"{base_url}/movie/{movie_id}"
    return requests.get(url, headers=headers).json()

def get_movie_credits(movie_id):
    url = f"{base_url}/movie/{movie_id}/credits"
    return requests.get(url, headers=headers).json()

def build_movie_document(movie, details, credits):
    diretor = next((c['name'] for c in credits['crew'] if c['job'] == 'Director'), "Desconhecido")
    
    atores = credits.get("cast", [])
    ator_principal = atores[0] if atores else {"name": "Desconhecido", "known_for_department": "Acting"}
    coadjuvantes = [a['name'] for a in atores[1:5]]

    ator_principal_doc = {
        "nome": ator_principal.get("name", "Desconhecido"),
        "idade": random.randint(25, 70),
        "nacionalidade": random.choice(["Americano", "Canadense", "Britânico", "Australiano"])
    }

    return {
        "titulo": movie.get("title"),
        "ano": int(movie.get("release_date", "1900-01-01")[:4]),
        "genero": details['genres'][0]['name'] if details.get('genres') else "Desconhecido",
        "diretor": diretor,
        "nota": movie.get("vote_average", 0),
        "dataLancamento": movie.get("release_date"),
        "atorPrincipal": ator_principal_doc,
        "atoresCoadjuvantes": coadjuvantes
    }

total_inseridos = 0
page = 1
while total_inseridos < 10000:
    movies = get_popular_movies(page)
    if not movies:
        break
    
    for movie in movies:
        try:
            details = get_movie_details(movie["id"])
            credits = get_movie_credits(movie["id"])
            doc = build_movie_document(movie, details, credits)
            collection.insert_one(doc)
            total_inseridos += 1
            print(f"[{total_inseridos}] Inserido: {doc['titulo']}")
            time.sleep(0.2)  # Evitar rate limit da API
            if total_inseridos >= 10000:
                break
        except Exception as e:
            print("Erro:", e)
            continue

    page += 1

print("Finalizado. Total inserido:", total_inseridos)
