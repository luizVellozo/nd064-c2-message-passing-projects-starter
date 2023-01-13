import time
from concurrent import futures
from datetime import datetime

import grpc
import location_event_pb2
import location_event_pb2_grpc
from kafka import KafkaProducer
import logging
import os
import json

kafka_url = os.environ["KAFKA_URL"]
kafka_topic = os.environ["KAFKA_TOPIC"]
logging.info('kafka_url : ', kafka_url)
logging.info('kafka_topic : ', kafka_topic)
producer = KafkaProducer(bootstrap_servers=kafka_url)

logging.basicConfig(level=logging.INFO)

class LocationEventService(location_event_pb2_grpc.location_eventServiceServicer):
    
    def Create(self, request, context):
        logging.info("Received a message!")

        request_value = {
            'person_id': int(request.person_id),
            'latitude': float(request.latitude),
            'longitude': float(request.longitude),
            'creation_time': datetime.now()
        }
        logging.info(request_value)
        print(request_value)
        try:
            location_encode_data =  json.dumps(request_value, indent=2).encode('utf-8')
            promise=producer.send(kafka_topic, location_encode_data)
            producer.flush()
            record_metadata=promise.get(timeout=10) 
            logging.info('Kafka integration', record_metadata)
        except KafkaError:
            logging.error('Kafka Exception', request_value)
        
        return location_event_pb2.LocationEventMessage(**request_value)

# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
location_event_pb2_grpc.add_location_eventServiceServicer_to_server(LocationEventService(), server)

logging.info("gRPC Server listening on port 5005...")
server.add_insecure_port("[::]:5005")
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(5000)
except KeyboardInterrupt:
    server.stop(0)