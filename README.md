# Zemenay Analytics API

A high-performance Django REST API for blog analytics with time-series aggregation, providing comprehensive insights into blog views, user engagement, and performance metrics.

## 🚀 Features

- **Blog Views Analytics**: Aggregate and analyze blog views by country, user, or custom filters
- **Top Analytics**: Identify top-performing users, countries, and blogs
- **Performance Analytics**: Time-series performance metrics with growth calculations
- **Compressive Time Series**: Multi-granularity time-series aggregation (hour, day, week, month, year)
- **Real-time Aggregation**: Automated background jobs using Celery and Celery Beat
- **RESTful API**: Clean, well-documented REST API with OpenAPI/Swagger documentation
- **Scalable Architecture**: Optimized queries using pre-aggregated time-series data
- **Docker Support**: Complete Docker and Docker Compose setup for development and production

## 🛠️ Tech Stack

- **Framework**: Django 5.2.8
- **API**: Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)
- **Task Queue**: Celery with Redis broker
- **Documentation**: drf-spectacular (OpenAPI 3.0)
- **Testing**: pytest, pytest-django
- **Containerization**: Docker, Docker Compose

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+ (for production)
- Redis 7+ (for Celery)
- Docker and Docker Compose (optional, for containerized deployment)

## 🔧 Installation

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:codewiztinsing/zemenayalytics.git
   cd zemenayalytics
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements/dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env  # Create .env file with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

7. **Populate test data** (optional)
   ```bash
   python manage.py populate_data
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Docker Setup

1. **Build and start services**
   ```bash
   docker compose up --build
   ```

2. **Run migrations**
   ```bash
   docker compose up migrate
   ```

3. **Populate test data**
   ```bash
   docker compose up populate
   ```

4. **Start development server**
   ```bash
   docker compose up dev
   ```

5. **Start Celery workers** (for time-series aggregation)
   ```bash
   docker compose up celery_worker celery_beat
   ```

## ⚙️ Configuration

### Environment Variables

Create a `env.example` file in the project root with the following variables:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=zemenayalytics
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# API Settings
API_PAGE_SIZE=100
API_MAX_PAGE_SIZE=1000

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Settings Files

- `config/settings/base.py`: Base settings
- `config/settings/local.py`: Local development settings
- `config/settings/production.py`: Production settings

## 🏃 Running the Project

### Development Mode

```bash
# Using Docker (recommended)
docker compose up dev

# Or locally
python manage.py runserver
```

The API will be available at `http://localhost:8000`

### Production Mode

```bash
# Using Docker
docker compose up web

# Or using Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Background Tasks

Start Celery worker and beat scheduler:

```bash
# Using Docker
docker compose up celery_worker celery_beat

# Or locally
celery -A config worker -l info
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## 📡 API Endpoints

### Base URL
- Development: `http://localhost:8000`
- API Base: `http://localhost:8000/api/analytics/`

### Available Endpoints

#### 1. Blog Views Analytics
```
POST /api/analytics/blog-views/
```
Get analytics for blog views grouped by country or user.

**Request Body:**
```json
{
  "group_by": "country",  // or "user"
  "filters": {},  // optional dynamic filters
  "start": "2025-01-01",  // optional
  "end": "2025-12-31"  // optional
}
```

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "x": "Country Name",
      "y": 5,  // number of blogs
      "z": 150  // total views
    }
  ]
}
```

#### 2. Top Analytics
```
POST /api/analytics/top/
```
Get top 10 users, countries, or blogs by total views.

**Request Body:**
```json
{
  "top": "user",  // or "country", "blog"
  "filters": {},  // optional
  "start": "2025-01-01",  // optional
  "end": "2025-12-31"  // optional
}
```

#### 3. Performance Analytics
```
GET /api/analytics/performance/?compare=month&user_id=1
```
Get time-series performance metrics with growth calculations.

**Query Parameters:**
- `compare`: Period size (`day`, `week`, `month`, `year`)
- `user_id`: Optional user ID filter
- `start`: Start date (YYYY-MM-DD)
- `end`: End date (YYYY-MM-DD)
- `filters`: JSON string of dynamic filters

**Response:**
```json
{
  "count": 12,
  "results": [
    {
      "x": "January 2025 (5)",
      "y": 1200,  // views in period
      "z": 15.5  // growth percentage vs previous period
    }
  ]
}
```

### API Documentation

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## 🗄️ Database Management

### Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Using Docker
docker compose exec dev python manage.py migrate
```

