from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

class DeepSeekKernel:
    def __init__(self, model_path="./models/deepseek-coder-6.7b-instruct"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ Model path not found: {model_path}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
            self.model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True).half().cuda()
            self.model.eval()
            print(f"✅ DeepSeek loaded from {model_path}")
        except Exception as e:
            print(f"❌ Error loading DeepSeek model: {e}")
            raise

    def infer(self, prompt: str, max_tokens: int = 512) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=max_tokens,
                temperature=0.7,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
