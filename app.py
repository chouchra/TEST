from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'

# ---------------------
# Données simulées
# ---------------------
users = {
    "alice":   {"password": "1234", "trust_index": 5},
    "bob":     {"password": "1234", "trust_index": 0},  # Exemple utilisateur bloqué
    "charlie": {"password": "1234", "trust_index": 8}
}

products = {
    # product_id: 
    #    name, daily_price, avg_rating_product, supplier_id, supplier_rating, image
    1: {
        "name": "Caméra GoPro",
        "daily_price": 10,
        "avg_rating_product": 4.5,
        "supplier_id": "supplierA",
        "supplier_rating": 4.8,
        "image": "https://via.placeholder.com/150x100?text=GoPro"  # Ex URL
    },
    2: {
        "name": "Tente de camping",
        "daily_price": 5,
        "avg_rating_product": 4.0,
        "supplier_id": "supplierB",
        "supplier_rating": 3.9,
        "image": "https://via.placeholder.com/150x100?text=Tente"
    }
}

suppliers = {
    # supplier_id: name, rating, image
    "supplierA": {
        "name": "Fournisseur Alpha",
        "rating": 4.8,
        "image": "https://via.placeholder.com/120x80?text=Alpha"
    },
    "supplierB": {
        "name": "Fournisseur Beta",
        "rating": 3.9,
        "image": "https://via.placeholder.com/120x80?text=Beta"
    }
}

# locations en cours ou en attente
# rental_id: {
#   product_id, user, supplier_id, days, status("pending","accepted","refused","waiting_confirmation","confirmed","finished"), 
#   user_trust_index_at_request
# }
rentals = {}
rental_id_counter = 1

# Paramétrage du calcul du prix: prix_journalier * nb_jours (paramétrable)
def calculate_price(daily_price, days):
    return daily_price * days

@app.context_processor
def inject_globals():
    """
    Rendre accessibles globalement certaines variables comme users, products, suppliers.
    Permet d'éviter de les passer à chaque render_template.
    """
    return {
        'users': users,
        'products': products,
        'suppliers': suppliers
    }

@app.route('/')
def home():
    # On affiche la page d'accueil, qui liste déjà les produits
    # (La template home.html utilisera 'products' et 'suppliers' via le context_processor)
    return render_template('home.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username]['password'] == password:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return "Identifiants incorrects"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/products')
def list_products():
    return render_template('products.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    if product_id not in products:
        return "Produit introuvable"
    return render_template('product_detail.html', product_id=product_id)

@app.route('/request_rental/<int:product_id>', methods=['GET','POST'])
def request_rental(product_id):
    if 'user' not in session:
        return "Vous devez être connecté pour louer un produit."
    username = session['user']
    if users[username]['trust_index'] == 0:
        return "Votre indice de confiance est à 0, vous ne pouvez pas louer."

    if product_id not in products:
        return "Produit introuvable."

    if request.method == 'POST':
        days = int(request.form.get('days'))
        chosen_supplier = request.form.get('supplier_id')
        price = calculate_price(products[product_id]['daily_price'], days)
        global rental_id_counter
        rental_id = rental_id_counter
        rental_id_counter += 1
        rentals[rental_id] = {
            "product_id": product_id,
            "user": username,
            "supplier_id": chosen_supplier,
            "days": days,
            "status": "pending",
            "user_trust_index_at_request": users[username]['trust_index']
        }
        return f"Demande de location envoyée (ID: {rental_id}). En attente de réponse du fournisseur."

    return render_template('request_rental.html', product_id=product_id)

@app.route('/supplier_dashboard', methods=['GET','POST'])
def supplier_dashboard():
    # Simule l'interface d'un fournisseur (on se fixe sur supplierA par exemple)
    supplier_id = "supplierA"
    supplier_requests = {
        rid: r for rid, r in rentals.items()
        if r['supplier_id'] == supplier_id and r['status'] == 'pending'
    }
    if request.method == 'POST':
        rental_id = int(request.form.get('rental_id'))
        action = request.form.get('action')
        if rental_id in rentals:
            if action == 'accept':
                rentals[rental_id]['status'] = "accepted"
            elif action == 'refuse':
                rentals[rental_id]['status'] = "refused"
    return render_template('supplier_dashboard.html', supplier_id=supplier_id, supplier_requests=supplier_requests)

@app.route('/confirm_rental/<int:rental_id>', methods=['GET','POST'])
def confirm_rental(rental_id):
    if 'user' not in session:
        return "Vous devez être connecté."
    if rental_id not in rentals:
        return "Location introuvable."
    r = rentals[rental_id]
    if r['status'] != 'accepted':
        return "Cette location n'est pas en attente de confirmation."
    if r['user'] != session['user']:
        return "Vous n'êtes pas le demandeur de cette location."

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'confirm':
            r['status'] = 'confirmed'
            return "Location confirmée. Le produit sera livré hors site."
        else:
            return "Annulé"

    return render_template('confirm_rental.html', rental_id=rental_id)

@app.route('/finish_rental/<int:rental_id>', methods=['GET','POST'])
def finish_rental(rental_id):
    # Simule la fin de la location après restitution
    if rental_id not in rentals:
        return "Location introuvable"
    r = rentals[rental_id]
    if r['status'] != 'confirmed':
        return "La location n'est pas en cours."

    if request.method == 'POST':
        product_condition = request.form.get('product_condition', 'good')
        product_rating = request.form.get('product_rating')
        supplier_rating = request.form.get('supplier_rating')

        # Mise à jour de l'indice de confiance
        if product_condition == 'bad':
            users[r['user']]['trust_index'] = max(0, users[r['user']]['trust_index'] - 1)

        # Mise à jour de la note du produit (simple moyenne)
        if product_rating:
            old_rating = products[r['product_id']]['avg_rating_product']
            new_rating = (old_rating + float(product_rating)) / 2
            products[r['product_id']]['avg_rating_product'] = new_rating

        # Mise à jour de la note du fournisseur
        if supplier_rating:
            old_s_rating = suppliers[r['supplier_id']]['rating']
            new_s_rating = (old_s_rating + float(supplier_rating)) / 2
            suppliers[r['supplier_id']]['rating'] = new_s_rating

        r['status'] = 'finished'
        return f"Location terminée. Indice de confiance final: {users[r['user']]['trust_index']}."

    return render_template('finish_rental.html', rental_id=rental_id)

if __name__ == "__main__":
    app.run(debug=True)
