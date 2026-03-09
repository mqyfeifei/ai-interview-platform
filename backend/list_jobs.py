from app import create_app
from app.models.job import Job

app = create_app()
with app.app_context():
    jobs = Job.query.all()
    for j in jobs:
        print(j.id, j.name)
