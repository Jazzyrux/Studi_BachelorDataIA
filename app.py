from flask import Flask, render_template, request, Response, redirect, url_for, session, flash
import psycopg2
import csv
import io
import matplotlib.pyplot as plt
import base64
import secrets
import string

app = Flask(__name__)
def generate_secret_key(length=24):
    characters = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(characters) for i in range(length))
    return secret_key

app.secret_key = generate_secret_key()

db_params = {
    'host': 'localhost',
    'database': 'dataDb',
    'user': 'postgres',
    'password': '066202'
}



def extract_data():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    cursor.execute("""
        WITH ClientDepenses AS (
            SELECT 
                DonneesClient.categorie_socio,
                Collecte.client_id,
                SUM(Collecte.montant_depense) AS depense_totale_client
            FROM DonneesClient
            JOIN Collecte ON DonneesClient.id = Collecte.client_id
            GROUP BY DonneesClient.categorie_socio, Collecte.client_id
        )

        SELECT 
            categorie_socio,
            SUM(depense_totale_client) AS depenses_totales,
            AVG(depense_totale_client) AS depense_moyenne
        FROM ClientDepenses
        GROUP BY categorie_socio
        ORDER BY categorie_socio;
    """)

    data = cursor.fetchall()
    conn.close()
    return data


def generate_graph(data):
    categories, depenses_totales, depenses_moyennes = [], [], []

    for row in data:
        categories.append(row[0])
        depenses_totales.append(row[1])
        depenses_moyennes.append(row[2])

    # Graphique pour les dépenses totales
    fig1, ax1 = plt.subplots(figsize=(6, 6))
    ax1.bar(categories, depenses_totales)
    ax1.set_xlabel('Catégorie Socioprofessionnelle')
    ax1.set_ylabel('Dépenses Totales')
    ax1.set_title('Dépenses Totales par Catégorie Socioprofessionnelle')
    ax1.tick_params(axis='x', rotation=45)

    buffer1 = io.BytesIO()
    plt.savefig(buffer1, format='png')
    buffer1.seek(0)
    img_data_totales = base64.b64encode(buffer1.read()).decode()
    buffer1.close()

    # Graphique pour les dépenses moyennes
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    ax2.bar(categories, depenses_moyennes)
    ax2.set_xlabel('Catégorie Socioprofessionnelle')
    ax2.set_ylabel('Dépense Moyenne')
    ax2.set_title('Dépense Moyenne par Catégorie Socioprofessionnelle')
    ax2.tick_params(axis='x', rotation=45)

    buffer2 = io.BytesIO()
    plt.savefig(buffer2, format='png')
    buffer2.seek(0)
    img_data_moyennes = base64.b64encode(buffer2.read()).decode()
    buffer2.close()

    return categories, depenses_totales, depenses_moyennes, img_data_totales, img_data_moyennes


@app.route('/')
def afficher_graphiques():
    if 'user_id' not in session:
        flash('Vous devez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))  # Redirigez vers la page de connexion

    data = extract_data()
    categories, depenses_totales, depenses_moyennes, img_data_totales, img_data_moyennes = generate_graph(data)


    user_role = session.get('user_role', None)

    return render_template('graphiques.html', img_data_totales=img_data_totales, img_data_moyennes=img_data_moyennes,
                           categories=categories, depenses_totales=depenses_totales,
                           depenses_moyennes=depenses_moyennes, user_role=user_role)


@app.route('/exporter', methods=['GET', 'POST'])
def exporter_data():
    if 'user_id' not in session:
        flash('Vous devez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))  # Redirigez vers la page de connexion

    if request.method == 'GET':
        return render_template('export.html')
    elif request.method == 'POST':
        nombre_lignes = int(request.form['nombre_lignes'])

        # Extraction des données de la base de données
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Collecte LIMIT %s", (nombre_lignes,))
        data = cursor.fetchall()
        fieldnames = [desc[0] for desc in cursor.description]  # Obtention des noms des colonnes
        conn.close()

        # Création d'une réponse CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(fieldnames)
        writer.writerows(data)

        output.seek(0)
        return Response(output, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment;filename=collecte_data.csv"})



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['user_role'] = user[4]
            flash('Connexion réussie', 'success')
            return redirect(url_for('afficher_graphiques'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')

    return render_template('login.html')



users = [
    {'username': 'jules', 'password': '1234567890', 'email': 'jules@example.com', 'role': 'admin'},

]


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']

        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, email, role)
            VALUES (%s, %s, %s, %s)
        """, (username, password, email, role))
        conn.commit()
        conn.close()

        flash('Registration successful', 'success')

        return redirect(url_for('afficher_graphiques'))

    return render_template('registration.html')

if __name__ == '__main__':
    app.run(debug=True)
 
