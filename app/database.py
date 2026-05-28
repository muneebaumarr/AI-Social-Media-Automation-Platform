from SQLALCHEMY import create_engine, text
from SQLALCHEMY.orm import sessionmaker 
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from urllib.parse import quote_plus


#build SQL CONNECTIOn url
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

#Create SQLALCHEMY engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

#Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db():
    """
    Dependency Function.
    Every request that needs database access will call this function to get a session.
    Automatically closes the session after the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """"
    Tests the database connection by executing a simple query.
    If the connection is successful, it will print "Database connection successful!".
    Else, it will print the error message.
    
    """

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT DATABASE()"))
            db_name = result.Fetchone()[0]
            print(f"Database connection successful! Connected to database: {db_name}")  

            #count tables in the database
            result = connection.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"Number of tables in the database: {len(tables)}")
            for table in tables:
                print(f" - {table[0]}")
    except Exception as e:
        print(f"Database connection failed: {e}")
        


 