### Populating Data

```bash
# Populate with default data (100 records each)
python manage.py populate_data

# Custom counts
python manage.py populate_data --blogs 200 --blog-views 1000 --users 50

# Clear existing data first
python manage.py populate_data --clear
```

### Time Series Aggregation

```bash
# Backfill historical data
python manage.py backfill_time_series

# Backfill specific granularity
python manage.py backfill_time_series --granularity day

# Backfill date range
python manage.py backfill_time_series --start-date 2025-01-01 --end-date 2025-12-31

# Clear and rebuild
python manage.py backfill_time_series --clear

# Using Docker
docker compose exec dev python manage.py backfill_time_series --clear
```

### Setting up Celery Beat

```bash
# Configure periodic tasks
python manage.py setup_celery_beat
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps

# Run specific test file
pytest apps/analytics/tests/test_views.py

# Using Docker
docker compose up test
```

### Test Structure

```
apps/analytics/tests/
├── test_models.py      # Model tests
├── test_services.py    # Service layer tests
└── test_views.py       # API endpoint tests
```

## 📁 Project Structure

```
zemenayalytics/
├── apps/
│   └── analytics/
│       ├── api/              # API configuration
│       ├── factories/        # Factory Boy factories
│       ├── management/      # Management commands
│       ├── migrations/       # Database migrations
│       ├── models/          # Django models
│       ├── serializers/     # DRF serializers
│       ├── services/        # Business logic
│       ├── tasks/           # Celery tasks
│       ├── tests/           # Test suite
│       └── views/          # API views
├── config/                  # Django project settings
│   ├── settings/           # Environment-specific settings
│   ├── celery.py           # Celery configuration
│   └── urls.py             # URL routing
├── docs/                   # Documentation
├── requirements/           # Python dependencies
├── scripts/                 # Utility scripts
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Production Dockerfile
├── Dockerfile.dev          # Development Dockerfile
└── manage.py               # Django management script
```

## 🔄 Time Series Aggregation

The project implements a compressive time-series aggregation system for efficient querying of historical data.

### Granularities

- **Hour**: Raw data aggregated by hour
- **Day**: Daily aggregates
- **Week**: Weekly aggregates
- **Month**: Monthly aggregates
- **Year**: Yearly aggregates

### Aggregation Strategy

- Data is pre-aggregated at multiple granularities
- Queries use the most appropriate granularity for performance
- Automatic aggregation via Celery Beat scheduled tasks
- Manual backfilling available for historical data

See [docs/compressive_time_series.md](docs/compressive_time_series.md) for detailed documentation.

## 🐳 Docker Services

The project includes several Docker services:

- **db**: PostgreSQL database
- **redis**: Redis server for Celery
- **dev**: Development server with auto-reload
- **web**: Production web server (Gunicorn)
- **migrate**: Run database migrations
- **populate**: Populate test data
- **test**: Run test suite
- **celery_worker**: Celery worker for background tasks
- **celery_beat**: Celery Beat scheduler
- **backfill_time_series**: Backfill time-series aggregates

## 📝 Management Commands

### Available Commands

- `populate_data`: Populate database with test data
- `backfill_time_series`: Backfill time-series aggregates
- `setup_celery_beat`: Configure Celery Beat periodic tasks

## 🔒 Security

- Environment-based secret key management
- CSRF protection enabled
- Secure cookie settings for production
- Input validation via serializers
- SQL injection protection (Django ORM)

## 📊 Logging

The project uses centralized logging with colored output:

- **Errors**: Red
- **Warnings**: Yellow
- **Info**: Default color
- **Debug**: Default color

Logs are written to:
- Console (colored output)
- File: `config/logs/django.log`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

## 📚 Additional Documentation

- [Time Series Population Guide](docs/TIME_SERIES_POPULATION.md)
- [Compressive Time Series Documentation](docs/compressive_time_series.md)

---

**Built with ❤️ using Django and Django REST Framework**

