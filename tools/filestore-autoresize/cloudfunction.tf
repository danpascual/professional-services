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


module "cloud_function" {
  source        = "github.com/terraform-google-modules/cloud-foundation-fabric//modules/cloud-function?ref=v9.0.2"
  project_id    = local.project_id
  name          = "auto-resize"
  bucket_name   = var.code_bucket
  region        = var.default_region
  # consider adding output_file_mode to make zip hashes consistent: https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/archive_file#output_file_mode
  bundle_config = {
    source_dir  = var.src
    output_path = "${path.module}/bundle-${var.name}.zip"
    excludes    = var.excludes
  }
  function_config = {
    entry_point      = var.name
    ingress_settings = null
    instances        = 1
    memory           = 256
    runtime          = "python39"
    timeout          = 60
  }
  trigger_config = {
    event    = "google.pubsub.topic.publish"
    resource = google_pubsub_topic.topic.id
    retry    = true
  }
  service_account_create = true
  vpc_connector = {
    create = false,
    name = "default",
    egress_settings = "ALL_TRAFFIC"
  }
}

resource "random_id" "cf_code_bucket" {
  byte_length = 4
}

resource "google_storage_bucket" "code" {
  project                     = data.google_project.ctfd.project_id
  name                        = "${var.deployment}-csa-cf-code-${random_id.cf_code_bucket.hex}"
  location                    = var.default_region
  force_destroy               = false
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

resource "google_project_iam_member" "cloud_builder" {
  project = var.cicd_project
  role    = "roles/file.editor"
  member  = module.cloud_function.service_account_iam_email
}

resource "google_secret_manager_secret_iam_member" "mysql_root_password" {
  project   = var.ctfd_project
  secret_id = "mysql-root-password"
  role      = "roles/secretmanager.secretAccessor"
  member    = module.cloud_function.service_account_iam_email
}

resource "google_project_iam_member" "sql_client" {
  project = var.ctfd_project
  role    = "roles/cloudsql.client"
  member  = module.cloud_function.service_account_iam_email
}

resource "google_pubsub_topic" "topic" {
  project = var.ctfd_project
  name    = var.name
}
