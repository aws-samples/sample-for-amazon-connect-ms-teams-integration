# ----------------------------------------------------------
#                Common variables
# ----------------------------------------------------------
variable "region" {
  type = string
}

variable "this_layer_arn" {
  type        = list(string)
  default     = []
  description = "Chat Layer ARN for an existing Layer"
}


# ----------------------------------------------------------
#                Lambda Layer variables
# ----------------------------------------------------------
variable "this_layer_name" {
  type        = string
  description = "Name of the layer that will apear in the AWS console."
}
variable "this_layer_description" {
  type        = string
  description = "Description of the layer that will apear in the AWS console."
  default     = ""
}
variable "this_layer_source_code_file_path" {
  type        = string
  description = "Path to the zip file of the chat layer."
}
variable "this_layer_runtimes" {
  type        = list(string)
  description = "List of runtimes available for the chat layer."
}

variable "this_layer_compatible_arch" {
  type        = list(string)
  description = "List of compatible architecture available for the chat layer."
}
