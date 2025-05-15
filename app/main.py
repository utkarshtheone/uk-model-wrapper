import pika
from pika.spec import Basic, BasicProperties
import json
import time
from typing import Dict, List, Any
from lib.utils import preprocessing_operations
from lib.model_inference import ONNXModelWrapper
from lib.logger import get_logger

logger = get_logger("main")

RABBITMQ_HOST = "rabbitmq"  # Assuming your RabbitMQ container is named 'rabbitmq' in Docker
QUEUE_NAME = "request_queue"
ONNX_MODEL_PATH = "model.onnx"  # Ensure this path is correct within the container

def process_message(message_body: str, model_wrapper: ONNXModelWrapper) -> str:
    """
    Processes a single message from the queue with a defined input structure.
    """
    start = time.time()
    data: Dict[str, Any] = json.loads(message_body)
    input_data: List[float] = data.get("data",)
    processed_data = preprocessing_operations(input_data) # Pass the structured data
    pre_end = time.time()
    model_output = model_wrapper.predict(processed_data)
    model_end = time.time()
    logger.debug(f"Preprocessing Time: {pre_end - start:.2f}s")
    logger.debug(f"Inference Time: {model_end - pre_end:.2f}s")
    result = {"original_input": input_data, "processed_data": processed_data, "model_output": model_output}
    return result

def callback(ch: pika.adapters.BlockingConnection, method: Basic.Deliver, properties: BasicProperties, body: bytes, model_wrapper: ONNXModelWrapper) -> None:
    """
    Callback function to process messages from RabbitMQ and send a response.
    """
    props = pika.BasicProperties(correlation_id=properties.correlation_id)
    print(f"Reply-to queue: {properties.reply_to}")
    request_data = json.loads(body.decode())
    message_id = request_data.get('message_id')
    pick_up_timestamp = time.time()
    logger.info(f"Received message {message_id} at {pick_up_timestamp:.2f}")

    try:
        result = process_message(body.decode(), model_wrapper)
        response_timestamp = time.time()
        logger.info(f"Processed message {message_id} in {response_timestamp - pick_up_timestamp:.2f}s")
        response_message = json.dumps({
            'message_id': message_id,
            'pick_up_timestamp': pick_up_timestamp,
            'response_timestamp': response_timestamp,
            'result': result
        })
        ch.basic_publish(exchange='', routing_key=properties.reply_to, properties=props, body=response_message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing message {message_id}: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, multiple=False, requeue=False)

def main() -> None:
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters(RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)  # Process one message at a time

    model_wrapper = ONNXModelWrapper(ONNX_MODEL_PATH)

    logger.info("Waiting for messages...")
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=lambda ch, method, properties, body: callback(ch, method, properties, body, model_wrapper))

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()
