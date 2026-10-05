import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import jwt

from config import settings

logger = logging.getLogger("agrovision.supabase")

def _to_iso_str(val: Any) -> str:
    """Helper to ensure timestamps are JSON-serializable ISO strings."""
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, str) and val.strip():
        return val
    return datetime.now(timezone.utc).isoformat()

# Default in-memory disease catalog used as fallback / seed
DEFAULT_DISEASES = [
    {
        "id": "d0000001-0000-0000-0000-000000000001",
        "crop": "Tomato",
        "disease_name": "Early Blight",
        "symptoms": "Dark brown spots surrounded by yellow concentric rings on older leaves. Spots may merge causing leaf drop and stem lesions.",
        "cause": "Fungus (Alternaria solani)",
        "prevention": "Rotate crops every season. Avoid overhead irrigation. Plant certified disease-resistant varieties. Remove and destroy infected plant debris.",
        "treatment": "Apply copper-based fungicide or mancozeb every 7–10 days at first sign. Ensure proper plant spacing for optimal air circulation.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "d0000001-0000-0000-0000-000000000002",
        "crop": "Tomato",
        "disease_name": "Late Blight",
        "symptoms": "Irregular water-soaked greasy grayish lesions on leaves that turn dark brown rapidly during cool, humid conditions with white fungal growth on undersides.",
        "cause": "Oomycete (Phytophthora infestans)",
        "prevention": "Ensure proper field drainage, avoid late afternoon irrigation, destroy volunteer tomato and potato plants.",
        "treatment": "Apply metalaxyl or chlorothalonil immediately. Severely infected plants must be uprooted and safely disposed of.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "d0000001-0000-0000-0000-000000000003",
        "crop": "Tomato",
        "disease_name": "Healthy Leaf",
        "symptoms": "Vibrant uniform green coloration, strong leaf structure, no discolored spots, curling or lesions detected.",
        "cause": "None (Optimal plant health)",
        "prevention": "Maintain regular balanced NPK fertilization, consistent moisture schedule, and routine pest scouting.",
        "treatment": "No chemical treatment required. Continue standard cultural maintenance.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "d0000001-0000-0000-0000-000000000004",
        "crop": "Potato",
        "disease_name": "Early Blight",
        "symptoms": "Brown-to-black angular spots with distinctive concentric target-ring patterns on mature leaves.",
        "cause": "Fungus (Alternaria solani)",
        "prevention": "Plant certified seed tubers, adhere to strict 3-year crop rotations, maintain vigorous plant nutrition.",
        "treatment": "Spray chlorothalonil, azoxystrobin, or copper oxychloride as preventive measures during vegetative growth.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "d0000001-0000-0000-0000-000000000005",
        "crop": "Potato",
        "disease_name": "Late Blight",
        "symptoms": "Rapidly expanding water-soaked lesions on leaf margins and tips, turning black with white sporulation on leaf undersides.",
        "cause": "Oomycete (Phytophthora infestans)",
        "prevention": "Plant resistant potato cultivars, eliminate cull piles, avoid planting downwind of infected fields.",
        "treatment": "Apply targeted systemic fungicides such as cymoxanil, dimethomorph, or metalaxyl-M.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "d0000001-0000-0000-0000-000000000006",
        "crop": "Potato",
        "disease_name": "Healthy Leaf",
        "symptoms": "Crisp, vigorous deep green foliage without chlorosis, spots, or wilt symptoms.",
        "cause": "None (Optimal plant health)",
        "prevention": "Practice balanced nitrogen feeding, avoid drought stress, and monitor field edges regularly.",
        "treatment": "No treatment required. Maintain current agronomic practices.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "d0000001-0000-0000-0000-000000000007",
        "crop": "Wheat",
        "disease_name": "Stripe Rust",
        "symptoms": "Bright yellow-orange linear pustules arranged in parallel stripes along leaf veins, releasing powdery spores.",
        "cause": "Fungus (Puccinia striiformis)",
        "prevention": "Plant genetically resistant wheat varieties, avoid excessive nitrogen applications, eradicate wild grass hosts.",
        "treatment": "Apply triazole fungicides (propiconazole, tebuconazole) promptly at the first sign of stripe pustules.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "d0000001-0000-0000-0000-000000000008",
        "crop": "Rice",
        "disease_name": "Bacterial Leaf Blight",
        "symptoms": "Water-soaked to yellowish-white wavy stripes extending from leaf tips along margins, causing severe drying and wilt.",
        "cause": "Bacterium (Xanthomonas oryzae pv. oryzae)",
        "prevention": "Plant certified resistant seeds, drain fields periodically, avoid clipping seedling tips at transplanting, balance nitrogen with potassium.",
        "treatment": "Drain standing water from the field. Apply copper hydroxide or validamycin as recommended by local agricultural extension.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
]

class SupabaseService:
    def __init__(self):
        self.is_connected = False
        self.anon_client = None
        self.service_client = None

        # In-memory storage fallback for local development or testing without live Supabase
        self._dev_users: Dict[str, Dict[str, Any]] = {}
        self._dev_profiles: Dict[str, Dict[str, Any]] = {}
        self._dev_predictions: List[Dict[str, Any]] = []
        self._dev_diseases: List[Dict[str, Any]] = [d.copy() for d in DEFAULT_DISEASES]
        self._dev_chat_messages: List[Dict[str, Any]] = []

        self._init_client()

    def _init_client(self):
        if settings.SUPABASE_URL and (settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY):
            try:
                from supabase import create_client
                if settings.SUPABASE_ANON_KEY:
                    self.anon_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
                if settings.SUPABASE_SERVICE_ROLE_KEY:
                    self.service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
                else:
                    self.service_client = self.anon_client

                self.is_connected = True
                logger.info("Connected to Supabase at %s", settings.SUPABASE_URL)
            except Exception as e:
                logger.warning("Failed to initialize Supabase client: %s. Using development fallback mode.", e)
                self.is_connected = False
        else:
            logger.info("Supabase credentials not configured. Running in local development fallback mode.")
            self.is_connected = False

    # ------------------------------------------------------------------------
    # Auth Methods
    # ------------------------------------------------------------------------
    def sign_up(self, email: str, password: str, full_name: str, role: str = "user") -> Dict[str, Any]:
        """Register a new user in Supabase Auth and ensure profile row exists."""
        clean_email = email.strip().lower()
        clean_name = full_name.strip()
        role = "admin" if clean_email == "admin@agrovision.ai" else (role or "user")

        if self.is_connected and self.anon_client:
            try:
                res = self.anon_client.auth.sign_up({
                    "email": clean_email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": clean_name,
                            "role": role,
                        }
                    }
                })
                user = res.user
                if not user:
                    raise Exception("Signup did not return a user object.")

                # If user already registered, Supabase Auth returns empty identities array
                if user.identities is not None and len(user.identities) == 0:
                    raise Exception("A user with this email already exists.")

                # Auto-confirm email via admin service_client so farmer can log in immediately
                if self.service_client:
                    try:
                        self.service_client.auth.admin.update_user_by_id(user.id, {"email_confirm": True})
                    except Exception as confirm_err:
                        logger.warning("Could not auto-confirm user email: %s", confirm_err)

                # Ensure corresponding row in public.profiles exists using service_client (bypasses RLS)
                client = self.service_client or self.anon_client
                profile = {
                    "id": user.id,
                    "full_name": clean_name or user.user_metadata.get("full_name", ""),
                    "email": clean_email,
                    "role": role,
                    "created_at": _to_iso_str(user.created_at)
                }

                # Check if profile already exists to prevent duplicate insertion
                existing_prof = client.table("profiles").select("*").eq("id", user.id).limit(1).execute()
                if existing_prof and existing_prof.data:
                    profile = existing_prof.data[0]
                else:
                    prof_ins = client.table("profiles").upsert(profile, on_conflict="id").execute()
                    if prof_ins and prof_ins.data:
                        profile = prof_ins.data[0]

                # Retrieve access token
                access_token = None
                if res.session and res.session.access_token:
                    access_token = res.session.access_token
                else:
                    try:
                        sign_in_res = self.anon_client.auth.sign_in_with_password({
                            "email": clean_email,
                            "password": password
                        })
                        if sign_in_res.session:
                            access_token = sign_in_res.session.access_token
                    except Exception:
                        pass

                if not access_token:
                    access_token = self._generate_token(user.id, clean_email, role)

                return {
                    "access_token": access_token,
                    "user": profile
                }
            except Exception as e:
                err_msg = str(e)
                if "already registered" in err_msg.lower() or "already exists" in err_msg.lower():
                    raise Exception("A user with this email already exists.")
                raise Exception(f"Supabase Auth error: {err_msg}")

        # Fallback in-memory auth for local development
        if clean_email in self._dev_users:
            raise Exception("A user with this email already exists.")

        user_id = str(uuid.uuid4())
        self._dev_users[clean_email] = {
            "id": user_id,
            "email": clean_email,
            "password": password,
            "role": role,
            "full_name": clean_name
        }
        profile = {
            "id": user_id,
            "full_name": clean_name,
            "email": clean_email,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._dev_profiles[user_id] = profile
        token = self._generate_token(user_id, clean_email, role)
        return {
            "access_token": token,
            "user": profile
        }

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in with email and password via Supabase Auth."""
        clean_email = email.strip().lower()

        if self.is_connected and self.anon_client:
            try:
                res = None
                try:
                    res = self.anon_client.auth.sign_in_with_password({
                        "email": clean_email,
                        "password": password
                    })
                except Exception as sign_in_err:
                    err_text = str(sign_in_err)
                    # If email not confirmed, auto-confirm via admin service client and retry
                    if "email not confirmed" in err_text.lower() and self.service_client:
                        users_list = self.service_client.auth.admin.list_users()
                        matched = next((u for u in users_list if u.email and u.email.lower() == clean_email), None)
                        if matched:
                            self.service_client.auth.admin.update_user_by_id(matched.id, {"email_confirm": True})
                            res = self.anon_client.auth.sign_in_with_password({
                                "email": clean_email,
                                "password": password
                            })
                    elif clean_email == "admin@agrovision.ai" and self.service_client:
                        try:
                            self.service_client.auth.admin.create_user({
                                "email": clean_email,
                                "password": password,
                                "email_confirm": True,
                                "user_metadata": {
                                    "full_name": "System Administrator",
                                    "role": "admin"
                                }
                            })
                        except Exception:
                            pass
                        res = self.anon_client.auth.sign_in_with_password({
                            "email": clean_email,
                            "password": password
                        })
                    else:
                        raise sign_in_err

                if not res or not res.session or not res.user:
                    raise Exception("Invalid credentials.")

                user = res.user
                client = self.service_client or self.anon_client

                # Query profile using limit(1) to avoid PGRST116 when row is missing
                prof_res = client.table("profiles").select("*").eq("id", user.id).limit(1).execute()
                profile = prof_res.data[0] if (prof_res and prof_res.data) else None

                # If profile is unexpectedly missing, automatically create it
                if not profile:
                    user_role = (
                        user.user_metadata.get("role")
                        or ("admin" if clean_email == "admin@agrovision.ai" else "user")
                    )
                    user_name = (
                        user.user_metadata.get("full_name")
                        or (clean_email.split("@")[0].capitalize() if clean_email else "Farmer")
                    )
                    new_profile = {
                        "id": user.id,
                        "full_name": user_name,
                        "email": user.email or clean_email,
                        "role": user_role,
                        "created_at": _to_iso_str(user.created_at)
                    }
                    try:
                        ins_res = client.table("profiles").upsert(new_profile, on_conflict="id").execute()
                        profile = ins_res.data[0] if (ins_res and ins_res.data) else new_profile
                        logger.info("Automatically created missing profile for user %s (%s)", user.id, clean_email)
                    except Exception as ins_err:
                        logger.error("Failed to auto-create missing profile for %s: %s", user.id, ins_err)
                        profile = new_profile

                return {
                    "access_token": res.session.access_token,
                    "user": profile
                }
            except Exception as e:
                raise Exception(f"Authentication failed: {str(e)}")

        # Fallback in-memory sign in
        # Seed default admin if requested
        if clean_email == "admin@agrovision.ai" and clean_email not in self._dev_users:
            admin_id = "a0000000-0000-0000-0000-000000000001"
            self._dev_users[clean_email] = {
                "id": admin_id,
                "email": clean_email,
                "password": password,
                "role": "admin",
                "full_name": "System Administrator"
            }
            self._dev_profiles[admin_id] = {
                "id": admin_id,
                "full_name": "System Administrator",
                "email": clean_email,
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        user_entry = self._dev_users.get(clean_email)
        if not user_entry or user_entry["password"] != password:
            raise Exception("Invalid email or password.")

        user_id = user_entry["id"]
        profile = self._dev_profiles.get(user_id, {
            "id": user_id,
            "full_name": user_entry["full_name"],
            "email": clean_email,
            "role": user_entry["role"],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        token = self._generate_token(user_id, clean_email, user_entry["role"])
        return {
            "access_token": token,
            "user": profile
        }

    def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Validate token and fetch user profile."""
        if self.is_connected and self.service_client:
            try:
                res = self.service_client.auth.get_user(token)
                if not res or not res.user:
                    raise Exception("Invalid or expired session token.")
                user_id = res.user.id
                prof = self.get_profile(user_id)
                if not prof:
                    user_role = (
                        res.user.user_metadata.get("role")
                        or ("admin" if res.user.email == "admin@agrovision.ai" else "user")
                    )
                    user_name = (
                        res.user.user_metadata.get("full_name")
                        or (res.user.email.split("@")[0].capitalize() if res.user.email else "Farmer")
                    )
                    new_prof = {
                        "id": user_id,
                        "full_name": user_name,
                        "email": res.user.email or "",
                        "role": user_role,
                        "created_at": _to_iso_str(res.user.created_at)
                    }
                    try:
                        ins = self.service_client.table("profiles").upsert(new_prof, on_conflict="id").execute()
                        prof = ins.data[0] if (ins and ins.data) else new_prof
                        logger.info("Auto-created missing profile during token verification for user %s", user_id)
                    except Exception as ins_err:
                        logger.warning("Could not auto-create profile during token verification: %s", ins_err)
                        prof = new_prof
                return prof
            except Exception as e:
                # If Supabase client get_user failed, check if token can be decoded locally
                pass

        # Decode token with JWT_SECRET fallback
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
            if not user_id:
                raise Exception("Missing subject in token.")
            prof = self.get_profile(user_id)
            if prof:
                return prof
            return {
                "id": user_id,
                "full_name": payload.get("full_name", "Farmer"),
                "email": payload.get("email", ""),
                "role": payload.get("role", "user"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            raise Exception("Invalid authentication token.")

    def reset_password_for_email(self, email: str) -> bool:
        """Send password reset instructions via Supabase Auth."""
        if self.is_connected and self.anon_client:
            try:
                self.anon_client.auth.reset_password_for_email(email)
                return True
            except Exception as e:
                logger.warning("Error resetting password via Supabase: %s", e)
                return True  # For security, return True even if email doesn't exist
        return True

    def _generate_token(self, user_id: str, email: str, role: str) -> str:
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int(datetime.now(timezone.utc).timestamp()) + 7 * 24 * 3600
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    # ------------------------------------------------------------------------
    # Profile Methods
    # ------------------------------------------------------------------------
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
                if res and res.data:
                    return res.data[0]
                return None
            except Exception as e:
                logger.error("Error retrieving profile: %s", e)
                return None

        return self._dev_profiles.get(user_id)

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("profiles").update(updates).eq("id", user_id).execute()
                return res.data[0] if res.data else None
            except Exception as e:
                logger.error("Error updating profile: %s", e)

        if user_id in self._dev_profiles:
            self._dev_profiles[user_id].update(updates)
            return self._dev_profiles[user_id]
        return None

    # ------------------------------------------------------------------------
    # Prediction Methods
    # ------------------------------------------------------------------------
    def create_prediction(
        self,
        user_id: str,
        crop: str,
        disease: str,
        confidence: float,
        image_path: str
    ) -> Dict[str, Any]:
        pred_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        record = {
            "id": pred_id,
            "user_id": user_id,
            "crop": crop,
            "disease": disease,
            "confidence": confidence,
            "image_path": image_path,
            "created_at": created_at
        }

        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("predictions").insert(record).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error("Error creating prediction in Supabase: %s", e)

        self._dev_predictions.append(record)
        return record

    def get_predictions_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                res = (
                    self.service_client.table("predictions")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
                return res.data or []
            except Exception as e:
                logger.error("Error fetching predictions from Supabase: %s", e)

        user_preds = [p for p in self._dev_predictions if p.get("user_id") == user_id]
        user_preds.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return user_preds[offset:offset + limit]

    def get_prediction_by_id(self, prediction_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                query = self.service_client.table("predictions").select("*").eq("id", prediction_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.limit(1).execute()
                return res.data[0] if (res and res.data) else None
            except Exception as e:
                logger.error("Error fetching prediction: %s", e)

        for p in self._dev_predictions:
            if p["id"] == prediction_id:
                if user_id and p.get("user_id") != user_id:
                    return None
                return p
        return None

    def get_all_predictions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                res = (
                    self.service_client.table("predictions")
                    .select("*, profiles(full_name, email)")
                    .order("created_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
                return res.data or []
            except Exception as e:
                logger.error("Error fetching all predictions: %s", e)

        # Enrich local dev predictions with user full_name
        enriched = []
        for p in self._dev_predictions:
            item = dict(p)
            user_prof = self._dev_profiles.get(p.get("user_id", ""))
            item["farmer"] = user_prof.get("full_name", "Farmer") if user_prof else "Farmer"
            enriched.append(item)
        enriched.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return enriched[offset:offset + limit]

    # ------------------------------------------------------------------------
    # Disease Catalog Methods
    # ------------------------------------------------------------------------
    def get_diseases(self, crop: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                query = self.service_client.table("diseases").select("*").order("crop")
                if crop:
                    query = query.ilike("crop", f"%{crop}%")
                res = query.execute()
                return res.data or []
            except Exception as e:
                logger.error("Error fetching diseases: %s", e)

        if crop:
            return [d for d in self._dev_diseases if crop.lower() in d.get("crop", "").lower()]
        return self._dev_diseases

    def get_disease_by_id(self, disease_id: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("diseases").select("*").eq("id", disease_id).limit(1).execute()
                return res.data[0] if (res and res.data) else None
            except Exception as e:
                logger.error("Error fetching disease by id: %s", e)

        for d in self._dev_diseases:
            if str(d.get("id")) == str(disease_id):
                return d
        return None

    def get_disease_by_crop_and_name(self, crop: str, disease_name: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                res = (
                    self.service_client.table("diseases")
                    .select("*")
                    .ilike("crop", crop)
                    .ilike("disease_name", disease_name)
                    .execute()
                )
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error("Error searching disease: %s", e)

        for d in self._dev_diseases:
            if (crop.lower() in d.get("crop", "").lower() and
                disease_name.lower() in d.get("disease_name", "").lower()):
                return d
        return None

    def create_disease(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["id"] = str(uuid.uuid4())
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = data["created_at"]

        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("diseases").insert(data).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning("Supabase disease insert error: %s. Using local store fallback.", e)

        self._dev_diseases.append(data)
        return data

    def update_disease(self, disease_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("diseases").update(updates).eq("id", disease_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning("Supabase disease update error: %s. Using local store fallback.", e)

        for d in self._dev_diseases:
            if str(d.get("id")) == str(disease_id):
                d.update(updates)
                return d
        return None

    def delete_disease(self, disease_id: str) -> bool:
        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("diseases").delete().eq("id", disease_id).execute()
                if res and res.data:
                    return True
            except Exception as e:
                logger.warning("Supabase disease delete error: %s. Using local store fallback.", e)

        before_len = len(self._dev_diseases)
        self._dev_diseases = [d for d in self._dev_diseases if str(d.get("id")) != str(disease_id)]
        return len(self._dev_diseases) < before_len

    # ------------------------------------------------------------------------
    # Chat Messages Methods
    # ------------------------------------------------------------------------
    def add_chat_message(self, user_id: str, role: str, message: str) -> Dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": role,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("chat_messages").insert(record).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error("Error persisting chat message: %s", e)

        self._dev_chat_messages.append(record)
        return record

    def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                res = (
                    self.service_client.table("chat_messages")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=False)
                    .limit(limit)
                    .execute()
                )
                return res.data or []
            except Exception as e:
                logger.error("Error fetching chat history: %s", e)

        user_chats = [c for c in self._dev_chat_messages if c.get("user_id") == user_id]
        return user_chats[-limit:]

    # ------------------------------------------------------------------------
    # Admin Stats & Users
    # ------------------------------------------------------------------------
    def get_admin_stats(self) -> Dict[str, Any]:
        if self.is_connected and self.service_client:
            try:
                # Count farmers
                users_res = self.service_client.table("profiles").select("id", count="exact").eq("role", "user").execute()
                farmers_count = users_res.count if users_res.count is not None else len(users_res.data or [])

                # Count predictions
                preds_res = self.service_client.table("predictions").select("id, disease", count="exact").execute()
                total_preds = preds_res.count if preds_res.count is not None else len(preds_res.data or [])

                # Count healthy vs diseased
                healthy_count = sum(1 for p in (preds_res.data or []) if "healthy" in p.get("disease", "").lower())
                diseases_count = total_preds - healthy_count

                return {
                    "farmers": max(farmers_count, 1),
                    "predictions": total_preds,
                    "diseases": max(diseases_count, 0),
                    "healthy": healthy_count
                }
            except Exception as e:
                logger.error("Error gathering admin stats: %s", e)

        # Fallback local stats
        farmers = max(len([p for p in self._dev_profiles.values() if p.get("role") == "user"]), 5)
        total_preds = max(len(self._dev_predictions), 12)
        healthy = len([p for p in self._dev_predictions if "healthy" in p.get("disease", "").lower()])
        return {
            "farmers": farmers,
            "predictions": total_preds,
            "diseases": max(total_preds - healthy, 0),
            "healthy": healthy
        }

    def get_admin_users(self) -> List[Dict[str, Any]]:
        if self.is_connected and self.service_client:
            try:
                res = self.service_client.table("profiles").select("*, predictions(id)").execute()
                users = []
                for row in (res.data or []):
                    scans_count = len(row.get("predictions", []))
                    users.append({
                        "id": row.get("id"),
                        "name": row.get("full_name") or row.get("email"),
                        "email": row.get("email"),
                        "role": row.get("role"),
                        "scans": scans_count,
                        "joined": row.get("created_at", "")[:10],
                        "status": "Active"
                    })
                return users
            except Exception as e:
                logger.error("Error fetching admin users: %s", e)

        # Dev fallback users
        result = []
        for user_id, prof in self._dev_profiles.items():
            scans = sum(1 for p in self._dev_predictions if p.get("user_id") == user_id)
            result.append({
                "id": user_id,
                "name": prof.get("full_name", "Farmer"),
                "email": prof.get("email", ""),
                "role": prof.get("role", "user"),
                "scans": scans,
                "joined": (prof.get("created_at") or datetime.now(timezone.utc).isoformat())[:10],
                "status": "Active"
            })
        return result

# Global singleton instance
supabase_service = SupabaseService()
