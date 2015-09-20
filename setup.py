import os
import reviews
from reviews import db, create_user, model

db.drop_all()
db.create_all()

admin = create_user('admin', 'admin@example.com', 'password', is_admin=True)

cat = model.Category('ginger-beer')
rev = model.Review("Ben's Ginger Beer",10,cat,admin)

db.session.add(cat)
db.session.add(admin)
db.session.commit()

