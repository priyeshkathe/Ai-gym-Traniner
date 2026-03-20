import os

class Config:
    SECRET_KEY = "supersecretkey"

    SQLALCHEMY_DATABASE_URI = "sqlite:///gym.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = "jwtsecret"