resource "aws_cloudwatch_event_rule" "daily_invoke_lambda_trigger" {
  name                = "daily-weather-fetch-trigger"
  description         = "Triggers the weather invoke fetch Lambda once per day"
  schedule_expression = "cron(0 8 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_invoke_lambda_trigger.name
  target_id = "invoke-weather-lambda"
  arn       = aws_lambda_function.invoke_fetch_weather.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.invoke_fetch_weather.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_invoke_lambda_trigger.arn
}