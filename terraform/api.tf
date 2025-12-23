resource "aws_lambda_function_url" "export_csv_url" {
  function_name      = aws_lambda_function.export_to_csv.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["POST", "GET"]
    allow_headers     = ["*"]
    max_age           = 86400
  }
}

resource "aws_lambda_permission" "allow_public_csv" {
  statement_id           = "AllowPublicFunctionUrlAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.export_to_csv.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}


output "api_url_export_csv" {
  value = aws_lambda_function_url.export_csv_url.function_url
}