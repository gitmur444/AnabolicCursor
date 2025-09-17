# Anabolic Deployment Guide

Этот проект поддерживает два способа деплоя:
1. **Локальный деплой** - из командной строки через `deploy.sh`
2. **GitHub Actions деплой** - через веб-интерфейс GitHub

## Требования

### Общие требования
- AWS CLI установлен и настроен с SSO профилем `admin-sso`
- Terraform >= 1.8.5
- Репозиторий AnabolicInfra склонирован рядом с AnabolicCursor

### Для локального деплоя
- SSH ключи будут созданы автоматически
- Доступ к интернету для установки Docker на сервере

### Для GitHub Actions деплоя
- Настроенные GitHub Secrets (см. ниже)
- AWS OIDC настроен для GitHub Actions

## Локальный деплой

### Подготовка
1. Убедитесь что у вас есть оба репозитория:
   ```bash
   ls ~/CodePlayground/
   # Должны быть: AnabolicCursor и AnabolicInfra
   ```

2. Войдите в AWS SSO:
   ```bash
   aws sso login --profile admin-sso
   ```

### Запуск деплоя
```bash
cd AnabolicCursor
./deploy.sh
```

Скрипт попросит вас ввести API ключи:
- `ANTHROPIC_API_KEY` - ключ Anthropic Claude
- `LITELLM_PROXY_API_KEY` - ключ для LiteLLM прокси

### Что делает локальный деплой:
1. 🔑 Создает SSH ключи (если нужно)
2. 🧹 Очищает старые ресурсы
3. 🏗️ Деплоит инфраструктуру через Terraform
4. 🔌 Устанавливает SSH соединение
5. 📦 Синхронизирует файлы приложения
6. 🚀 Запускает Docker сервисы

## GitHub Actions деплой

### Настройка Secrets

В настройках GitHub репозитория AnabolicCursor добавьте:

1. **INFRA_REPO_TOKEN** - Personal Access Token с доступом к AnabolicInfra
2. **LIGHTSAIL_SSH_KEY_B64** - Base64-encoded SSH private key
3. **AWS_OIDC_ROLE_ARN** - ARN роли для OIDC аутентификации

#### Получение SSH ключа для GitHub

Если у вас уже есть рабочий локальный деплой:
```bash
# Закодировать существующий ключ в base64
base64 -i ~/.ssh/anabolic_deploy | tr -d '\n'
```

Или создать новый ключ:
```bash
# Создать новый SSH ключ
ssh-keygen -t rsa -b 4096 -f ~/.ssh/anabolic_github -N ""

# Закодировать в base64 для GitHub Secrets
base64 -i ~/.ssh/anabolic_github | tr -d '\n'
```

#### Настройка AWS SSM параметров

GitHub Actions использует секреты из AWS SSM:
```bash
# Добавить API ключи в SSM
aws ssm put-parameter --region eu-central-1 \
  --name "/anabolic/litellm/ANTHROPIC_API_KEY" \
  --value "your-anthropic-key" \
  --type "SecureString"

aws ssm put-parameter --region eu-central-1 \
  --name "/anabolic/litellm/LITELLM_PROXY_API_KEY" \
  --value "your-proxy-key" \
  --type "SecureString"
```

### Запуск GitHub Actions деплоя

1. Перейдите в репозиторий AnabolicCursor на GitHub
2. Откройте вкладку "Actions"
3. Выберите "Deploy Infra and Stack"
4. Нажмите "Run workflow"

## Результат деплоя

После успешного деплоя вы получите:

- **LiteLLM Proxy**: `http://<IP>` (порт 80)
- **Grafana**: `http://<IP>/grafana` (admin/admin)
- **SSH доступ**: `ssh -i ~/.ssh/anabolic_deploy ubuntu@<IP>`

## Структура проекта

```
AnabolicCursor/
├── deploy.sh              # Локальный деплой скрипт
├── .github/workflows/
│   └── deploy.yml         # GitHub Actions workflow
└── DEPLOY.md              # Эта документация

AnabolicInfra/
└── infra/
    ├── terraform/         # Terraform конфигурация
    ├── stack/            # Docker Compose стек
    └── user-data/        # Cloud-init скрипты
```

## Troubleshooting

### Локальный деплой

**SSH connection failed:**
- Проверьте что AWS SSO сессия активна: `aws sts get-caller-identity --profile admin-sso`
- Убедитесь что security groups открыты для SSH (порт 22)

**Terraform errors:**
- Проверьте что рабочий каталог правильный и AnabolicInfra рядом
- Очистите Terraform state если нужно: `rm -rf infra/terraform/.terraform*`

### GitHub Actions деплой

**SSH key errors:**
- Убедитесь что LIGHTSAIL_SSH_KEY_B64 правильно закодирован в base64
- Проверьте что приватный ключ в правильном формате (начинается с `-----BEGIN`)

**AWS permissions:**
- Проверьте что OIDC роль имеет необходимые разрешения для Lightsail, SSM, EC2

## Очистка ресурсов

Для удаления всех созданных ресурсов:

```bash
cd AnabolicInfra/infra/terraform
terraform destroy -auto-approve
```

Или через AWS CLI:
```bash
aws lightsail delete-instance --region eu-central-1 --instance-name anabolic-litellm
aws lightsail delete-key-pair --region eu-central-1 --key-pair-name anabolic-key-ci
```