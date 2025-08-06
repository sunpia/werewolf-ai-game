variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (test, staging, prod)"
  type        = string
}

variable "domain_names" {
  description = "List of domain names for CloudFront distribution"
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  type        = string
  default     = ""
}

variable "cloudfront_price_class" {
  description = "CloudFront distribution price class"
  type        = string
  default     = "PriceClass_100"
}

variable "alb_dns_name" {
  description = "DNS name of the Application Load Balancer for API routing"
  type        = string
}

variable "alb_https_enabled" {
  description = "Whether HTTPS is enabled on the ALB"
  type        = bool
  default     = false
}
