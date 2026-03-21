from llama_cpp import Llama

model = Llama(model_path="./models/TinyLlama/tinyllama-1.1b-chat-v1.0.Q2_K.gguf")
prompt = "What is the capital of France?"
result = model(prompt, max_tokens=128)
print(result)
