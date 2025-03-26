closet-to-climate/
├── backend/
│   ├── app/                  # Core application
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app entrypoint
│   │   ├── database.py       # DB connections
│   │   ├── models.py         # Pydantic/SQL models
│   │   ├── services/         # Business logic
│   │   │   ├── weather.py    # Weather API calls
│   │   │   ├── ai.py         # Image tagging/outfit generation
│   │   │   └── recommendations.py
│   │   ├── routers/          # API endpoints
│   │   │   ├── clothes.py    # /clothes endpoints
│   │   │   └── outfits.py    # /outfits endpoints
│   │   └── utils/            # Helpers
│   │       ├── image_utils.py
│   │       └── geolocation.py
│   ├── tests/                # Unit/integration tests
│   ├── requirements.txt      # Dependencies
│   └── .env                  # Environment variables
├── ml/                       # AI/ML models
│   ├── train_model.py        # Model training script
│   └── clothing_classifier/  # Saved model files
└── README.md