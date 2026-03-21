# ai_core/infer_router.py

import time
import traceback
from ai_core.kernel_selector import get_active_kernel

async def infer_from_bruce(user_input: str, lang: str = "en") -> str:
    """
    Handles a complete inference cycle using the active kernel.
    Provides detailed diagnostics and returns a user-friendly message if any error occurs.
    """
    print(f"🧠 [Bruce] Received prompt: {user_input}")
    start_time = time.time()

    try:
        model = get_active_kernel()

        if not model:
            print("❌ [Bruce] No model is currently loaded or initialized.")
            return "⚠️ Bruce is not ready yet. Please activate a model first."

        if not hasattr(model, "run") or not callable(getattr(model, "run", None)):
            print("❌ [Bruce] The current model does not implement the `.run()` method.")
            return "⚠️ Bruce's brain is incomplete. Please check the kernel implementation."

        # Execute the model
        response = await model.run(user_input, lang=lang)

        if not response:
            print("⚠️ [Bruce] The model did not return any response.")
            return "⚠️ Bruce could not think of an answer. Try again."

        duration = time.time() - start_time
        print(f"✅ [Bruce] Response generated in {duration:.2f} seconds.")
        print("🧠 [Bruce] Output:\n", response.strip())

        return response.strip()

    except Exception as e:
        print("🔥 [Bruce] Fatal error during inference!")
        traceback.print_exc()

        return (
            "❌ Bruce had an internal malfunction.\n"
            f"🛠️ Reason: {str(e)}\n"
            "🧩 Try restarting or checking the model setup."
        )
