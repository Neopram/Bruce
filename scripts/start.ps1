param (
    [string]$mode = "dev"
)

Write-Host "==[ OKK_Gorilla_Bot Launcher | Mode: $mode ]==" -ForegroundColor Cyan

# Cargar variables de entorno desde .env.overdrive
$envPath = ".env.overdrive"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^(?!#)([\\w_]+)=(.*)$") {
            $name, $value = $matches[1], $matches[2]
            [System.Environment]::SetEnvironmentVariable($name, $value)
        }
    }
    Write-Host "[✓] Variables de entorno cargadas." -ForegroundColor Green
} else {
    Write-Host "[X] Archivo .env.overdrive no encontrado." -ForegroundColor Red
    exit 1
}

# Verificar Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[X] Docker no está instalado o no está en PATH." -ForegroundColor Red
    exit 1
}

# Ejecutar según modo
switch ($mode.ToLower()) {
    "dev" {
        Write-Host "[•] Iniciando en modo desarrollo..." -ForegroundColor Yellow
        docker-compose -f infrastructure/docker/docker-compose.yaml up --build
    }
    "train" {
        Write-Host "[•] Entrenando modelo PPO..." -ForegroundColor Yellow
        python scripts/train_model.py
    }
    "sim" {
        Write-Host "[•] Ejecutando simulación de entorno RL..." -ForegroundColor Yellow
        python gym_envs/market_env.py
    }
    "real" {
        Write-Host "[•] Ejecutando conexión real con CEX/DEX..." -ForegroundColor Yellow
        python app/usecases/trade_executor.py
    }
    default {
        Write-Host "[X] Modo no reconocido: $mode" -ForegroundColor Red
        exit 1
    }
}
