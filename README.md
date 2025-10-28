<img width="2660" height="1884" alt="Blank diagram" src="https://github.com/user-attachments/assets/94b3d976-9612-4524-a796-345419cd837b" />

Hey! This is a little project I put together to spin up a **Telegram bot** on AWS without clicking around in the console all day. It uses **Terraform** to create everything, **Fargate** to run the bot in Docker, and **ECR** to store the images. I also threw in a **GitHub Actions CI/CD pipeline** so every time I push code, it builds, scans, and deploys automatically.



What’s in the setup?

Here’s the gist of what gets created:

- **VPC** with **public subnets** (so the bot can talk to Telegram)
- **ECR repo** to hold the Docker images (with auto-scanning on push)
- **ECS Cluster on Fargate** – runs the bot container, no servers to manage
- **IAM roles** so ECS can pull images and write logs
- **Security Group** – only allows what’s needed (port 80 inbound for now)
- **CloudWatch Logs** – see what the bot is doing in real time

Push new code → GitHub builds & pushes image → ECS pulls the latest → bot updates. Zero manual steps.


 Terraform Resources (the important bits)

1. **AWS Provider**  
   Just points to the region you set.

2. **ECR Repository**  
   Stores the Docker image. `scan_on_push = true` so AWS flags any vulnerabilities.

3. **Networking**  
   - VPC (your private network bubble)  
   - Public subnets (for Fargate tasks)  
   - Internet Gateway + Route Table → internet access

4. **Security**  
   - Security Group: allows HTTP (port 80) inbound  
   - IAM Role: gives ECS permission to pull from ECR and push logs

5. **ECS Stuff**  
   - Cluster → groups tasks  
   - Task Definition → says “run this Docker image”  
   - Service → keeps one task running and restarts if it dies

6. **Logging**  
   CloudWatch Log Group catches all `print()` and error output from the container.


## How to deploy it (step-by-step)

### 1. Set your variables
Edit `variables.tf` (or pass via CLI):

```hcl
variable "aws_region" { default = "us-east-1" }
variable "project_name" { default = "telegram-bot" }
variable "environment" { default = "prod" }
variable "vpc_cidr" { default = "10.0.0.0/16" }
```

 2. Initialize Terraform
```bash
terraform init
```

3. See what’ll be created
```bash
terraform plan
```

 4. Build the infra
```bash
terraform apply
```

 5. Build & push your Docker image
```bash
# Build
docker build -t my-telegram-bot:latest .

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag & push
docker tag my-telegram-bot:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-telegram-bot:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-telegram-bot:latest
```

> ECS will auto-pull the `latest` tag if your task def uses it. You can also update the task def via Terraform.

---

 Security & Good Stuff

- **Bot token?** → Store it in **AWS Secrets Manager**, not in code or env files.
- **Scanning:** ECR scans on push. I also use **Trivy** in CI.
- **Want tighter security?** Move Fargate tasks to **private subnets** + NAT Gateway.

---

Monitoring

- All logs go to **CloudWatch** – just search your log group.
- Set up **alarms** for:
  - Task crashes
  - High CPU/memory
  - No healthy tasks

---

 CI/CD with GitHub Actions

I have a workflow that:
1. Builds the Docker image
2. Scans it with **Trivy**
3. Pushes to ECR
4. Runs `terraform apply` to update ECS

→ Push to `main` → bot updates in ~2 minutes.

---

 Diagram (text version)

```
[Internet]
   ↓
[Internet Gateway]
   ↓
[Route Table]
   ↓
[Public Subnet]
   ├─ ECS Fargate Task → runs Telegram Bot
   └─ Security Group (port 80 in)
   
[ECS Task] → pulls image from [ECR]
[ECS Task] → sends logs to [CloudWatch]
```

---

 Future Ideas

- [ ] Move tasks to **private subnets + NAT**
- [ ] Add **ALB** for clean webhook URLs
- [ ] Use **DynamoDB** or **RDS** if the bot needs to remember stuff
- [ ] Full Terraform in CI/CD (already half-done)

linkedin : https://www.linkedin.com/in/bekhti-djalal/
