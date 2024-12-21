from location_app import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    trust_index = db.Column(db.Integer, default=5)

    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    daily_price = db.Column(db.Float, default=0.0)
    avg_rating_product = db.Column(db.Float, default=0.0)
    supplier_id = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f'<Product {self.name}>'
