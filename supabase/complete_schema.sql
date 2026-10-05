-- ========================================================================
-- AgroVision AI — Supabase Database Schema (Complete Setup)
-- Run this ENTIRE script in Supabase SQL Editor (https://supabase.com/dashboard/project/_/sql)
-- ========================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ========================================================================
-- 1. PROFILES TABLE
-- Stores user profile data linked directly to Supabase Auth (auth.users)
-- ========================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for email and role lookups
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);

-- ========================================================================
-- 2. DISEASES TABLE
-- Crop disease catalog containing symptoms, causes, prevention, and treatment
-- ========================================================================
CREATE TABLE IF NOT EXISTS public.diseases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop TEXT NOT NULL,
    disease_name TEXT NOT NULL,
    symptoms TEXT NOT NULL,
    cause TEXT NOT NULL DEFAULT '',
    prevention TEXT NOT NULL,
    treatment TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_crop_disease UNIQUE (crop, disease_name)
);

-- Index for fast searches by crop and disease name
CREATE INDEX IF NOT EXISTS idx_diseases_crop ON public.diseases(crop);
CREATE INDEX IF NOT EXISTS idx_diseases_name ON public.diseases(disease_name);

-- ========================================================================
-- 3. PREDICTIONS TABLE
-- History of leaf image disease classifications performed by farmers
-- ========================================================================
CREATE TABLE IF NOT EXISTS public.predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    crop TEXT NOT NULL,
    disease TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    image_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for efficient farmer history queries & admin analytics
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON public.predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON public.predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_crop ON public.predictions(crop);

-- ========================================================================
-- 4. CHAT_MESSAGES TABLE
-- Conversational history between farmers and Krishi AI assistant
-- ========================================================================
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'bot')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for fetching conversation ordered by timestamp
CREATE INDEX IF NOT EXISTS idx_chat_user_id_created ON public.chat_messages(user_id, created_at ASC);

-- ========================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ========================================================================

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.diseases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Helper function to check if the requesting user is an admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid() AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- --- Profiles RLS ---
-- Users can view their own profile; Admins can view all profiles
CREATE POLICY "Users can view own profile or admins view all"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id OR public.is_admin());

-- Users can update their own profile; Admins can update any
CREATE POLICY "Users can update own profile or admins update all"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id OR public.is_admin());

-- System or service role can insert profiles upon signup
CREATE POLICY "Enable insert for authenticated users or triggers"
    ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id OR public.is_admin());

-- --- Predictions RLS ---
-- Users can view their own predictions; Admins can view all predictions
CREATE POLICY "Users can view own predictions or admins view all"
    ON public.predictions
    FOR SELECT
    USING (auth.uid() = user_id OR public.is_admin());

-- Users can insert their own predictions
CREATE POLICY "Users can insert own predictions"
    ON public.predictions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- --- Diseases RLS ---
-- Everyone (authenticated and anonymous) can view the disease catalog
CREATE POLICY "Anyone can view diseases"
    ON public.diseases
    FOR SELECT
    USING (true);

-- Only admins can insert diseases
CREATE POLICY "Only admins can insert diseases"
    ON public.diseases
    FOR INSERT
    WITH CHECK (public.is_admin());

-- Only admins can update diseases
CREATE POLICY "Only admins can update diseases"
    ON public.diseases
    FOR UPDATE
    USING (public.is_admin());

-- Only admins can delete diseases
CREATE POLICY "Only admins can delete diseases"
    ON public.diseases
    FOR DELETE
    USING (public.is_admin());

-- --- Chat Messages RLS ---
-- Users can view their own chat messages; Admins can view all
CREATE POLICY "Users can view own chat messages or admins view all"
    ON public.chat_messages
    FOR SELECT
    USING (auth.uid() = user_id OR public.is_admin());

