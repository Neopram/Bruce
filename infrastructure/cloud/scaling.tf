resource "kubernetes_horizontal_pod_autoscaler" "trading_bot_hpa" {
  metadata {
    name      = "trading-bot-hpa"
    namespace = "default"
  }

  spec {
    scale_target_ref {
      kind = "Deployment"
      name = "trading-bot"
      api_version = "apps/v1"
    }

    min_replicas = 2
    max_replicas = 10

    metrics {
      type = "Resource"
      resource {
        name  = "cpu"
        target {
          type                = "Utilization"
          average_utilization = 70
        }
      }
    }

    metrics {
      type = "Resource"
      resource {
        name  = "memory"
        target {
          type                = "Utilization"
          average_utilization = 75
        }
      }
    }
  }
}
