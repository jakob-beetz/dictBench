# PropBench Docker Deployment

This directory contains all necessary files for deploying PropBench using Docker on Plesk or any server.

## Quick Start

1. **Clone your repository** (replace with your actual repo URL):
   ```bash
   git clone https://github.com/yourusername/propbench.git
   cd propbench
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Deploy**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## Files Overview

### Core Files
- `Dockerfile` - Main application container
- `docker-compose.yml` - Multi-container orchestration
- `requirements-docker.txt` - Python dependencies
- `deploy.sh` - Automated deployment script

### Configuration
- `docker/settings_production.py` - Django production settings
- `nginx/nginx.conf` - Nginx reverse proxy configuration
- `.env.example` - Environment variables template

## Environment Variables

Required variables in `.env`:

```bash
# Security
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@db:5432/propbench_db
POSTGRES_DB=propbench_db
POSTGRES_USER=propbench_user
POSTGRES_PASSWORD=your_db_password

# Cache
REDIS_URL=redis://redis:6379/1

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Deployment Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Nginx     │────│   Django    │────│ PostgreSQL  │
│ (Port 80)   │    │ (Port 8000) │    │ (Port 5432) │
│ Reverse     │    │ Gunicorn    │    │ Database    │
│ Proxy       │    │ Application │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
                   ┌─────────────┐
                   │   Redis     │
                   │ (Port 6379) │
                   │ Cache &     │
                   │ Sessions    │
                   └─────────────┘
```

## Plesk Deployment Steps

### 1. Plesk Docker Extension
Install Docker extension in Plesk:
- Go to Extensions > Docker
- Install Docker extension

### 2. Upload Files
Upload all Docker files to your domain directory:
```
/var/www/vhosts/yourdomain.com/
├── Dockerfile
├── docker-compose.yml
├── requirements-docker.txt
├── deploy.sh
├── .env
├── docker/
│   └── settings_production.py
└── nginx/
    └── nginx.conf
```

### 3. Configure Domain
In Plesk domain settings:
- Set document root to `/var/www/vhosts/yourdomain.com/`
- Enable Docker proxy (if available)
- Configure DNS to point to server

### 4. Deploy
SSH into server and run:
```bash
cd /var/www/vhosts/yourdomain.com/
chmod +x deploy.sh
./deploy.sh
```

## Production Considerations

### SSL/HTTPS
1. Obtain SSL certificate (Let's Encrypt via Plesk)
2. Uncomment HTTPS server block in `nginx/nginx.conf`
3. Update `ALLOWED_HOSTS` in `.env`
4. Enable SSL settings in `settings_production.py`

### Security
- Change default admin credentials
- Use strong `SECRET_KEY`
- Enable CSRF protection
- Configure firewall rules
- Regular security updates

### Performance
- Monitor resource usage
- Scale containers as needed:
  ```bash
  docker-compose up -d --scale web=3
  ```
- Configure database connection pooling
- Set up CDN for static files

### Backup
Regular database backups:
```bash
# Create backup
docker-compose exec db pg_dump -U propbench_user propbench_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T db psql -U propbench_user propbench_db < backup.sql
```

## Monitoring Commands

```bash
# View all container status
docker-compose ps

# View logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx

# Execute commands in containers
docker-compose exec web python manage.py shell
docker-compose exec db psql -U propbench_user propbench_db

# Update application (pull new code)
docker-compose down
docker-compose build --no-cache web
docker-compose up -d
```

## Troubleshooting

### Container Won't Start
1. Check logs: `docker-compose logs [service]`
2. Verify .env configuration
3. Ensure ports aren't conflicted
4. Check disk space

### Database Connection Issues
1. Verify DATABASE_URL format
2. Check database container is running: `docker-compose ps db`
3. Test connection: `docker-compose exec db psql -U propbench_user propbench_db`

### Permission Issues
1. Check file ownership: `chown -R www-data:www-data /var/www/vhosts/yourdomain.com/`
2. Verify Docker daemon is running
3. Check Plesk Docker integration

### Static Files Not Loading
1. Run collectstatic: `docker-compose exec web python manage.py collectstatic --noinput`
2. Check nginx volume mounts
3. Verify file permissions

## Support

For issues:
1. Check application logs: `docker-compose logs -f web`
2. Review Plesk error logs
3. Consult Django documentation
4. Create GitHub issue with logs and configuration