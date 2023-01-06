### Architecture decisions
Session to record the strategies and architectural decisions used in the UdaConnect MVP.

### Key requirements
First, it is important to extract the requirements or characteristics that most influence the architecture.

* Respond quickly to user interactions.
* Large capacity for ingesting location data.
* The app is new and has not yet been released into production, so infrastructure and data definitions are free.
* Application must use microservice architecture and different message passing techniques, running in Kubernetes and with Python.

### Microservices and components
Considering the requirements, the solution was separated into the following microservices:

* Person API: It will be isolated in a separate service and will control all access to person information, providing a Rest interface for external calls and gRPC for internal service calls, in this case the Connections API. The database will also be separated, where only the Person API will have access.
* Location API: It will also be isolated in a separate service, where it will be responsible for receiving incoming location information and scaling as the load increases. The Rest interface will be maintained but a specific gRPC interface will be added to receive locations, since there will be many requests, this can help with performance. For each new location that arrives, either by REST or gRPC, the service will send the event to process and thus generate the connections, this will be done by the Location event consumer component.
* Location event consumer: Component responsible for creating the connections for each new location that is submitted, as the location API sends the events to Kafka, this component acts as a consumer. To generate the connections, it still reads the location database, in the future we can isolate this reading in the location api using gRPC for that.
* Connections API: Component responsible for creating the connections for each new location that is submitted, as the location API sends the events to Kafka, this component acts as a consumer. To generate the connections, it still reads the location database, in the future we can isolate this reading in the location api using gRPC for that. As connection data is immutable, this service's database was separated, acting as a reading base for processed/created connections.
* Frontend: Frontend component that displays connections and people. It was necessary to adjust the host of the calls that were segregated, Person API and Connections API.


