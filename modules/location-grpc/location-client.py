import grpc
import location_event_pb2
import location_event_pb2_grpc

"""
write messages to gRPC.
"""

print("Send payload...")

channel = grpc.insecure_channel("172.25.36.171:30004")
stub = location_event_pb2_grpc.location_eventServiceStub(channel)

# Update this with desired payload
location_event = location_event_pb2.LocationEventMessage (
    person_id=9,
    longitude=-106.5721845,
    latitude=35.058564,
)

response1 = stub.Create(location_event)

print("Location sent...")
print(response1)