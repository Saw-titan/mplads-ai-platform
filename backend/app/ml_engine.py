import math
import hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date

def calculate_haversine_distance(lat1: Optional[float], lon1: Optional[float], lat2: Optional[float], lon2: Optional[float]) -> float:
    """
    Computes great-circle distance between two geographic coordinates in meters using the Haversine formula.
    Pure Python implementation without requiring PostGIS.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0
    
    # Earth radius in meters
    R = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = R * c
    return float(distance)


def compute_sha256_hash(data: bytes) -> str:
    """Calculates SHA-256 hash for photo evidence integrity & duplicate verification."""
    return hashlib.sha256(data).hexdigest()


class MPLADSAnomalyDetector:
    def __init__(self):
        # 1. Financial Anomaly Detectors
        self.iso_forest = IsolationForest(contamination=0.12, random_state=42)
        self.lof = LocalOutlierFactor(n_neighbors=15, contamination=0.12, novelty=True)
        
        # 2. Text Duplicate Detectors
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
        self.sbert_model = None
        self.use_sbert = False

        # Attempt to load Sentence-BERT model
        try:
            from sentence_transformers import SentenceTransformer
            self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_sbert = True
            print("[ML Engine] Sentence-BERT ('all-MiniLM-L6-v2') loaded successfully.")
        except Exception as e:
            print(f"[ML Engine] Sentence-BERT unavailable ({e}). Using TF-IDF vectorizer fallback.")
            self.use_sbert = False

        self.is_fitted = False
        self.historical_records: List[Dict[str, Any]] = []
        self.historical_texts: List[str] = []
        self.historical_embeddings = None

    def fit(self, historical_projects: List[Dict[str, Any]]):
        """Fits Isolation Forest, Local Outlier Factor, and text models on historical MPLADS project records."""
        if not historical_projects:
            return

        self.historical_records = historical_projects
        df = pd.DataFrame(historical_projects)
        
        # Calculate feature ratios for numerical anomaly detection
        df['cost_ratio'] = df['expenditure_amount'] / (df['sanctioned_amount'].replace(0, 1))
        
        start_dates = pd.to_datetime(df['start_date'])
        target_dates = pd.to_datetime(df['target_completion_date'])
        df['duration_days'] = (target_dates - start_dates).dt.days.fillna(180).clip(lower=1)
        df['sanctioned_val'] = df['sanctioned_amount'].fillna(1000000)

        features = df[['cost_ratio', 'duration_days', 'sanctioned_val']].fillna(0)
        
        # Fit Isolation Forest and Local Outlier Factor (LOF)
        try:
            self.iso_forest.fit(features)
            self.lof.fit(features)
        except Exception as err:
            print(f"[ML Engine] Warning fitting numerical models: {err}")

        # Fit Text Models
        self.historical_texts = [f"{p.get('title', '')} {p.get('description', '')}".strip() for p in historical_projects]
        if self.historical_texts:
            try:
                self.vectorizer.fit(self.historical_texts)
            except Exception as err:
                print(f"[ML Engine] TF-IDF fit notice: {err}")

            if self.use_sbert and self.sbert_model:
                try:
                    # Pre-calculate embeddings for fast cosine similarity lookup
                    self.historical_embeddings = self.sbert_model.encode(self.historical_texts, show_progress_bar=False)
                except Exception as err:
                    print(f"[ML Engine] S-BERT embedding notice: {err}. Falling back to TF-IDF.")
                    self.use_sbert = False

        self.is_fitted = True

    def calculate_cost_score(self, sanctioned_amount: float, expenditure_amount: float, start_date: str, target_completion_date: str, physical_progress: Optional[float] = None) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Calculates normalized Cost Score (0-100) using Cost Overrun Ratios, Isolation Forest, and Local Outlier Factor (LOF).
        """
        signals = []
        cost_ratio = expenditure_amount / sanctioned_amount if sanctioned_amount > 0 else 1.0
        
        # Base cost score from overrun ratio
        if cost_ratio > 1.6:
            raw_cost = 90.0 + min((cost_ratio - 1.6) * 20.0, 10.0)
            signals.append({
                "name": "Severe Cost Overrun",
                "severity": "CRITICAL",
                "score": raw_cost,
                "description": f"Expenditure exceeds sanctioned amount by {((cost_ratio-1)*100):.1f}%."
            })
        elif cost_ratio > 1.25:
            raw_cost = 65.0 + (cost_ratio - 1.25) * 60.0
            signals.append({
                "name": "Elevated Cost Overrun",
                "severity": "HIGH",
                "score": raw_cost,
                "description": f"Expenditure is {((cost_ratio-1)*100):.1f}% over the initial sanctioned budget."
            })
        elif cost_ratio < 0.20 and expenditure_amount > 0:
            raw_cost = 45.0
            signals.append({
                "name": "Stalled Fund Utilization",
                "severity": "MEDIUM",
                "score": 45.0,
                "description": f"Only {(cost_ratio*100):.1f}% of sanctioned budget mobilized."
            })
        else:
            # Normal range (0.75 - 1.10)
            raw_cost = max(5.0, abs(cost_ratio - 0.95) * 50.0)

        # Earned-value intensity: expenditure vs verified physical completion
        if physical_progress is not None and physical_progress > 0 and sanctioned_amount > 0:
            expected_exp = sanctioned_amount * (physical_progress / 100.0)
            if expected_exp > 0:
                intensity = expenditure_amount / expected_exp
                if intensity >= 2.0:
                    raw_cost = max(raw_cost, 88.0 + min((intensity - 2.0) * 6.0, 12.0))
                    signals.append({
                        "name": "Earned-Value Cost Intensity Outlier",
                        "severity": "CRITICAL",
                        "score": raw_cost,
                        "description": f"Expenditure is {intensity:.1f}x the amount implied by {physical_progress:.1f}% physical progress."
                    })
                elif intensity >= 1.5:
                    raw_cost = max(raw_cost, 70.0 + (intensity - 1.5) * 30.0)
                    signals.append({
                        "name": "Elevated Unit Cost vs Progress",
                        "severity": "HIGH",
                        "score": raw_cost,
                        "description": f"Unit cost intensity is {intensity:.1f}x expected earned-value at current physical progress."
                    })

        # ML Outlier Detectors: Isolation Forest + LOF
        if self.is_fitted:
            try:
                start_dt = pd.to_datetime(start_date)
                target_dt = pd.to_datetime(target_completion_date)
                duration_days = max((target_dt - start_dt).days, 1)
                sample_features = np.array([[cost_ratio, duration_days, sanctioned_amount]])

                iso_pred = self.iso_forest.predict(sample_features)[0] # -1 = outlier
                lof_pred = self.lof.predict(sample_features)[0]       # -1 = outlier

                if iso_pred == -1 and lof_pred == -1:
                    raw_cost = min(raw_cost + 25.0, 100.0)
                    signals.append({
                        "name": "Isolation Forest & LOF Outlier",
                        "severity": "HIGH",
                        "score": 25.0,
                        "description": "Multi-variate statistical anomaly verified by both Isolation Forest and Local Outlier Factor."
                    })
                elif iso_pred == -1 or lof_pred == -1:
                    raw_cost = min(raw_cost + 15.0, 100.0)
                    detector_name = "Isolation Forest" if iso_pred == -1 else "Local Outlier Factor"
                    signals.append({
                        "name": f"{detector_name} Outlier",
                        "severity": "MEDIUM",
                        "score": 15.0,
                        "description": f"{detector_name} identified statistical density deviation in expenditure vector."
                    })
            except Exception:
                pass

        cost_score = min(max(float(raw_cost), 0.0), 100.0)
        return cost_score, signals

    def calculate_timeline_score(self, start_date: str, target_completion_date: str, actual_completion_date: Optional[str] = None, delay_months: Optional[float] = None) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Calculates normalized Timeline Score (0-100) based on milestone delays and target completion variance.
        """
        signals = []
        start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime("2024-01-01")
        target_dt = pd.to_datetime(target_completion_date) if target_completion_date else start_dt + pd.Timedelta(days=180)
        planned_duration = max((target_dt - start_dt).days, 30)

        if delay_months is not None:
            delay_days = int(delay_months * 30.0)
        elif actual_completion_date:
            actual_dt = pd.to_datetime(actual_completion_date)
            delay_days = max(0, (actual_dt - target_dt).days)
        else:
            # For active projects, evaluate if past target date
            today = pd.to_datetime(date.today())
            delay_days = max(0, (today - target_dt).days) if today > target_dt else 0

        delay_ratio = delay_days / planned_duration

        if delay_ratio >= 1.0 or delay_days >= 180: # 6+ months delay
            score = 85.0 + min((delay_days - 180) * 0.08, 15.0)
            signals.append({
                "name": "Critical Timeline Delay",
                "severity": "CRITICAL" if score >= 85 else "HIGH",
                "score": score,
                "description": f"Project delayed by ~{delay_days} days ({round(delay_days/30, 1)} months) past target completion."
            })
        elif delay_ratio >= 0.40 or delay_days >= 90:
            score = 60.0 + (delay_ratio - 0.40) * 40.0
            signals.append({
                "name": "Moderate Timeline Delay",
                "severity": "MEDIUM",
                "score": score,
                "description": f"Work progress running {delay_days} days behind scheduled milestone completion."
            })
        elif delay_days > 15:
            score = 25.0 + (delay_days / 90.0) * 25.0
        else:
            score = 5.0 # On-schedule baseline

        timeline_score = min(max(float(score), 0.0), 100.0)
        return timeline_score, signals

    def calculate_payment_score(self, payment_progress: float, physical_progress: float) -> Tuple[float, float, List[Dict[str, Any]]]:
        """
        Calculates Payment Score (0-100) based on Payment Progress vs Physical Progress Mismatch.
        Rule: Mismatch = payment_progress - physical_progress
        """
        signals = []
        mismatch = float(payment_progress - physical_progress)

        if mismatch >= 50.0:
            # Severe mismatch (e.g. 90% payment vs 35% physical = 55% mismatch)
            score = 85.0 + min((mismatch - 50.0) * 0.3, 15.0)
            signals.append({
                "name": "Severe Payment-Physical Progress Mismatch",
                "severity": "CRITICAL",
                "score": score,
                "description": f"{payment_progress:.1f}% funds disbursed while physical execution is only at {physical_progress:.1f}% (Mismatch: {mismatch:.1f}%)."
            })
        elif mismatch >= 25.0:
            score = 65.0 + (mismatch - 25.0) * 0.75
            signals.append({
                "name": "Elevated Progress Mismatch",
                "severity": "HIGH",
                "score": score,
                "description": f"Payment disbursement ({payment_progress:.1f}%) exceeds verified physical progress ({physical_progress:.1f}%) by {mismatch:.1f}%."
            })
        elif mismatch >= 10.0:
            score = 35.0 + (mismatch - 10.0) * 1.5
            signals.append({
                "name": "Minor Tranche Advance",
                "severity": "LOW",
                "score": score,
                "description": f"Disbursement leads physical completion by {mismatch:.1f}% within allowable advance limits."
            })
        else:
            # Healthy alignment
            score = 5.0

        payment_score = min(max(float(score), 0.0), 100.0)
        return payment_score, mismatch, signals

    def calculate_geo_score(self, sanctioned_lat: Optional[float], sanctioned_lon: Optional[float], actual_lat: Optional[float], actual_lon: Optional[float]) -> Tuple[float, float, bool, List[Dict[str, Any]]]:
        """
        Calculates Geospatial Score (0-100) and Distance using Haversine calculation.
        Rule: Distance <= 500m -> Normal; Distance > 500m -> Geospatial Anomaly.
        """
        signals = []
        if sanctioned_lat is None or sanctioned_lon is None or actual_lat is None or actual_lon is None:
            return 5.0, 0.0, False, signals

        distance_meters = calculate_haversine_distance(sanctioned_lat, sanctioned_lon, actual_lat, actual_lon)
        is_anomaly = distance_meters > 500.0

        if distance_meters > 3000.0: # 3+ km (e.g. 4.2 km)
            score = 90.0 + min((distance_meters - 3000.0) / 1000.0 * 2.5, 10.0)
            signals.append({
                "name": "Critical Geospatial Anomaly",
                "severity": "CRITICAL",
                "score": score,
                "description": f"Site evidence location is {(distance_meters/1000.0):.2f} km away from sanctioned coordinates (>500m threshold)."
            })
        elif distance_meters > 500.0:
            score = 65.0 + ((distance_meters - 500.0) / 2500.0) * 25.0
            signals.append({
                "name": "Geospatial Boundary Violation",
                "severity": "HIGH",
                "score": score,
                "description": f"Work location deviates by {int(distance_meters)} meters from approved nodal GPS coordinates."
            })
        else:
            # Within 500m normal tolerance
            score = (distance_meters / 500.0) * 15.0

        geo_score = min(max(float(score), 0.0), 100.0)
        return geo_score, distance_meters, is_anomaly, signals

    def calculate_duplicate_score(self, title: str, description: Optional[str] = None, exclude_title: Optional[str] = None) -> Tuple[float, Optional[str], List[Dict[str, Any]]]:
        """
        Calculates Duplicate Score (0-100) using Sentence-BERT cosine similarity with TF-IDF fallback.
        """
        signals = []
        query_text = f"{title} {description or ''}".strip()
        max_sim = 0.0
        matched_title = None

        if self.is_fitted and self.historical_texts:
            # Filter historical list if excluding current project
            comp_texts = []
            comp_records = []
            for idx, t in enumerate(self.historical_texts):
                rec_title = ""
                if idx < len(self.historical_records):
                    rec_title = str(self.historical_records[idx].get("title") or "")
                if exclude_title and rec_title == exclude_title:
                    continue
                if t.strip() == query_text:
                    continue
                comp_texts.append(t)
                if idx < len(self.historical_records):
                    comp_records.append(self.historical_records[idx])
            if not comp_texts:
                comp_texts = self.historical_texts
                comp_records = self.historical_records

            if self.use_sbert and self.sbert_model:
                try:
                    q_emb = self.sbert_model.encode([query_text], show_progress_bar=False)
                    if self.historical_embeddings is not None and len(self.historical_embeddings) > 0:
                        if exclude_title:
                            h_embs = self.sbert_model.encode(comp_texts, show_progress_bar=False)
                            sims = cosine_similarity(q_emb, h_embs).flatten()
                            idx_max = int(np.argmax(sims))
                            max_sim = float(sims[idx_max])
                            if idx_max < len(comp_records):
                                matched_title = comp_records[idx_max].get('title', 'Historical Proposal')
                        else:
                            sims = cosine_similarity(q_emb, self.historical_embeddings).flatten()
                            idx_max = int(np.argmax(sims))
                            max_sim = float(sims[idx_max])
                            if idx_max < len(self.historical_records):
                                matched_title = self.historical_records[idx_max].get('title', 'Historical Proposal')
                except Exception as err:
                    print(f"[ML Engine] S-BERT inference notice: {err}. Using TF-IDF.")
                    self.use_sbert = False

            if not self.use_sbert:
                try:
                    q_vec = self.vectorizer.transform([query_text])
                    h_vecs = self.vectorizer.transform(comp_texts)
                    sims = cosine_similarity(q_vec, h_vecs).flatten()
                    if len(sims) > 0:
                        idx_max = int(np.argmax(sims))
                        max_sim = float(sims[idx_max])
                        if idx_max < len(comp_texts):
                            matched_title = comp_texts[idx_max][:80]
                except Exception:
                    pass

        dup_status = "NORMAL"
        # Duplicate scoring threshold
        if max_sim >= 0.85:
            dup_status = "DUPLICATE_PROPOSAL"
            score = 85.0 + (max_sim - 0.85) * 100.0
            signals.append({
                "name": "Duplicate Project Proposal (Sentence-BERT / Text)",
                "severity": "CRITICAL" if max_sim > 0.92 else "HIGH",
                "score": score,
                "description": f"Semantic proposal similarity ({int(max_sim*100)}%) with prior sanctioned project '{matched_title}'."
            })
        elif max_sim >= 0.70:
            dup_status = "HIGH_OVERLAP"
            score = 50.0 + (max_sim - 0.70) * 150.0
            signals.append({
                "name": "High Textual Overlap",
                "severity": "MEDIUM",
                "score": score,
                "description": f"Moderate semantic overlap ({int(max_sim*100)}%) with recorded works."
            })
        else:
            dup_status = "NORMAL"
            score = max_sim * 20.0

        duplicate_score = min(max(float(score), 0.0), 100.0)
        return duplicate_score, matched_title, float(max_sim), dup_status, signals

    def compute_sih_composite_risk(
        self,
        cost_score: float,
        timeline_score: float,
        payment_score: float,
        geo_score: float,
        duplicate_score: float,
        has_duplicate_evidence: bool = False
    ) -> Tuple[float, str]:
        """
        Executes the Smart India Hackathon (SIH) Transparent Composite Risk Formula:
        
        Risk Score = 0.30 * Cost + 0.25 * Timeline + 0.20 * Payment + 0.15 * Geo + 0.10 * Duplicate
        
        Clamped between 0.0 and 100.0.
        
        Severity Ranges:
        0 - 39:   LOW
        40 - 69:  MEDIUM
        70 - 84:  HIGH
        85 - 100: CRITICAL
        """
        # If duplicate evidence is detected, elevate duplicate component score
        effective_duplicate_score = max(duplicate_score, 95.0 if has_duplicate_evidence else duplicate_score)

        raw_score = (
            0.30 * cost_score +
            0.25 * timeline_score +
            0.20 * payment_score +
            0.15 * geo_score +
            0.10 * effective_duplicate_score
        )

        final_risk = min(max(round(raw_score, 1), 0.0), 100.0)

        # Exact severity mapping
        if final_risk >= 85.0:
            severity = "CRITICAL"
        elif final_risk >= 70.0:
            severity = "HIGH"
        elif final_risk >= 40.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return final_risk, severity

    def analyze_project(
        self,
        title: str,
        category: str,
        sanctioned_amount: float,
        expenditure_amount: float,
        start_date: str,
        target_completion_date: str,
        contractor_name: str,
        contractor_gstin: str,
        district_name: str,
        description: Optional[str] = None,
        physical_progress: Optional[float] = None,
        sanctioned_lat: Optional[float] = None,
        sanctioned_lon: Optional[float] = None,
        actual_lat: Optional[float] = None,
        actual_lon: Optional[float] = None,
        is_contractor_blacklisted: bool = False,
        has_duplicate_evidence: bool = False,
        actual_completion_date: Optional[str] = None,
        delay_months: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a project proposal or stored record through the complete SIH 5-Factor Risk Pipeline.
        """
        all_signals = []

        # 1. Cost Score (0.30 weight)
        cost_score, cost_signals = self.calculate_cost_score(
            sanctioned_amount=sanctioned_amount,
            expenditure_amount=expenditure_amount,
            start_date=start_date,
            target_completion_date=target_completion_date,
            physical_progress=physical_progress
        )
        all_signals.extend(cost_signals)

        # 2. Timeline Score (0.25 weight)
        timeline_score, timeline_signals = self.calculate_timeline_score(
            start_date=start_date,
            target_completion_date=target_completion_date,
            actual_completion_date=actual_completion_date,
            delay_months=delay_months
        )
        all_signals.extend(timeline_signals)

        # 3. Payment Score (0.20 weight)
        calc_payment_progress = (expenditure_amount / sanctioned_amount * 100.0) if sanctioned_amount > 0 else 0.0
        calc_physical_progress = physical_progress if physical_progress is not None else min(calc_payment_progress * 0.85, 100.0)
        payment_score, progress_mismatch, payment_signals = self.calculate_payment_score(
            payment_progress=calc_payment_progress,
            physical_progress=calc_physical_progress
        )
        all_signals.extend(payment_signals)

        # 4. Geospatial Score (0.15 weight)
        geo_score, geo_distance, is_geo_anomaly, geo_signals = self.calculate_geo_score(
            sanctioned_lat=sanctioned_lat,
            sanctioned_lon=sanctioned_lon,
            actual_lat=actual_lat,
            actual_lon=actual_lon
        )
        all_signals.extend(geo_signals)

        # 5. Duplicate Score (0.10 weight)
        duplicate_score, matched_proposal, max_sim, dup_status, duplicate_signals = self.calculate_duplicate_score(
            title=title,
            description=description,
            exclude_title=title
        )
        all_signals.extend(duplicate_signals)

        if has_duplicate_evidence:
            duplicate_score = max(duplicate_score, 95.0)
            all_signals.append({
                "name": "Duplicate Photo Evidence Detected",
                "severity": "CRITICAL",
                "score": 95.0,
                "description": "Identical SHA-256 photo evidence hash uploaded across multiple distinct project records."
            })

        # Contractor blacklist check
        if is_contractor_blacklisted:
            cost_score = min(cost_score + 30.0, 100.0)
            all_signals.append({
                "name": "Blacklisted Contractor Assigned",
                "severity": "HIGH",
                "score": 30.0,
                "description": f"Contractor '{contractor_name}' (GSTIN: {contractor_gstin}) is flagged on state debarment register."
            })

        # Calculate Final SIH Composite Risk
        final_risk_score, severity = self.compute_sih_composite_risk(
            cost_score=cost_score,
            timeline_score=timeline_score,
            payment_score=payment_score,
            geo_score=geo_score,
            duplicate_score=duplicate_score,
            has_duplicate_evidence=has_duplicate_evidence
        )

        is_flagged = severity in ["HIGH", "CRITICAL"]

        # Recommended Administrative Actions
        if severity == "CRITICAL":
            recommendation = "Physical Verification / Detailed Forensic Audit"
        elif severity == "HIGH":
            recommendation = "Field Inspection & Clarification Request"
        elif severity == "MEDIUM":
            recommendation = "Nodal Desk Verification Before Next Tranche"
        else:
            recommendation = "Approved for Standard Disbursement"

        # AI Summary
        if all_signals:
            top_reasons = [f"• {s['name']}: {s['description']}" for s in all_signals[:3]]
            summary = f"{severity} Anomaly Risk ({final_risk_score}/100).\n" + "\n".join(top_reasons)
        else:
            summary = f"Normal proposal profile ({final_risk_score}/100). All parameters conform to standard guidelines."

        return {
            "cost_score": cost_score,
            "timeline_score": timeline_score,
            "payment_score": payment_score,
            "geo_score": geo_score,
            "duplicate_score": duplicate_score,
            "final_risk_score": final_risk_score,
            "risk_score": final_risk_score,
            "severity": severity,
            "risk_level": severity,
            "is_flagged": is_flagged,
            "physical_progress": calc_physical_progress,
            "payment_progress": calc_payment_progress,
            "progress_mismatch": progress_mismatch,
            "geo_distance_meters": geo_distance,
            "geo_anomaly_flag": is_geo_anomaly,
            "recommendation": recommendation,
            "risk_factors": all_signals,
            "ai_summary": summary,
            "matched_project": matched_proposal,
            "similarity_score": round(max_sim * 100, 1),
            "duplicate_status": dup_status,
            "model_used": "Sentence-BERT (all-MiniLM-L6-v2)" if self.use_sbert else "TF-IDF Vectorizer (Fallback)"
        }

ml_engine = MPLADSAnomalyDetector()

