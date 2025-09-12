# ----------------------------------------------------------
#                Common variables
# ----------------------------------------------------------
# Region where you want to deploy this solution.  Make sure that you have access to
# Bedrock service in this region if you plan to use Bedrock based LLMs
region = "YOUR_AWS_REGION"
# put a ARN if you dont want to generate the role
this_layers_arn = ["arn:aws:lambda:YOUR_AWS_REGION:YOUR_AWS_ACCOUNT:layer:LAYER_NAME:LATEST_DEPLOYED_CHAT_VERSION"]

# ----------------------------------------------------------
#                  Lambda Layer Config
# ----------------------------------------------------------
this_layer_name                  = "YOUR_CHAT_LAYER_NAME"
this_layer_source_code_file_path = "YOUR_CHAT_LAYER_FULLY_QUALIFIED_ZIP_PATH"
this_layer_runtimes              = ["python3.12"]
this_layer_compatible_arch       = ["x86_64"]
