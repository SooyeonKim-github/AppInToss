from app.database import Base, engine, session_scope
from app.services import seed_menus_if_empty


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with session_scope() as db:
        inserted = seed_menus_if_empty(db)
    print(f"seeded={inserted}")
