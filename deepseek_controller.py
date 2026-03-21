
# deepseek_controller.py
"""
Núcleo Cognitivo Ampliado: DeepSeek como controlador maestro del sistema de trading
Controla PPO, LSTM y módulos simbióticos: memoria, personalidad, sesgos, retroalimentación, eventos macro.
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
from memory import MemoryManager
from personality import TraderProfile
from bias_filter import BiasFilter
from feedback_loop import FeedbackLearner
from macro_events import MacroAnalyzer

LLM_PATH = "./models/deepseek"
tokenizer = AutoTokenizer.from_pretrained(LLM_PATH)
model = AutoModelForCausalLM.from_pretrained(LLM_PATH)
model.eval()
if torch.cuda.is_available():
    model = model.to("cuda")

# Inicializar módulos simbióticos
memory = MemoryManager()
profile = TraderProfile()
bias_filter = BiasFilter()
learner = FeedbackLearner()
macro = MacroAnalyzer()

AVAILABLE_TOOLS = {
    "train_ppo": lambda episodes: f"[Entrenamiento PPO iniciado por {episodes} episodios]",
    "predict_lstm": lambda data: f"[Predicción LSTM para: {data}]",
    "retrain_all": lambda _: "[Reentrenamiento total activado]",
    "get_reward_avg": lambda _: "[Reward promedio actual: 0.845]",
    "generate_report": lambda _: "[Reporte generado y guardado]",
    "summarize_memory": lambda _: memory.summarize(),
    "get_macro_outlook": lambda _: macro.summary(),
}

def deepseek_thought(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=300, do_sample=True, temperature=0.7)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def handle_command(user_input: str, user_id: str = "default") -> str:
    memory.log_interaction(user_input, user_id)
    profile.update(user_input)
    filtered_input = bias_filter.clean(user_input)

    command_prompt = f"""
Eres DeepSeek, el cerebro maestro del sistema de trading.
Usuario ({profile.current_profile()}): "{filtered_input}"
Contexto macroeconómico: {macro.summary()}

Funciones disponibles:
{json.dumps(list(AVAILABLE_TOOLS.keys()), indent=2)}

Memoria reciente: {memory.recall(user_id)}

Decide una acción en formato JSON:
{{"action": "train_ppo", "args": 100}} o {{"message": "Solo consejo textual."}}
"""
    llm_response = deepseek_thought(command_prompt)
    try:
        learner.learn_from(user_input, llm_response)
        action_obj = json.loads(llm_response.split("\n")[-1])
        if "action" in action_obj:
            action = action_obj["action"]
            args = action_obj.get("args", None)
            result = AVAILABLE_TOOLS[action](args)
            memory.store_decision(user_input, action_obj, user_id)
            return f"🧠 DeepSeek: {result}"
        elif "message" in action_obj:
            return f"💬 DeepSeek: {action_obj['message']}"
    except Exception as e:
        return f"⚠️ Error al interpretar acción: {e}\n{llm_response}"

if __name__ == "__main__":
    while True:
        prompt = input("💡 Usuario: ")
        print(handle_command(prompt))
