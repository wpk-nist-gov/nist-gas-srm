# ruff:file-ignore[commented-out-code]

from sqlmodel import Session, SQLModel, create_engine

from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    **(
        {}
        if settings.ENGINE_CHECK_SAME_THREAD
        else {"connect_args": {"check_same_thread": settings.ENGINE_CHECK_SAME_THREAD}}
    ),
)

# print("hello", settings.ENGINE_CHECK_SAME_THREAD)
# raise ValueError


def init_db(session: Session) -> None:  # ruff:ignore[unused-function-argument]
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    from nist_gas_srm.backend import models  # ruff:ignore[unused-import]

    SQLModel.metadata.create_all(engine)

    # user = session.exec(
    #     select(User).where(User.email == settings.FIRST_SUPERUSER)
    # ).first()
    # if not user:
    #     user_in = UserCreate(
    #         email=settings.FIRST_SUPERUSER,
    #         password=settings.FIRST_SUPERUSER_PASSWORD,
    #         is_superuser=True,
    #     )
    #     user = crud.create_user(session=session, user_create=user_in)
