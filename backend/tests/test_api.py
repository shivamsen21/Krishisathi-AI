import io
import uuid
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from main import app

client = TestClient(app)

def create_test_image_bytes(format="JPEG") -> bytes:
    """Helper to generate in-memory dummy image for testing upload."""
    buf = io.BytesIO()
    img = Image.new("RGB", (256, 256), color=(34, 139, 34))
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AgroVision AI Backend"
    assert "supabase_connected" in data

def test_user_registration_and_login():
    # 1. Register new user
    uid = uuid.uuid4().hex[:8]
    test_email = f"ramesh_{uid}@agrotest.com"
    reg_payload = {
        "full_name": "Ramesh Patel",
        "email": test_email,
        "password": "SecurePassword123!"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["role"] == "user"
    assert reg_data["user"]["id"]

    token = reg_data["access_token"]

    # 2. Duplicate registration should fail
    dup_res = client.post("/api/auth/register", json=reg_payload)
    assert dup_res.status_code == 400

    # 3. Login with credentials
    login_res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == test_email
    assert login_data["user"]["role"] == "user"

    # 4. Access /api/auth/me with Bearer token
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == test_email

    # 5. Access /api/auth/profile with Bearer token
    profile_res = client.get(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_res.status_code == 200
    assert profile_res.json()["email"] == test_email
    assert profile_res.json()["role"] == "user"

    # 6. Access /api/auth/profile without token should return 401
    unauth_res = client.get("/api/auth/profile")
    assert unauth_res.status_code == 401

def test_forgot_password():
    res = client.post("/api/auth/forgot-password", json={"email": "ramesh.patel@agrotest.com"})
    assert res.status_code == 200
    assert "message" in res.json()

def test_disease_catalog():
    res = client.get("/api/diseases")
    assert res.status_code == 200
    diseases = res.json()
    assert isinstance(diseases, list)
    assert len(diseases) > 0

    first_id = diseases[0]["id"]
    detail_res = client.get(f"/api/diseases/{first_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == first_id

def test_prediction_image_validation_and_flow():
    # 1. Reject invalid file type
    text_file = io.BytesIO(b"not an image file")
    bad_res = client.post(
        "/api/predict",
        files={"image": ("test.txt", text_file, "text/plain")},
        data={"crop": "Tomato"}
    )
    assert bad_res.status_code == 400

    # 2. Valid image upload
    img_bytes = create_test_image_bytes(format="JPEG")
    valid_res = client.post(
        "/api/predict",
        files={"image": ("leaf.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        data={"crop": "Tomato"}
    )
    assert valid_res.status_code == 200
    pred_data = valid_res.json()
    assert pred_data["crop"] == "Tomato"
    assert "disease" in pred_data
    assert "image_url" in pred_data
    assert "model_notice" in pred_data
    # Model may be loaded or fallback - both are valid
    assert pred_data["is_temporary_model"] in [True, False]

def test_user_history():
    uid = uuid.uuid4().hex[:8]
    user_payload = {
        "full_name": "Kavita Rao",
        "email": f"kavita_{uid}@agrotest.com",
        "password": "Password12345!"
    }
    reg = client.post("/api/auth/register", json=user_payload).json()
    token = reg["access_token"]

    img_bytes = create_test_image_bytes(format="PNG")
    client.post(
        "/api/predict",
        files={"image": ("kavita_leaf.png", io.BytesIO(img_bytes), "image/png")},
        data={"crop": "Potato"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Fetch user history
    hist_res = client.get(
        "/api/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert hist_res.status_code == 200
    history_items = hist_res.json()
    assert len(history_items) >= 1
    assert history_items[0]["crop"] == "Potato"

def test_chatbot():
    chat_res = client.post("/api/chat", json={"message": "My tomato plants have dark spots on leaves"})
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "reply" in data
    assert len(data["reply"]) > 10

def test_admin_authorization():
    uid = uuid.uuid4().hex[:8]
    norm_res = client.post("/api/auth/register", json={
        "full_name": "Farmer Joe",
        "email": f"joe_{uid}@agrotest.com",
        "password": "JoePassword123!"
    }).json()
    user_token = norm_res["access_token"]

    forbidden_res = client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert forbidden_res.status_code == 403
    assert "Administrator privileges required" in forbidden_res.json()["detail"]

    # 2. Login as admin
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@agrovision.ai",
        "password": "adminSecretPassword!"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    assert admin_login.json()["user"]["role"] == "admin"

    # 3. Admin stats
    stats_res = client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "farmers" in stats
    assert "predictions" in stats

    # 4. Admin users
    users_res = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert users_res.status_code == 200

    # 5. Admin predictions
    preds_res = client.get(
        "/api/admin/predictions",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert preds_res.status_code == 200

    # 6. Admin Disease CRUD
    create_res = client.post(
        "/api/admin/diseases",
        json={
            "crop": "Cotton",
            "disease_name": "Boll Rot",
            "symptoms": "Bolls become soft, brown and rot prematurely.",
            "cause": "Fungal/Bacterial complex",
            "prevention": "Avoid excessive plant canopy density and late season nitrogen.",
            "treatment": "Apply copper oxychloride at early boll formation."
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]

    # Update disease
    update_res = client.put(
        f"/api/admin/diseases/{created_id}",
        json={"symptoms": "Updated symptoms: water-soaked sunken brown lesions."},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_res.status_code == 200
    assert "Updated symptoms" in update_res.json()["symptoms"]

    # Delete disease
    del_res = client.delete(
        f"/api/admin/diseases/{created_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_res.status_code == 200
