#!/bin/bash
set -e

echo "🚀 PropBench Deployment Script for Plesk"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before proceeding!"
    echo "   Required: SECRET_KEY, ALLOWED_HOSTS, database credentials"
    read -p "Press enter to continue after editing .env file..."
fi

echo "🔧 Building and starting containers..."
docker-compose down --volumes --remove-orphans
docker-compose build --no-cache
docker-compose up -d

echo "⏳ Waiting for database to be ready..."
sleep 15

echo "🗄️  Running database migrations..."
docker-compose exec web python manage.py migrate --settings=propbench.settings_production

echo "👤 Creating superuser (if needed)..."
docker-compose exec web python manage.py shell --settings=propbench.settings_production -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('ℹ️  Superuser already exists')
"

echo "📚 Creating test dictionaries..."
docker-compose exec web python manage.py create_test_dictionaries --settings=propbench.settings_production

echo "📊 Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput --settings=propbench.settings_production

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your PropBench application is now running:"
echo "   📍 Application: http://localhost"
echo "   🔧 Admin: http://localhost/admin"
echo "   👤 Login: admin / admin123"
echo ""
echo "📋 Useful commands:"
echo "   🔍 View logs: docker-compose logs -f"
echo "   🛑 Stop: docker-compose down"
echo "   🔄 Restart: docker-compose restart"
echo "   💾 Backup DB: docker-compose exec db pg_dump -U propbench_user propbench_db > backup.sql"
echo ""
echo "⚠️  Remember to:"
echo "   1. Change default admin password"
echo "   2. Configure SSL certificates for production"
echo "   3. Set up regular database backups"
echo "   4. Monitor logs and performance"