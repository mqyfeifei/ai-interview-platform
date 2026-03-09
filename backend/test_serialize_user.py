from app import create_app
from app.services.user_service import UserService
from app.extensions import db
from app.models.user import User

app = create_app()
with app.app_context():
    u = User.query.first()
    if u:
        print(UserService.serialize_user(u))
    else:
        print('no user')
