from kafka import KafkaConsumer
import logging
import os
import json

from datetime import datetime
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from shapely.geometry.point import Point
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text
from sqlalchemy import BigInteger, Float, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

kafka_url = os.environ["KAFKA_URL"]
kafka_topic = os.environ["KAFKA_TOPIC"]

DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]

DB_USERNAME_LOCATION = os.environ["DB_USERNAME_LOCATION"]
DB_PASSWORD_LOCATION = os.environ["DB_PASSWORD_LOCATION"]
DB_HOST_LOCATION = os.environ["DB_HOST_LOCATION"]
DB_PORT_LOCATION = os.environ["DB_PORT_LOCATION"]
DB_NAME_LOCATION = os.environ["DB_NAME_LOCATION"]

logging.basicConfig(level=logging.INFO)

logging.info('kafka_url : %s', kafka_url)
logging.info('kafka_topic : %s', kafka_topic)

consumer = KafkaConsumer(kafka_topic, bootstrap_servers=[kafka_url])

Base = declarative_base()
connections_db = create_engine(f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}", echo=True)
SessionConn = sessionmaker(bind=connections_db)
SessionConn.configure(bind=connections_db)
connection_db = SessionConn()

locations_db = create_engine(f"postgresql://{DB_USERNAME_LOCATION}:{DB_PASSWORD_LOCATION}@{DB_HOST_LOCATION}:{DB_PORT_LOCATION}/{DB_NAME_LOCATION}", echo=True)
SessionLocation = sessionmaker(bind=locations_db)
SessionLocation.configure(bind=locations_db)
location_db = SessionLocation()

class ConnectionP(Base):
    __tablename__ = "connection"

    person_id = Column(Integer, primary_key=True)
    exposed_person_id = Column(Integer, primary_key=True)
    longitude = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    creation_time = Column(DateTime, nullable=False, default=datetime.utcnow, primary_key=True)

class Location(Base):
    __tablename__ = "location"

    id = Column(BigInteger, primary_key=True)
    person_id = Column(Integer, nullable=False)
    coordinate = Column(Geometry("POINT"), nullable=False)
    creation_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    _wkt_shape: str = None

    def wkt_shape(self) -> str:
        # Persist binary form into readable text
        if not self._wkt_shape:
            point: Point = to_shape(self.coordinate)
            # normalize WKT returned by to_wkt() from shapely and ST_AsText() from DB
            self._wkt_shape = point.to_wkt().replace("POINT ", "ST_POINT")
        return self._wkt_shape

    def wkt_shape(self, v: str) -> None:
        self._wkt_shape = v

    def set_wkt_with_coords(self, lat: str, long: str) -> str:
        self._wkt_shape = f"ST_POINT({lat} {long})"
        return self._wkt_shape

    def longitude(self) -> str:
        coord_text = self.wkt_shape
        return coord_text[coord_text.find(" ") + 1 : coord_text.find(")")]

    def latitude(self) -> str:
        coord_text = self.wkt_shape
        return coord_text[coord_text.find("(") + 1 : coord_text.find(" ")]

def process_location_connections(location):
    
    query = text(
        """
    SELECT  person_id, id, ST_X(coordinate), ST_Y(coordinate), creation_time
    FROM    location
    WHERE   ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint(:latitude,:longitude),4326)::geography, :meters)
    AND     person_id != :person_id
    """
    )

    query_data = {
        "person_id": location["person_id"],
        "longitude": location["longitude"],
        "latitude": location["latitude"],
        "meters": 5
    }

    new_location = Location()
    new_location.person_id = location["person_id"]
    new_location.creation_time = datetime.now()
    new_location.coordinate = ST_Point(location["latitude"], location["longitude"])
    new_location.set_wkt_with_coords(location["latitude"], location["longitude"])

    connections: List[ConnectionP] = []
    for (
        exposed_person_id,
        location_id,
        exposed_lat,
        exposed_long,
        exposed_time,
    ) in location_db.execute(query, query_data):
        connection = ConnectionP(
            person_id=new_location.person_id,
            exposed_person_id=exposed_person_id,
            latitude=exposed_lat,
            longitude=exposed_long,
            creation_time=new_location.creation_time
            
        )
        connections.append(connection)
    
    connection_db.bulk_save_objects(connections)
    connection_db.commit()

    location_db.add(new_location)
    location_db.commit()

    logging.info('Connections created!')


for location in consumer:
    message = location.value.decode('utf-8')
    location_message = json.loads(message)
    try:
        print(location_message)
        process_location_connections(location_message)
    except Exception as error:
        logging.error('Error message  %s', location_message)
        logging.exception(error)