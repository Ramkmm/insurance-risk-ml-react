import os
import logging
from datetime import datetime, timedelta, timezone

import joblib
import numpy as np
import jwt

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

from pwdlib import PasswordHash
from jwt.exceptions import InvalidTokenError

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    status,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# FASTAPI CONFIG
# ============================================================

app = FastAPI(
    title="House Insurance Risk API 🚀",
    version="2.0.0",
    description="House insurance risk prediction API with JWT authentication",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://insurance-risk-ml-react.vercel.app",
        "https://insurance-risk-ml-react-git-main-pushpa-enterprises.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SECURITY CONFIG
# ============================================================

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()

security = HTTPBearer()


# ============================================================
# MONGODB CONFIG
# ============================================================

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "insurance_risk")

mongo_client = None
users_collection = None


def get_users_collection():
    """
    Create/reuse MongoDB connection.

    MongoClient is kept at module level so warm serverless
    invocations can reuse the connection.
    """

    global mongo_client
    global users_collection

    if not MONGODB_URI:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is not configured."
        )

    try:
        if mongo_client is None:
            mongo_client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,
            )

            # Verify connection
            mongo_client.admin.command("ping")

            logger.info("✅ MongoDB connected successfully")

        if users_collection is None:
            db = mongo_client[MONGODB_DB]
            users_collection = db["users"]

            # Prevent duplicate email accounts
            users_collection.create_index(
                "email",
                unique=True
            )

        return users_collection

    except PyMongoError as e:
        logger.exception(f"❌ MongoDB connection failed: {e}")

        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable."
        )


# ============================================================
# INPUT MODELS
# ============================================================

class InsuranceInput(BaseModel):
    house_age: int = Field(
        ...,
        ge=0,
        le=100,
        description="House age in years"
    )

    location_risk: float = Field(
        ...,
        ge=0,
        le=1,
        description="Location risk score (0-1)"
    )

    roof_type: int = Field(
        ...,
        ge=1,
        le=5,
        description="Roof type (1-5)"
    )

    past_claims: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of past claims"
    )

    property_value: float = Field(
        ...,
        gt=0,
        description="Property value in rupees"
    )


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128
    )


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=1,
        max_length=128
    )


# ============================================================
# MODEL CONFIG
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "risk_model1.pkl"
)

METADATA_PATH = MODEL_PATH.replace(
    ".pkl",
    "_metadata.pkl"
)

model = None
metadata = None


# ============================================================
# LOAD ML MODEL
# ============================================================

def load_model():

    global model
    global metadata

    try:

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}"
            )

        model = joblib.load(MODEL_PATH)

        logger.info(
            "✅ ML model loaded successfully"
        )

        if os.path.exists(METADATA_PATH):

            metadata = joblib.load(
                METADATA_PATH
            )

            logger.info(
                "✅ Model metadata loaded"
            )

        else:

            metadata = None

            logger.warning(
                "⚠️ Metadata file not found"
            )

    except Exception as e:

        logger.exception(
            f"❌ Model loading failed: {e}"
        )

        model = None
        metadata = None


@app.on_event("startup")
def startup_event():

    logger.info(
        "🚀 Starting House Insurance Risk API..."
    )

    load_model()


# ============================================================
# JWT FUNCTIONS
# ============================================================

def create_access_token(email: str):

    if not JWT_SECRET:

        raise HTTPException(
            status_code=503,
            detail="JWT authentication is not configured."
        )

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
):

    if not JWT_SECRET:

        raise HTTPException(
            status_code=503,
            detail="JWT authentication is not configured."
        )

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        email = payload.get("sub")

        if not email:
            raise credentials_exception

    except InvalidTokenError:

        raise credentials_exception

    users = get_users_collection()

    user = users.find_one(
        {
            "email": email
        }
    )

    if not user:

        raise credentials_exception

    return user


# ============================================================
# AUTH - REGISTER
# ============================================================

@app.post("/auth/register")
def register(data: RegisterInput):

    email = str(data.email).lower().strip()

    users = get_users_collection()

    existing_user = users.find_one(
        {
            "email": email
        }
    )

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )

    hashed_password = password_hash.hash(
        data.password
    )

    user_document = {
        "email": email,
        "password_hash": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "active": True,
    }

    try:

        users.insert_one(
            user_document
        )

    except DuplicateKeyError:

        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )

    except PyMongoError:

        logger.exception(
            "User registration failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create account."
        )

    logger.info(
        f"✅ New user registered: {email}"
    )

    return {
        "message": "Registration successful",
        "email": email,
    }


# ============================================================
# AUTH - LOGIN
# ============================================================

