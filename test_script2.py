import asyncio
import aio_pika
import time
import json
import random
import argparse
import uuid


def generate_message():
    message_id = str(uuid.uuid4())
    input_data = [random.uniform(0, 1) for _ in range(5)]
    send_timestamp = time.time()
    return message_id, json.dumps({
        "message_id": message_id,
        "data": input_data,
        "send_timestamp": send_timestamp
    })


async def receive_responses(queue: aio_pika.Queue, responses: dict, expected_count: int, timeout: int):
    start_time = time.time()
    while len(responses) < expected_count and time.time() - start_time < timeout:
        try:
            incoming_message = await queue.get(timeout=1)
            response = json.loads(incoming_message.body.decode())
            responses[response['message_id']] = response
            await incoming_message.ack()
        except aio_pika.exceptions.QueueEmpty:
            await asyncio.sleep(0.1)


async def send_messages(
    host: str,
    queue_name: str,
    num_messages: int,
    response_queue_name: str,
    timeout: int
):
    connection = await aio_pika.connect_robust(host)
    channel = await connection.channel()

    await channel.declare_queue(queue_name, durable=True)
    response_queue = await channel.declare_queue(response_queue_name, durable=False)

    responses = {}
    sent_messages = {}

    # Start receiving task
    consume_task = asyncio.create_task(
        receive_responses(response_queue, responses, num_messages, timeout)
    )

    start_time = time.time()
    for i in range(num_messages):
        message_id, message_body = generate_message()
        sent_messages[message_id] = json.loads(message_body)['send_timestamp']

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                correlation_id=message_id,
                reply_to=response_queue_name
            ),
            routing_key=queue_name
        )

        if (i + 1) % 100 == 0:
            print(f"Sent {i + 1} messages...")

    send_duration = time.time() - start_time
    print(f"\nSent {num_messages} messages in {send_duration:.2f} seconds.")

    # Wait for responses
    await consume_task
    await connection.close()

    # Calculate and print metrics
    metrics = []
    for msg_id, response in responses.items():
        send_time = sent_messages.get(msg_id)
        if not send_time:
            continue
        pick_up_time = response.get('pick_up_timestamp')
        response_time = response.get('response_timestamp')

        if pick_up_time and response_time:
            metrics.append({
                'message_id': msg_id,
                'send_time': send_time,
                'pick_up_latency': pick_up_time - send_time,
                'processing_latency': response_time - pick_up_time,
                'total_latency': response_time - send_time,
                'response_time': response_time
            })

    if metrics:
        avg_pickup = sum(m['pick_up_latency'] for m in metrics) / len(metrics)
        avg_processing = sum(m['processing_latency'] for m in metrics) / len(metrics)
        avg_total = sum(m['total_latency'] for m in metrics) / len(metrics)
        total_time = max(m['response_time'] for m in metrics) - min(m['send_time'] for m in metrics)

        print("\n--- Processing Metrics ---")
        print(f"Number of responses received: {len(responses)}/{num_messages}")
        print(f"Average Pick-Up Latency: {avg_pickup:.4f} seconds")
        print(f"Average Processing Latency: {avg_processing:.4f} seconds")
        print(f"Average Total Latency: {avg_total:.4f} seconds")
        print(f"Total Processing Time: {total_time:.4f} seconds")
    else:
        print("\n--- No responses received or metrics could not be calculated. ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Async RabbitMQ Tester with aio-pika.')
    parser.add_argument('--num_messages', type=int, default=20, help='Number of messages to send')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout in seconds to wait for responses')
    parser.add_argument('--host', type=str, default='amqp://guest:guest@localhost:5672/', help='RabbitMQ URL')
    parser.add_argument('--queue', type=str, default='request_queue', help='Request queue name')
    parser.add_argument('--response_queue', type=str, default='response_queue', help='Response queue name')
    
    # request_queue
    args = parser.parse_args()

    asyncio.run(
        send_messages(
            host=args.host,
            queue_name=args.queue,
            num_messages=args.num_messages,
            response_queue_name=args.response_queue,
            timeout=args.timeout
        )
    )
