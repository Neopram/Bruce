# brucetest.ps1 - Script de verificación para Bruce AI desde PowerShell

$baseUrl = "http://localhost:8000"

Write-Host "🧠 Verificando estado de Bruce AI..." -ForegroundColor Cyan
try {
    $status = Invoke-RestMethod -Uri "$baseUrl/api/terminal/status" -Method Get
    Write-Host "`n✅ Estado verificado. Bruce está en:" $status.device "usando el modelo predeterminado '$($status.default_model)'" -ForegroundColor Green
} catch {
    Write-Host "❌ No se pudo conectar al servidor de Bruce." -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 2

# === PROMPT SIMPLE ===
Write-Host "`n🚀 Enviando prompt simple..." -ForegroundColor Yellow
$payloadSimple = @{
    message = "¿Quién fue Alan Turing?"
} | ConvertTo-Json -Depth 3

try {
    $responseSimple = Invoke-RestMethod -Uri "$baseUrl/api/terminal/message" -Method Post -Body $payloadSimple -ContentType "application/json"
    Write-Host "`n🧠 Respuesta del modelo (modo simple):`n" -ForegroundColor Green
    Write-Output $responseSimple.response
} catch {
    Write-Host "`n❌ Error al enviar prompt simple:" -ForegroundColor Red
    $_.Exception.Message
}

Start-Sleep -Seconds 2

# === PROMPT AVANZADO ===
Write-Host "`n⚙️ Enviando prompt avanzado (modo personalizado con top_p y temperatura)..." -ForegroundColor Yellow
$payloadAdvanced = @{
    prompt = "Explícame qué es el aprendizaje por refuerzo en IA"
    model = "phi3"
    max_tokens = 300
    temperature = 0.65
    top_p = 0.9
} | ConvertTo-Json -Depth 3

try {
    $responseAdvanced = Invoke-RestMethod -Uri "$baseUrl/api/terminal/ask" -Method Post -Body $payloadAdvanced -ContentType "application/json"
    Write-Host "`n🧠 Respuesta del modelo (modo avanzado):`n" -ForegroundColor Green
    Write-Output $responseAdvanced.response
    Write-Host "`n⏱️ Tiempo de procesamiento:" $responseAdvanced.elapsed "segundos"
} catch {
    Write-Host "`n❌ Error al enviar prompt avanzado:" -ForegroundColor Red
    $_.Exception.Message
}
