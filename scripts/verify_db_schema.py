import sys
import os
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper

sys.path.append(os.getcwd())

from backend.app.db import engine
from backend.app.models import User, Referral, Subscription

def print_model_schema(model):
    print(f"\nModel: {model.__name__}")
    mapper = class_mapper(model)
    for prop in mapper.column_attrs:
        print(f"  - {prop.key}: {prop.columns[0].type}")

if __name__ == "__main__":
    print("Verifying DB Schema (SQLAlchemy Models)...")
    print_model_schema(User)
    print_model_schema(Referral)
    print_model_schema(Subscription)
