import psycopg2
import random

db_params = {
    'host': 'localhost',
    'database': 'dataDb',
    'user': 'postgres',
    'password': '066202'
}

categories_possibles = ['Alimentaire', 'Maison', 'Électronique', 'Vêtements', 'Multimédia']

def inserer_donnees_aleatoires():
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        client_id = 1

        for _ in range(3):
            categorie_socio = random.choice(['Étudiant', 'Professionnel', 'Retraité'])
            if categorie_socio == 'Étudiant':
                nombre_enfants = 0
            else:
                nombre_enfants = random.randint(1, 5)
            prix_panier_client = round(random.uniform(10.0, 200.0), 2)

            montant_total = prix_panier_client
            while montant_total > 0:
                categorie = random.choice(categories_possibles)
                montant_depense = round(random.uniform(1.0, montant_total), 2)
                cursor.execute(
                    "INSERT INTO Collecte (client_id, prix_total_panier, categorie, montant_depense) VALUES (%s, %s, %s, %s)",
                    (client_id, prix_panier_client, categorie, montant_depense)
                )
                montant_total -= montant_depense

            cursor.execute(
                "INSERT INTO DonneesClient (nombre_enfants, categorie_socio, prix_panier_client, collecte_id) VALUES (%s, %s, %s, %s)",
                (nombre_enfants, categorie_socio, prix_panier_client, client_id)
            )

            client_id += 1

        conn.commit()

    except Exception as e:
        print("Erreur lors de l'insertion des données :", str(e))
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inserer_donnees_aleatoires()
