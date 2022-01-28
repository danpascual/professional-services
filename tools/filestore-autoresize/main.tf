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

resource "random_id" "filestore_project" {
  byte_length = 2
}

module "filestore_project" {
  source          = "github.com/terraform-google-modules/cloud-foundation-fabric//modules/project?ref=v9.0.2"
  billing_account = var.billing_account
  name            = "${var.project_prefix}-filestore-${random_id.filestore_project.hex}"
  parent          = google_folder.bootstrap.name
  services        = [
    "logging.googleapis.com",
  ]
  project_create  = true
  service_config  = {
    disable_on_destroy         = false
    disable_dependent_services = false
  }
  labels = {
    "component"  = "filestore"
  }
}
