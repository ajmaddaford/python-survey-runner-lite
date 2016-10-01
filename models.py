from sqlalchemy import Column, Integer, String
from database import Base

class QuestionnaireData(Base):
    __tablename__ = 'questionnaire_data'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(80), unique=True)
    data = Column(String(10000))

    def __init__(self, user_id, data):
        self.user_id = user_id
        self.data = data

    def __repr__(self):
        return '<User %r>' % self.user_id

