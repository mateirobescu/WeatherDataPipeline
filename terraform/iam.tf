#fetch-raw-weather-data--mateirobescu
data "aws_iam_policy_document" "lambda_fetch_data_policy" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.openweather_api.arn]
  }

  statement {
    actions   = ["s3:PutObject", "s3:PutObjectAcl"]
    resources = ["${aws_s3_bucket.weather_data_bucket.arn}/raw/*"]
  }
}

resource "aws_iam_role" "lambda_fetch_data_role" {
  name = "lambda_fetch_data_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_fetch_data_policy_attach" {
  name   = "lambda_fetch_data_policy_attach"
  role   = aws_iam_role.lambda_fetch_data_role.id
  policy = data.aws_iam_policy_document.lambda_fetch_data_policy.json
}

#invoke-fetch-weather-data--mateirobescu
data "aws_iam_policy_document" "lambda_invoke_fetch_data_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]
    resources = [aws_dynamodb_table.cities.arn]
  }

  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.fetch_weather.arn]
  }
}

resource "aws_iam_role" "lambda_invoke_fetch_data_role" {
  name = "lambda_invoke_fetch_data_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lamba_invoke_fetch_data_policy_attach" {
  name   = "lamba_invoke_fetch_data_policy_attach"
  role   = aws_iam_role.lambda_invoke_fetch_data_role.id
  policy = data.aws_iam_policy_document.lambda_invoke_fetch_data_policy.json
}

#lambda_load_weather_to_rds
data "aws_iam_policy_document" "lambda_load_weather_policy" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.rds_weather_data_credentials.arn]
  }

  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.weather_data_bucket.arn]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject"
    ]
    resources = ["${aws_s3_bucket.weather_data_bucket.arn}/raw/*"]
  }
}

resource "aws_iam_role" "lambda_load_weather_role" {
  name = "lambda_load_weather_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_load_weather_policy_attach" {
  name   = "lambda_load_weather_policy_attach"
  role   = aws_iam_role.lambda_load_weather_role.id
  policy = data.aws_iam_policy_document.lambda_load_weather_policy.json
}

#lambda_export_to_csv
data "aws_iam_policy_document" "lambda_export_to_csv_policy" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.rds_weather_data_credentials.arn]
  }

  statement {
    actions = ["s3:ListBucket"]
    resources = [
      aws_s3_bucket.weather_data_bucket.arn
    ]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["csv/*"]
    }
  }

  statement {
    actions = ["s3:PutObject", "s3:PutObjectAcl"]
    resources = [
      "${aws_s3_bucket.weather_data_bucket.arn}/csv/*"
    ]
  }
}

resource "aws_iam_role" "lambda_export_to_csv_role" {
  name = "lambda_export_to_csv_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_export_to_csv_role_policy_attach" {
  name   = "lambda_export_to_csv_role_policy_attach"
  role   = aws_iam_role.lambda_export_to_csv_role.id
  policy = data.aws_iam_policy_document.lambda_export_to_csv_policy.json
}

resource "aws_iam_policy" "lambda_vpc_access_policy" {
  name = "lambda-vpc-access-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access_invoke" {
  role       = aws_iam_role.lambda_invoke_fetch_data_role.name
  policy_arn = aws_iam_policy.lambda_vpc_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access_fetch" {
  role       = aws_iam_role.lambda_fetch_data_role.name
  policy_arn = aws_iam_policy.lambda_vpc_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access_load" {
  role       = aws_iam_role.lambda_load_weather_role.name
  policy_arn = aws_iam_policy.lambda_vpc_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access_csv" {
  role       = aws_iam_role.lambda_export_to_csv_role.name
  policy_arn = aws_iam_policy.lambda_vpc_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access_history" {
  role       = aws_iam_role.lambda_fetch_data_role.name
  policy_arn = aws_iam_policy.lambda_vpc_access_policy.arn
}