import time
from concurrent import futures

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

class LocationEventService(location_event_pb2_grpc.location_eventService):
    
    def Create(self, request, context):
        logging.info("Received a message!")

        request_value = {
            'personId': int(request.userId),
            'latitude': int(request.latitude),
            'longitude': int(request.longitude)
        }
        logging.info(request_value)
        try:
            location_encode_data =  json.dumps(request_value, indent=2).encode('utf-8')
            promise=producer.send(kafka_topic, location_encode_data)
            producer.flush()
            record_metadata=promise.get(timeout=10) 
            logging.info('Kafka integration', record_metadata)
        except KafkaError:
            logging.error('Kafka Exception', request_value)

# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
location_event_pb2_grpc.add_location_eventServiceServicer_to_server(LocationEventService(), server)

logging.info("gRPC Server listening on port 5005...")
server.add_insecure_port("[::]:5005")
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(50000)
except KeyboardInterrupt:
    server.stop(0)