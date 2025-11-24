variable "region" {
  description = "AWS region"
  default     = "eu-north-1"
}

variable "project_name" {
  description = "Project base name"
  default     = "weather-pipeline-mateirobescu"
}

variable "openweather_api_key" {
  description = "Your OpenWeather API key"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Master password for RDS"
  type        = string
  sensitive   = true
}

variable "dev_con_ip" {
  description = "public ip of my laptop"
  type        = string
}

variable "rds_user" {
  description = "username of rds db"
  type        = string
}

variable "rds_pass" {
  description = "password of rds db"
  type        = string
}

variable "rds_host" {
  description = "hostname of rds db"
  type        = string
}

variable "rds_dbname" {
  description = "database name of rds db"
  type        = string
}