-- Users can insert their own chat messages
CREATE POLICY "Users can insert own chat messages"
    ON public.chat_messages
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ========================================================================
-- AUTOMATIC PROFILE CREATION TRIGGER
-- When a user registers in auth.users, create their row in public.profiles
-- ========================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, role)
    VALUES (
        new.id,
        COALESCE(new.raw_user_meta_data->>'full_name', ''),
        new.email,
        COALESCE(new.raw_user_meta_data->>'role', 'user')
    )
    ON CONFLICT (id) DO UPDATE SET
        full_name = EXCLUDED.full_name,
        email = EXCLUDED.email;
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger execution on auth.users INSERT
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Trigger for auto-updating updated_at on diseases
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_diseases_updated_at ON public.diseases;
CREATE TRIGGER trg_diseases_updated_at
    BEFORE UPDATE ON public.diseases
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ========================================================================
-- SEED INITIAL DISEASE CATALOG
-- ========================================================================
INSERT INTO public.diseases (crop, disease_name, symptoms, cause, prevention, treatment)
VALUES
(
    'Tomato',
    'Early Blight',
    'Dark brown spots surrounded by yellow concentric rings on older leaves. Spots may merge causing leaf drop and stem lesions.',
    'Fungus (Alternaria solani)',
    'Rotate crops every season. Avoid overhead irrigation. Plant certified disease-resistant varieties. Remove and destroy infected plant debris.',
    'Apply copper-based fungicide or mancozeb every 7–10 days at first sign. Ensure proper plant spacing for optimal air circulation.'
),
(
    'Tomato',
    'Late Blight',
    'Irregular water-soaked greasy grayish lesions on leaves that turn dark brown rapidly during cool, humid conditions with white fungal growth on undersides.',
    'Oomycete (Phytophthora infestans)',
    'Ensure proper field drainage, avoid late afternoon irrigation, destroy volunteer tomato and potato plants.',
    'Apply metalaxyl or chlorothalonil immediately. Severely infected plants must be uprooted and safely disposed of.'
),
(
    'Tomato',
    'Leaf Mold',
    'Pale yellow-green spots on upper leaf surfaces that develop olive-green to brown velvety fungal patches on lower surfaces.',
    'Fungus (Passalora fulva / Cladosporium fulvum)',
    'Ensure high greenhouse ventilation, keep relative humidity below 85%, space plants evenly.',
    'Prune lower infected foliage to enhance airflow. Spray appropriate bio-fungicide or copper hydroxide.'
),
(
    'Tomato',
    'Healthy Leaf',
    'Vibrant uniform green coloration, strong leaf structure, no discolored spots, curling or lesions detected.',
    'None (Optimal plant health)',
    'Maintain regular balanced NPK fertilization, consistent moisture schedule, and routine pest scouting.',
    'No chemical treatment required. Continue standard cultural maintenance.'
),
(
    'Potato',
    'Early Blight',
    'Brown-to-black angular spots with distinctive concentric target-ring patterns on mature leaves.',
    'Fungus (Alternaria solani)',
    'Plant certified seed tubers, adhere to strict 3-year crop rotations, maintain vigorous plant nutrition.',
    'Spray chlorothalonil, azoxystrobin, or copper oxychloride as preventive measures during vegetative growth.'
),
(
    'Potato',
    'Late Blight',
    'Rapidly expanding water-soaked lesions on leaf margins and tips, turning black with white sporulation on leaf undersides.',
    'Oomycete (Phytophthora infestans)',
    'Plant resistant potato cultivars, eliminate cull piles, avoid planting downwind of infected fields.',
    'Apply targeted systemic fungicides such as cymoxanil, dimethomorph, or metalaxyl-M.'
),
(
    'Potato',
    'Healthy Leaf',
    'Crisp, vigorous deep green foliage without chlorosis, spots, or wilt symptoms.',
    'None (Optimal plant health)',
    'Practice balanced nitrogen feeding, avoid drought stress, and monitor field edges regularly.',
    'No treatment required. Maintain current agronomic practices.'
),
(
    'Wheat',
    'Stripe Rust',
    'Bright yellow-orange linear pustules arranged in parallel stripes along leaf veins, releasing powdery spores.',
    'Fungus (Puccinia striiformis)',
    'Plant genetically resistant wheat varieties, avoid excessive nitrogen applications, eradicate wild grass hosts.',
    'Apply triazole fungicides (propiconazole, tebuconazole) promptly at the first sign of stripe pustules.'
),
(
    'Wheat',
    'Healthy Leaf',
    'Uniform green slender leaves with strong erect posture and no rust pustules or powdery mildew.',
    'None (Optimal plant health)',
    'Monitor soil moisture at crown root initiation and tillering stages; ensure balanced zinc and micronutrient availability.',
    'No treatment needed. Proceed with planned irrigation stages.'
),
(
    'Rice',
    'Bacterial Leaf Blight',
    'Water-soaked to yellowish-white wavy stripes extending from leaf tips along margins, causing severe drying and wilt.',
    'Bacterium (Xanthomonas oryzae pv. oryzae)',
    'Plant certified resistant seeds, drain fields periodically, avoid clipping seedling tips at transplanting, balance nitrogen with potassium.',
    'Drain standing water from the field. Apply copper hydroxide or validamycin as recommended by local agricultural extension.'
),
(
    'Corn',
    'Healthy Leaf',
    'Broad vibrant green leaves with sturdy midribs and no necrotic lesions, rust, or chlorotic streaks.',
    'None (Optimal plant health)',
    'Ensure balanced nitrogen and phosphorus feeding; maintain proper weed control during early canopy establishment.',
    'No treatment needed. Maintain standard irrigation schedule.'
)
ON CONFLICT (crop, disease_name) DO NOTHING;