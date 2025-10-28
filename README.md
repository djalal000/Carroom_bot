
<img width="2660" height="1884" alt="Blank diagram" src="https://github.com/user-attachments/assets/94b3d976-9612-4524-a796-345419cd837b" />




This project provides an automated infrastructure setup for deploying a Python-based Telegram bot on AWS using Terraform, ECS Fa<img width="2660" height="1884" alt="Blank diagram" src="https://github.com/user-attachments/assets/aa5881a4-283a-4f88-ae6a-625ae2d4339a" />
rgate, and ECR. It includes a CI/CD workflow to build, scan, and deploy Docker images.

---

## 🏗️ Project Overview

The infrastructure consists of:

- **AWS VPC** with public subnets
- **ECR Repository** for Docker images
- **ECS Cluster (Fargate)** to run the Telegram bot container
- **IAM Roles** for ECS task execution
- **Security Groups** to manage access
- **CloudWatch Logs** for monitoring container logs

The setup allows the bot to be updated automatically whenever code changes are pushed to GitHub.

---

## ⚙️ Terraform Resources

### 1. Provider Configuration
- AWS provider configured using the region variable

### 2. ECR Repository
- Stores Docker images
- Enabled `scan_on_push` for vulnerability scanning

### 3. Networking
- **VPC**: isolated network for resources
- **Subnets**: public subnets for ECS tasks
- **Internet Gateway**: allows outbound/inbound Internet access
- **Route Table**: routes traffic to IGW

### 4. Security
- Security Group: allows inbound HTTP traffic on port 80
- IAM Role: ECS execution role with proper permissions

### 5. ECS Cluster & Tasks
- **Cluster**: groups ECS tasks
- **Task Definition**: specifies Docker container configuration
- **Service**: ensures task is running and healthy

### 6. Logging
- CloudWatch Log Group for container logs

---

## 🚀 Deployment Steps

1. **Configure Variables**
   Update `variables.tf` with:
   ```hcl
   variable "aws_region" {}
   variable "project_name" {}
   variable "environment" {}
   variable "vpc_cidr" {}
````

2. **Initialize Terraform**

   ```bash
   terraform init
   ```

3. **Plan Infrastructure**

   ```bash
   terraform plan
   ```

4. **Apply Infrastructure**

   ```bash
   terraform apply
   ```

5. **Build and Push Docker Image**

   ```bash
   docker build -t <your-ecr-repo>:latest .
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com
   docker tag <your-image>:latest <account_id>.dkr.ecr.<region>.amazonaws.com/<your-ecr-repo>:latest
   docker push <account_id>.dkr.ecr.<region>.amazonaws.com/<your-ecr-repo>:latest
   ```

6. **Update ECS Service**

   * ECS service automatically pulls the latest image if configured with the same task definition
   * Optionally, update task definition and apply with Terraform

---

## 🔒 Security & Best Practices

* **Secrets**: Store Telegram bot token in AWS Secrets Manager
* **Vulnerability Scanning**: Enable Trivy or ECR scan on push
* **Private Subnets**: Move ECS tasks to private subnets with NAT Gateway for enhanced security

---

## 📊 Monitoring

* CloudWatch Logs will capture all container logs
* Set up CloudWatch Alarms for task failures or high CPU/memory usage

---

## ⚡ CI/CD Integration

* **GitHub Actions**:

  * Build Docker image
  * Scan with Trivy
  * Push to ECR
  * Deploy using Terraform
* Automates updates whenever code is pushed to the repository

---

## 🖼️ Diagram

```
[Internet] 
   ↓
[Internet Gateway]
   ↓
[Route Table]
   ↓
[Public Subnet]
   ├─ ECS Fargate Task (Telegram Bot)
   └─ Security Group
[ECS Task] → [ECR] (pull image)
[ECS Task] → [CloudWatch] (logs)
```

---

## 📦 Future Enhancements

* Move ECS tasks to private subnets for better security
* Add Application Load Balancer (ALB) for webhook routing
* Integrate RDS or DynamoDB for persistent bot data
* Automated Terraform with GitHub Actions for full CI/CD

```

This README explains your **current Terraform structure**, **services used**, and **deployment workflow**, while giving clear guidance for CI/CD, security, and future improvements.
```
