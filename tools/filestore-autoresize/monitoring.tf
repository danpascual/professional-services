/**
 * Copyright 2022 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

resource "google_monitoring_notification_channel" "awsome_app_notification_channel" {
  project = module.webserver-project.project_id
  display_name = "Awsome App Notification Channel"
  type         = "email"
  labels = {
    email_address = var.app_admin_email
  }
}

resource "google_monitoring_alert_policy" "awsome_app_alert_policy" {
  project = module.webserver-project.project_id
  display_name = "Awsome App Alert Policy"
  combiner     = "OR"
  conditions {
    display_name = "awsome app uptime check"
    condition_threshold {
      filter     = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" resource.type=\"uptime_url\" metric.label.\"check_id\"=\"${split("/", google_monitoring_uptime_check_config.awsome_app_http_uptime_check.name)[3]}\""
      threshold_value = "1"
      trigger {
        count = "1"
      }
      duration   = "0s"
      comparison = "COMPARISON_GT"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields = ["resource.*"]
      }
    }
  }
  documentation {
    content = "OMG!!!111 AWSOME APP IS DOWN!!!111 DO SOMETHING!!!111"
  }
  notification_channels = [ google_monitoring_notification_channel.awsome_app_notification_channel.id ]
}