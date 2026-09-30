# 🏠 House Insurance Risk Prediction System

AI-powered property risk assessment application built with React, FastAPI, XGBoost, MongoDB and JWT authentication.

## 🚀 Live Demo

**Primary demo:** https://houseinsurancerisk.site

**Vercel deployment:** https://insurance-risk-ml-react.vercel.app

**Backend API:** https://insurance-risk-ml.onrender.com

**Swagger API docs:** https://insurance-risk-ml.onrender.com/docs

**GitHub:** https://github.com/Ramkmm/insurance-risk-ml-react

## ✨ What it does

The application accepts property information and returns:

- AI-generated property risk score
- Low / Medium / High risk category
- Illustrative annual premium
- Premium rate
- Property value summary
- Feature importance for model explainability

## 🧠 ML & Engineering

- **Model:** XGBoost risk prediction
- **API:** FastAPI + Uvicorn
- **Frontend:** React + Vite
- **Database:** MongoDB
- **Authentication:** JWT-protected API endpoints
- **Deployment:** Vercel + Render
- **API documentation:** FastAPI Swagger UI
- **Containerization:** Docker

## 🏗️ Architecture

```text
Browser
  │
  ▼
React + Vite
  │ HTTPS + JWT
  ▼
FastAPI on Render
  ├── /auth/register
  ├── /auth/login
  ├── /auth/me
  └── /predict
       │
       ├── XGBoost model
       ├── Feature importance
       └── Premium calculation
              │
              ▼
           MongoDB
```

## 🔐 Demo flow

1. Open the live demo.
2. Register a demo account.
3. Sign in.
4. Enter property details.
5. Click **Calculate risk**.
6. Review risk score, category, premium estimate and feature importance.

## ⚠️ Demo disclaimer

This project is a machine-learning demonstration. Premium values are illustrative estimates and are **not actuarial insurance quotes**.

## 🎯 Portfolio value

This project demonstrates an end-to-end ML application covering model inference, REST API development, authentication, database integration, explainability, React UI development, cloud deployment and production-style API integration.
