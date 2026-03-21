def execute_action(action_obj, user_id: str):
    """
    Ejecuta acciones derivadas del pensamiento de Bruce.
    action_obj puede ser un dict con estructura:
    {
        "type": "notify",
        "target": "user",
        "message": "Tu portafolio está expuesto al riesgo"
    }
    """
    action_type = action_obj.get("type")
    if action_type == "notify":
        print(f"[NOTIFY] A {user_id}: {action_obj.get('message')}")
    elif action_type == "refactor":
        print(f"[REFACTOR] Iniciando refactor de módulo: {action_obj.get('module')}")
    elif action_type == "trade":
        print(f"[TRADE] Ejecutando estrategia: {action_obj.get('strategy')} para {user_id}")
    else:
        print(f"[UNKNOWN ACTION] {action_type}")