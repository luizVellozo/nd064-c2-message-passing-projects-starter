import logging
import json
import os
from typing import Dict,List

from app import db
from app.udaconnect.models import Location
from app.udaconnect.schemas import LocationSchema
from sqlalchemy.sql import text
from kafka import KafkaProducer

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("location-api")

kafka_url = os.environ["KAFKA_URL"]
kafka_topic = os.environ["KAFKA_TOPIC"]
producer = KafkaProducer(bootstrap_servers=kafka_url)

class LocationService:
    @staticmethod
    def retrieve(location_id) -> Location:
        location, coord_text = (
            db.session.query(Location, Location.coordinate.ST_AsText())
            .filter(Location.id == location_id)
            .one()
        )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        return location
    
    @staticmethod
    def retrieve_all() -> List[Location]:
        return db.session.query(Location).limit(50).all()

    @staticmethod
    def create(location: Dict) -> Location:
        validation_results: Dict = LocationSchema().validate(location)
        if validation_results:
            logger.warning(f"Unexpected data format in payload: {validation_results}")
            raise Exception(f"Invalid payload: {validation_results}")

        new_location = Location()
        new_location.person_id = location["person_id"]
        new_location.creation_time = location["creation_time"]
        new_location.coordinate = ST_Point(location["latitude"], location["longitude"])

        try:
            location_encode_data = json.dumps(new_location, indent=2).encode('utf-8')
            promise=producer.send(kafka_topic, location_encode_data)
            producer.flush()
            record_metadata=promise.get(timeout=10) 
            logging.info('Kafka integration', record_metadata)
        except KafkaError:
            logging.error('Kafka Exception', request_value)
            raise Exception(f"Invalid payload: {validation_results}")
        
