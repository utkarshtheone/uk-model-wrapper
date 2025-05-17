import onnxruntime
import numpy as np
import time
import asyncio
from typing import Any, List
from lib.logger import get_logger

logger = get_logger("inference")

class ONNXModelWrapper:
    def __init__(self, model_path: str):
        self.ort_session = onnxruntime.InferenceSession(model_path)
        self.input_name = self.ort_session.get_inputs()[0].name
        self.output_name = self.ort_session.get_outputs()[0].name
        logger.info(f"ONNX model loaded from {model_path}")

    def predict(self, data: Any) -> List[float]:
        """
        Performs inference using the ONNX model.
        For this example, we'll assume the model expects a numpy array.
        Adjust the input and output processing based on your actual model.
        """
        logger.debug(f"Starting inference on: {data}")
        start = time.time()
        input_data = np.array([float(x) for x in str(data).split(',')], dtype=np.float32).reshape(1, -1)
        ort_inputs = {self.input_name: input_data}
        ort_outputs = self.ort_session.run([self.output_name], ort_inputs)
        end = time.time()
        logger.debug(f"Inference completed in {end - start:.2f}s with output: {ort_outputs}")
        logger.info(f"ONNX model inference completed with output: {ort_outputs}")
        return ort_outputs[0].tolist()

    async def predict_async(self, data: Any) -> List[float]:
    
    
        logger.debug(f"Starting async inference on: {data}")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.predict, data)