@app.post("/auth/login")
def login(data: LoginInput):

    email = str(data.email).lower().strip()

    users = get_users_collection()

    user = users.find_one(
        {
            "email": email
        }
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    try:

        password_valid = password_hash.verify(
            data.password,
            user["password_hash"]
        )

    except Exception:

        password_valid = False

    if not password_valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if not user.get("active", True):

        raise HTTPException(
            status_code=403,
            detail="User account is inactive."
        )

    access_token = create_access_token(
        email
    )

    logger.info(
        f"✅ User login successful: {email}"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "email": email,
    }


# ============================================================
# AUTH - CURRENT USER
# ============================================================

@app.get("/auth/me")
def get_me(
    current_user=Depends(get_current_user)
):

    return {
        "email": current_user["email"],
        "active": current_user.get(
            "active",
            True
        ),
        "created_at": current_user.get(
            "created_at"
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    database_status = "not_configured"

    if MONGODB_URI:

        try:

            users = get_users_collection()

            users.database.client.admin.command(
                "ping"
            )

            database_status = "connected"

        except Exception:

            database_status = "unavailable"

    return {

        "status": (
            "healthy"
            if model is not None
            else "degraded"
        ),

        "model_loaded": model is not None,

        "model_path": MODEL_PATH,

        "model_exists": os.path.exists(
            MODEL_PATH
        ),

        "metadata_loaded": metadata is not None,

        "metadata_path": METADATA_PATH,

        "metadata_exists": os.path.exists(
            METADATA_PATH
        ),

        "database": database_status,

        "authentication": (
            "configured"
            if JWT_SECRET
            else "not_configured"
        ),
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "message": (
            "House Insurance Risk API running 🚀"
        ),

        "docs": "/docs",

        "health": "/health",

        "register": "POST /auth/register",

        "login": "POST /auth/login",

        "me": "GET /auth/me",

        "predict": "POST /predict 🔒",

        "version": "2.0.0",
    }


# ============================================================
# PROTECTED ML PREDICTION
# ============================================================

@app.post("/predict")
def predict(
    data: InsuranceInput,
    current_user=Depends(get_current_user)
):
    logger.info(
        f"📨 Prediction request from "
        f"{current_user['email']}: {data.model_dump()}"
    )

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not available. Check /health"
        )

    try:
        # --------------------------------------------------------
        # Build feature vector in the same order as model training
        # --------------------------------------------------------
        input_data = np.array(
            [[
                data.house_age,
                data.location_risk,
                data.roof_type,
                data.past_claims,
                data.property_value
            ]],
            dtype=np.float64
        )

        # --------------------------------------------------------
        # Continuous ML risk probability
        # --------------------------------------------------------
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(
                input_data
            )[0]

            # Binary XGBoost classifier:
            # probabilities[0] = Low Risk probability
            # probabilities[1] = High Risk probability
            risk_score = float(
                probabilities[1]
            )

        else:
            # Fallback for models without predict_proba
            prediction = model.predict(
                input_data
            )[0]

            risk_score = float(
                prediction
            )

        # Keep risk score between 0 and 1
        risk_score = max(
            0.0,
            min(
                1.0,
                risk_score
            )
        )

        # --------------------------------------------------------
        # Risk category
        # --------------------------------------------------------
        if risk_score < 0.3:
            risk_category = "Low Risk"

        elif risk_score < 0.7:
            risk_category = "Medium Risk"

        else:
            risk_category = "High Risk"

        # --------------------------------------------------------
        # Illustrative annual premium calculation
        #
        # Property value is entered in Indian rupees.
        #
        # 0% risk   -> 0.25%
        # 100% risk -> 0.75%
        #
        # This is a demo estimate and NOT an actuarial quote.
        # --------------------------------------------------------
        premium_rate = (
            0.0025
            + (risk_score * 0.0050)
        )

        recommended_premium = round(
            data.property_value * premium_rate,
            2
        )

        # --------------------------------------------------------
        # Feature importance
        # --------------------------------------------------------
        feature_importance = None

        try:
            if hasattr(
                model,
                "feature_importances_"
            ):
                importances = (
                    model.feature_importances_
                )

                if (
                    metadata
                    and "feature_names"
                    in metadata
                ):
                    feature_names = (
                        metadata["feature_names"]
                    )

                else:
                    feature_names = [
                        "house_age",
                        "location_risk",
                        "roof_type",
                        "past_claims",
                        "property_value",
                    ]

                if len(importances) == len(
                    feature_names
                ):
                    feature_importance = {
                        name: float(imp)
                        for name, imp in zip(
                            feature_names,
                            importances
                        )
                    }

        except Exception as fe:
            logger.warning(
                f"Feature importance failed: {fe}"
            )

            feature_importance = None

        # --------------------------------------------------------
        # API response
        # --------------------------------------------------------
        response = {
            "risk_score": round(
                risk_score,
                4
            ),

            "risk_percentage": round(
                risk_score * 100,
                2
            ),

            "risk_category": risk_category,

            "recommended_premium": (
                recommended_premium
            ),

            "premium_rate": (
                premium_rate
            ),

            "premium_frequency": (
                "annual"
            ),

            "property_value": round(
                float(
                    data.property_value
                ),
                2
            ),

            "input_summary": (
                data.model_dump()
            ),

            "feature_importance": (
                feature_importance
            ),

            "user": (
                current_user["email"]
            ),
        }

        logger.info(
            f"📤 Response: {response}"
        )

        return response

    except Exception as e:
        logger.exception(
            f"Prediction failed: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Prediction error"
        )