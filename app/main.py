import asyncio
import uvloop
import json
import time
from typing import Dict, Any, List

import aio_pika
from aio_pika import IncomingMessage

from lib.utils import preprocessing_operations
from lib.model_inference import ONNXModelWrapper
from lib.logger import get_logger

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = get_logger("main")
ONNX_MODEL_PATH = "model.onnx"
QUEUE_NAME = "request_queue"


async def process_message(message_body: str) -> Dict[str, Any]:
    start = time.time()
    data: Dict[str, Any] = json.loads(message_body)
    input_data: List[float] = data.get("data", [])
    processed_data = await preprocessing_operations(input_data)
    pre_end = time.time()

    model_wrapper = ONNXModelWrapper(ONNX_MODEL_PATH)
    model_output = await model_wrapper.predict_async(processed_data)
    model_end = time.time()

    logger.debug(f"Preprocessing Time: {pre_end - start:.2f}s")
    logger.debug(f"Inference Time: {model_end - pre_end:.2f}s")

    return {
        "original_input": input_data,
        "processed_data": processed_data,
        "model_output": model_output,
    }


async def on_message(message: IncomingMessage) -> None:
    async with message.process():
        props = message.properties
        request_data = json.loads(message.body.decode())
        message_id = request_data.get("message_id")
        pick_up_timestamp = time.time()
        logger.info(f"Received message {message_id} at {pick_up_timestamp:.2f}")

        try:
            result = await process_message(message.body.decode())
            response_timestamp = time.time()

            logger.info(f"Processed message {message_id} in {response_timestamp - pick_up_timestamp:.2f}s")

            response_message = json.dumps({
                "message_id": message_id,
                "pick_up_timestamp": pick_up_timestamp,
                "response_timestamp": response_timestamp,
                "result": result,
            })

            if props.reply_to:
                await message.channel.default_exchange.publish(
                    aio_pika.Message(
                        body=response_message.encode(),
                        correlation_id=props.correlation_id,
                    ),
                    routing_key=props.reply_to,
                )
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}", exc_info=True)


async def main() -> None:
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    logger.info("Waiting for messages...")

    await queue.consume(on_message)

    try:
        await asyncio.Future()  # run forever
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
