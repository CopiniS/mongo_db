## Instruções para execução
##Instalar dependenca com: pip install requests pymongo python-dotenv
## fazer um .env na raiz com essas variaveis:
## STRING_CONECT_MONGO
## DB_NAME
## API_KEY
## criar a API_KEY em: https://developer.themoviedb.org/reference/intro/getting-started

import requests
import random
from pymongo import MongoClient
from datetime import datetime
import time
from dotenv import load_dotenv
import os

load_dotenv()   

client = MongoClient(os.getenv("STRING_CONECT_MONGO"))
db = client[os.getenv("DB_NAME")]
collection = db["filmes"]

print(client.list_database_names())

api_key = os.getenv("API_KEY")
base_url = "https://api.themoviedb.org/3"
headers = {
    "accept": "application/json",
    "Authorization": api_key
}

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

def insert_number_last_page_file(number):
    with open(file_name, "w") as file:
        file.write(str(number))
    print(f"File 'last_save_page' was created with value {str(number)}.")

def look_last_saved_page():
    if not os.path.exists(file_name):
        insert_number_last_page_file(1)
        return 1

    with open(file_name, "r") as file:
        saved_page = file.read().strip()

    if not saved_page.isdigit():
        print("The saved page file, is not correct.")
        insert_number_last_page_file(1)
        return 1

    number = int(saved_page)
    return number


total_inseridos = 0
#FOI ATE A PAGINA 501 com 9981 dados, daí reiniciou da pagina 1

file_name = "last_saved_page.txt"
while total_inseridos < 10000:
    page = look_last_saved_page()
    movies = get_popular_movies(page)
    if not movies:
        break
    
    insert_number_last_page_file(page+1)

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

print("Finalizado. Total inserido:", total_inseridos)
