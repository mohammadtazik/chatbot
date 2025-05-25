# from llama_cpp import Llama
#
# llm = Llama(
#     model_path="/home/tazik/models/dorna-llama3-8b-instruct.Q8_0.gguf",
#     n_gpu_layers=-1,  # use full GPU acceleration
#     n_ctx=2048,
#     n_threads=8
# )
#
# def generate_response(prompt, max_tokens=256):
#     output = llm(prompt, max_tokens=max_tokens, stop=["\n"])
#     return output['choices'][0]['text'].strip()
